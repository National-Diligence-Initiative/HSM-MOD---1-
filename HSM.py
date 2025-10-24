#!/usr/bin/env python3
"""
NDI Heat-Seeking Missile — Defensive Alert Engine (Non-violent)
Purpose:
  - Ingest anonymized reports or automated signals
  - Score each report by the Fivefold Trajectory (Courage, Dexterity, ClauseMatter, Audacity)
  - Group & geofence signals, create incidents for human review
  - Log artifacts to append-only ledger with SHA-256 checksums
  - Send alerts to webhook / email for authorized human reviewers

Safety:
  - This system is purely defensive: it flags, archives, and notifies humans.
  - Do NOT use this to target or direct harm at people or locations.
  - Preserve chain-of-custody and follow local laws / organizational policy before escalating to authorities.

Dependencies: Python 3.8+, install:
  pip install flask requests python-dotenv
"""

import os
import json
import csv
import hashlib
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from math import isfinite

# Optional: for webhook delivery
try:
    import requests
except Exception:
    requests = None

# Optional: for running a lightweight API
try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except Exception:
    FLASK_AVAILABLE = False

# -----------------------
# Configuration (ENV)
# -----------------------
LEDGER_DIR = os.environ.get("HS_LEDGER_DIR", "./hs_ledger")
ALERT_WEBHOOK = os.environ.get("HS_ALERT_WEBHOOK")
ALERT_EMAIL_SMTP = os.environ.get("HS_ALERT_EMAIL_SMTP")
ALERT_EMAIL_FROM = os.environ.get("HS_ALERT_EMAIL_FROM", "alerts@example.local")
ALERT_EMAIL_TO = os.environ.get("HS_ALERT_EMAIL_TO", "reviewers@example.local")
SCORE_THRESHOLD = float(os.environ.get("HS_SCORE_THRESHOLD", "0.8"))
GEOFENCE_RADIUS_METERS = float(os.environ.get("HS_GEOFENCE_RADIUS_METERS", "500"))
LEDGER_LOCK_FILENAME = os.path.join(LEDGER_DIR, ".lock")

os.makedirs(LEDGER_DIR, exist_ok=True)

# -----------------------
# Utility helpers
# -----------------------
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def append_ledger(record: Dict[str, Any]) -> str:
    fname = os.path.join(LEDGER_DIR, f"ledger_{datetime.utcnow().strftime('%Y%m%d')}.ndjson")
    line = json.dumps(record, ensure_ascii=False)
    record_hash = sha256_bytes(line.encode("utf-8"))
    entry = {"ts": utc_now_iso(), "hash": record_hash, "record": record}
    with open(fname, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "
")
    return record_hash

# -----------------------
# Trajectory Mechanic (Fivefold)
# -----------------------
class TrajectoryMechanic:
    def __init__(self, honor: float = 1.0):
        self.honor = honor
    @staticmethod
    def _clamp(v: float) -> float:
        try:
            v = float(v)
        except Exception:
            return 0.0
        if not isfinite(v):
            return 0.0
        return max(0.0, min(1.0, v))
    def score(self, courage: float, dexterity: float, clause_matter: float, audacity: float) -> Dict[str, Any]:
        C = self._clamp(courage)
        D = self._clamp(dexterity)
        M = self._clamp(clause_matter)
        A = self._clamp(audacity)
        numerator = C + D + M + A
        denominator = 4.0 * max(self.honor, 1e-6)
        ratio = round(numerator / denominator, 4)
        phase = self._phase_name(ratio)
        return {"C": C, "D": D, "M": M, "A": A, "ratio": ratio, "phase": phase}
    @staticmethod
    def _phase_name(ratio: float) -> str:
        if ratio < 0.25:
            return "Initiation (Courage)"
        if ratio < 0.5:
            return "Adaptation (Dexterity)"
        if ratio < 0.75:
            return "Verification (Clause Matter)"
        if ratio < 1.0:
            return "Action (Audacity)"
        return "Equilibrium (Honor)"

# -----------------------
# Geofence / grouping helpers
# (simple haversine)
# -----------------------
from math import radians, sin, cos, asin, sqrt

def haversine_meters(lat1, lon1, lat2, lon2):
    R = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def in_same_geofence(a: Dict[str,Any], b: Dict[str,Any], radius_m: float) -> bool:
    if "lat" not in a or "lon" not in a or "lat" not in b or "lon" not in b:
        return False
    try:
        d = haversine_meters(float(a["lat"]), float(a["lon"]), float(b["lat"]), float(b["lon"]))
        return d <= radius_m
    except Exception:
        return False

# -----------------------
# Incident Manager
# -----------------------
class IncidentManager:
    def __init__(self, threshold: float = SCORE_THRESHOLD, webhook: Optional[str] = ALERT_WEBHOOK):
        self.tm = TrajectoryMechanic()
        self.threshold = threshold
        self.webhook = webhook
        self.incidents_file = os.path.join(LEDGER_DIR, "incidents.ndjson")
    def ingest_report(self, report: Dict[str,Any]) -> Dict[str,Any]:
        rid = report.get("id") or str(uuid.uuid4())
        record = {
            "id": rid,
            "received_at": utc_now_iso(),
            "text": report.get("text", "")[:5000],
            "meta": report.get("meta", {}),
            "lat": report.get("lat"),
            "lon": report.get("lon"),
            "source": report.get("source", "anonymous"),
        }
        score = self.tm.score(
            report.get("courage", 0.0),
            report.get("dexterity", 0.0),
            report.get("clause_matter", 0.0),
            report.get("audacity", 0.0)
        )
        record["score"] = score
        record_hash = append_ledger(record)
        record["ledger_hash"] = record_hash
        incident = None
        if score["ratio"] >= self.threshold:
            incident = self._create_incident(record)
            record["incident"] = incident
            self._send_alert(record, incident)
        with open(self.incidents_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": utc_now_iso(), "entry": record}, ensure_ascii=False) + "
")
        return record
    def _create_incident(self, record: Dict[str,Any]) -> Dict[str,Any]:
        incident_id = "INC-" + datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        incident = {
            "incident_id": incident_id,
            "created_at": utc_now_iso(),
            "priority": "HIGH" if record["score"]["ratio"] >= 0.95 else "MEDIUM",
            "evidence_hash": record["ledger_hash"],
            "record_ref": record["id"],
            "lat": record.get("lat"),
            "lon": record.get("lon"),
            "score": record["score"],
            "notes": "Auto-created by Heat-Seeking Defensive Engine"
        }
        incident_file = os.path.join(LEDGER_DIR, f"{incident_id}.json")
        with open(incident_file, "w", encoding="utf-8") as f:
            json.dump(incident, f, indent=2, ensure_ascii=False)
        return incident
    def _send_alert(self, record: Dict[str,Any], incident: Dict[str,Any]) -> None:
        payload = {
            "incident_id": incident["incident_id"],
            "created_at": incident["created_at"],
            "priority": incident["priority"],
            "score": incident["score"],
            "text": record["text"],
            "evidence_hash": incident["evidence_hash"],
            "context": record["meta"],
            "location": {"lat": record.get("lat"), "lon": record.get("lon")}
        }
        if self.webhook and requests:
            try:
                r = requests.post(self.webhook, json=payload, timeout=6)
                append_ledger({"alert_sent": True, "webhook": self.webhook, "status_code": r.status_code, "incident_id": incident["incident_id"]})
            except Exception as e:
                append_ledger({"alert_sent": False, "error": str(e), "incident_id": incident["incident_id"]})
        # Email notification code placeholder (implement per organizational policy)

# -----------------------
# Run server if executed
# -----------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="hs_defensive_engine")
    parser.add_argument("--cli", help="Process JSON file of report(s)", type=str)
    parser.add_argument("--serve", help="Run HTTP API (requires flask)", action="store_true")
    parser.add_argument("--port", help="Port for HTTP API", type=int, default=8000)
    args = parser.parse_args()
    if args.cli:
        example_cli_ingest(args.cli)
    elif args.serve:
        if not FLASK_AVAILABLE:
            print("Flask not installed. Install with: pip install flask")
            raise SystemExit(1)
        print(f"Starting Heat-Seeking Defensive Engine on 0.0.0.0:{args.port}")
        app.run(host="0.0.0.0", port=args.port)
    else:
        print("Run with --serve to start HTTP ingestion endpoint or --cli <file.json> to ingest")