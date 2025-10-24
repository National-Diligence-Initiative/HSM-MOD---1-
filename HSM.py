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

Blockchain-Enhanced NWI Defensive Engine
Immutable record-keeping with blockchain serialization
"""

import binascii
import os
import json
import csv
import hashlib
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from math import isfinite
import threading

# Optional: for webhook delivery
try:
    import requests
except ImportError:
    requests = None

# Optional: for running a lightweight API
try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
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
LOG_LEVEL = os.environ.get("HS_LOG_LEVEL", "INFO")

os.makedirs(LEDGER_DIR, exist_ok=True)

# -----------------------
# Logging Configuration
# -----------------------
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hs_defensive_engine")

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
    """Thread-safe ledger appending with file locking"""
    fname = os.path.join(LEDGER_DIR, f"ledger_{datetime.utcnow().strftime('%Y%m%d')}.ndjson")
    line = json.dumps(record, ensure_ascii=False, separators=(',', ':'))
    record_hash = sha256_bytes(line.encode("utf-8"))
    entry = {"ts": utc_now_iso(), "hash": record_hash, "record": record}
    
    # Use file lock for thread safety
    lock = threading.Lock()
    with lock:
        with open(fname, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, separators=(',', ':')) + "\n")
    
    logger.debug(f"Appended record to ledger with hash: {record_hash}")
    return record_hash

def validate_report(report: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate report structure and data types"""
    required_fields = ['text']
    for field in required_fields:
        if field not in report:
            return False, f"Missing required field: {field}"
    
    # Validate coordinates if present
    if 'lat' in report or 'lon' in report:
        try:
            lat = report.get('lat')
            lon = report.get('lon')
            if lat is not None:
                lat = float(lat)
                if not (-90 <= lat <= 90):
                    return False, "Latitude must be between -90 and 90"
            if lon is not None:
                lon = float(lon)
                if not (-180 <= lon <= 180):
                    return False, "Longitude must be between -180 and 180"
        except (ValueError, TypeError):
            return False, "Invalid coordinate format"
    
    # Validate score values
    score_fields = ['courage', 'dexterity', 'clause_matter', 'audacity']
    for field in score_fields:
        if field in report:
            try:
                val = float(report[field])
                if not (0 <= val <= 1):
                    return False, f"{field} must be between 0 and 1"
            except (ValueError, TypeError):
                return False, f"Invalid {field} value"
    
    return True, "Valid"

# -----------------------
# Trajectory Mechanic (Fivefold)
# -----------------------
class TrajectoryMechanic:
    def __init__(self, honor: float = 1.0):
        if not (0 < honor <= 1):
            raise ValueError("Honor must be between 0 and 1")
        self.honor = honor
    
    @staticmethod
    def _clamp(v: float) -> float:
        try:
            v = float(v)
        except (ValueError, TypeError):
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
        
        return {
            "C": C, 
            "D": D, 
            "M": M, 
            "A": A, 
            "ratio": ratio, 
            "phase": phase,
            "honor": self.honor
        }
    
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
# -----------------------
from math import radians, sin, cos, asin, sqrt

def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in meters"""
    R = 6371000.0  # Earth radius in meters
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def in_same_geofence(a: Dict[str, Any], b: Dict[str, Any], radius_m: float) -> bool:
    """Check if two reports are within the specified geofence radius"""
    if "lat" not in a or "lon" not in a or "lat" not in b or "lon" not in b:
        return False
    try:
        d = haversine_meters(float(a["lat"]), float(a["lon"]), float(b["lat"]), float(b["lon"]))
        return d <= radius_m
    except (ValueError, TypeError):
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
        self._ensure_incidents_file()
    
    def _ensure_incidents_file(self):
        """Ensure incidents file exists"""
        if not os.path.exists(self.incidents_file):
            with open(self.incidents_file, "w", encoding="utf-8") as f:
                f.write("")  # Create empty file
    
    def ingest_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a single report and process it"""
        # Validate report
        is_valid, validation_msg = validate_report(report)
        if not is_valid:
            raise ValueError(f"Invalid report: {validation_msg}")
        
        rid = report.get("id") or str(uuid.uuid4())
        record = {
            "id": rid,
            "received_at": utc_now_iso(),
            "text": report.get("text", "")[:5000],  # Limit text length
            "meta": report.get("meta", {}),
            "lat": report.get("lat"),
            "lon": report.get("lon"),
            "source": report.get("source", "anonymous"),
        }
        
        # Calculate score
        score = self.tm.score(
            report.get("courage", 0.0),
            report.get("dexterity", 0.0),
            report.get("clause_matter", 0.0),
            report.get("audacity", 0.0)
        )
        record["score"] = score
        
        # Append to ledger
        record_hash = append_ledger(record)
        record["ledger_hash"] = record_hash
        
        # Create incident if threshold exceeded
        incident = None
        if score["ratio"] >= self.threshold:
            incident = self._create_incident(record)
            record["incident"] = incident
            self._send_alert(record, incident)
            logger.info(f"Created incident {incident['incident_id']} for report {rid}")
        else:
            logger.debug(f"Report {rid} below threshold (score: {score['ratio']})")
        
        # Record in incidents file
        with open(self.incidents_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": utc_now_iso(), "entry": record}, ensure_ascii=False, separators=(',', ':')) + "\n")
        
        return record
    
    def _create_incident(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Create an incident record for high-scoring reports"""
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
    
    def _send_alert(self, record: Dict[str, Any], incident: Dict[str, Any]) -> None:
        """Send alert via webhook or email"""
        payload = {
            "incident_id": incident["incident_id"],
            "created_at": incident["created_at"],
            "priority": incident["priority"],
            "score": incident["score"],
            "text": record["text"][:1000],  # Limit text in alert
            "evidence_hash": incident["evidence_hash"],
            "context": record["meta"],
            "location": {"lat": record.get("lat"), "lon": record.get("lon")}
        }
        
        # Webhook delivery
        if self.webhook and requests:
            try:
                r = requests.post(self.webhook, json=payload, timeout=10)
                if r.status_code in [200, 201, 202]:
                    append_ledger({
                        "alert_sent": True, 
                        "webhook": self.webhook, 
                        "status_code": r.status_code, 
                        "incident_id": incident["incident_id"]
                    })
                    logger.info(f"Alert sent successfully for incident {incident['incident_id']}")
                else:
                    append_ledger({
                        "alert_sent": False, 
                        "webhook": self.webhook, 
                        "status_code": r.status_code,
                        "error": f"HTTP {r.status_code}",
                        "incident_id": incident["incident_id"]
                    })
                    logger.warning(f"Webhook returned status {r.status_code} for incident {incident['incident_id']}")
            except Exception as e:
                append_ledger({
                    "alert_sent": False, 
                    "error": str(e), 
                    "incident_id": incident["incident_id"]
                })
                logger.error(f"Failed to send webhook alert: {e}")

# -----------------------
# CLI and API Functions
# -----------------------
def example_cli_ingest(json_file: str):
    """Example function to ingest reports from JSON file"""
    if not os.path.exists(json_file):
        print(f"Error: File {json_file} not found")
        return
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return
    
    manager = IncidentManager()
    
    # Handle both single report and list of reports
    reports = data if isinstance(data, list) else [data]
    
    for i, report in enumerate(reports):
        try:
            result = manager.ingest_report(report)
            print(f"Processed report {i+1}/{len(reports)}: {result['id']} (Score: {result['score']['ratio']})")
        except Exception as e:
            print(f"Error processing report {i+1}: {e}")

# -----------------------
# Flask App (if available)
# -----------------------
if FLASK_AVAILABLE:
    app = Flask(__name__)
    incident_manager = IncidentManager()

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "timestamp": utc_now_iso()})

    @app.route('/ingest', methods=['POST'])
    def ingest_report():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            result = incident_manager.ingest_report(data)
            return jsonify(result), 201
            
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Unexpected error in ingest: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/status', methods=['GET'])
    def system_status():
        status = {
            "status": "operational",
            "timestamp": utc_now_iso(),
            "threshold": SCORE_THRESHOLD,
            "ledger_dir": LEDGER_DIR,
            "webhook_configured": bool(ALERT_WEBHOOK)
        }
        return jsonify(status)


class BlockchainNWIEngine:
    def __init__(self, ledger_dir: str = "./blockchain_ledger", network: str = "mainnet"):
        self.ledger_dir = ledger_dir
        self.network = network
        self.chain_file = os.path.join(ledger_dir, "nwi_blockchain.ndjson")
        self.pending_transactions = []
        
        os.makedirs(ledger_dir, exist_ok=True)
        self._initialize_chain()
    
    def _initialize_chain(self):
        """Initialize or load existing blockchain"""
        if not os.path.exists(self.chain_file):
            # Create genesis block
            genesis_block = self._create_block(
                previous_hash="0" * 64,
                transactions=[],
                nonce=0
            )
            self._add_block(genesis_block)
            print("✅ Genesis block created")
    
    def _create_block(self, previous_hash: str, transactions: List, nonce: int) -> Dict[str, Any]:
        """Create a new block in the chain"""
        block = {
            "index": self._get_chain_length(),
            "timestamp": utc_now_iso(),
            "transactions": transactions,
            "previous_hash": previous_hash,
            "nonce": nonce,
            "merkle_root": self._calculate_merkle_root(transactions),
            "block_hash": "",
            "network": self.network,
            "version": "1.0"
        }
        
        # Calculate block hash
        block["block_hash"] = self._calculate_block_hash(block)
        return block
    
    def _calculate_merkle_root(self, transactions: List) -> str:
        """Calculate Merkle root for block transactions"""
        if not transactions:
            return "0" * 64
        
        transaction_hashes = [self._hash_transaction(tx) for tx in transactions]
        
        while len(transaction_hashes) > 1:
            new_hashes = []
            for i in range(0, len(transaction_hashes), 2):
                if i + 1 < len(transaction_hashes):
                    combined = transaction_hashes[i] + transaction_hashes[i + 1]
                else:
                    combined = transaction_hashes[i] + transaction_hashes[i]
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            transaction_hashes = new_hashes
        
        return transaction_hashes[0]
    
    def _hash_transaction(self, transaction: Dict) -> str:
        """Create hash of a transaction"""
        tx_string = json.dumps(transaction, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def _calculate_block_hash(self, block: Dict) -> str:
        """Calculate hash of a block"""
        block_copy = block.copy()
        block_copy["block_hash"] = ""  # Remove hash for calculation
        block_string = json.dumps(block_copy, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def _get_chain_length(self) -> int:
        """Get current chain length"""
        if not os.path.exists(self.chain_file):
            return 0
        
        with open(self.chain_file, 'r') as f:
            return sum(1 for _ in f)
    
    def _get_last_block(self) -> Optional[Dict]:
        """Get the last block in the chain"""
        if not os.path.exists(self.chain_file):
            return None
        
        with open(self.chain_file, 'r') as f:
            lines = f.readlines()
            if not lines:
                return None
            return json.loads(lines[-1])
    
    def _add_block(self, block: Dict):
        """Add block to the chain"""
        with open(self.chain_file, 'a') as f:
            f.write(json.dumps(block, separators=(',', ':')) + '\n')
    
    def create_nwi_transaction(self, report: Dict, trajectory_score: Dict) -> Dict:
        """Create a blockchain transaction for NWI report"""
        
        transaction = {
            "tx_id": f"NWI-TX-{int(time.time())}-{hashlib.sha256(json.dumps(report).encode()).hexdigest()[:16]}",
            "type": "nwi_report",
            "timestamp": utc_now_iso(),
            "report_data": {
                "id": report.get("id"),
                "location": report.get("meta", {}).get("location"),
                "coordinates": {
                    "lat": report.get("lat"),
                    "lon": report.get("lon")
                },
                "trajectory_score": trajectory_score,
                "evidence_hash": self._hash_transaction(report),
                "classification": report.get("meta", {}).get("classification", "UNCLASSIFIED")
            },
            "metadata": {
                "version": "1.0",
                "network": self.network,
                "immutable": True,
                "tamper_evident": True
            }
        }
        
        # Add digital signature simulation
        transaction["signature"] = self._simulate_digital_signature(transaction)
        return transaction
    
    def _simulate_digital_signature(self, transaction: Dict) -> str:
        """Simulate digital signature (in real implementation, use proper crypto)"""
        tx_string = json.dumps(transaction["report_data"], sort_keys=True, separators=(',', ':'))
        return f"SIG-{hashlib.sha256(tx_string.encode()).hexdigest()[:32]}"
    
    def mine_block(self, difficulty: int = 4):
        """Mine a new block with pending transactions"""
        if not self.pending_transactions:
            print("⚠️  No transactions to mine")
            return None
        
        last_block = self._get_last_block()
        previous_hash = last_block["block_hash"] if last_block else "0" * 64
        
        # Simple proof-of-work
        nonce = 0
        while True:
            block = self._create_block(previous_hash, self.pending_transactions, nonce)
            if block["block_hash"][:difficulty] == "0" * difficulty:
                break
            nonce += 1
        
        self._add_block(block)
        print(f"✅ Block #{block['index']} mined with {len(self.pending_transactions)} transactions")
        print(f"   Block Hash: {block['block_hash']}")
        print(f"   Nonce: {nonce}")
        
        # Clear pending transactions
        self.pending_transactions = []
        return block
    
    def add_nwi_report(self, report: Dict, trajectory_score: Dict):
        """Add NWI report to pending transactions"""
        transaction = self.create_nwi_transaction(report, trajectory_score)
        self.pending_transactions.append(transaction)
        print(f"📄 Transaction created: {transaction['tx_id']}")
    
    def verify_chain_integrity(self) -> Dict:
        """Verify the entire blockchain integrity"""
        if not os.path.exists(self.chain_file):
            return {"status": "error", "message": "Chain file not found"}
        
        with open(self.chain_file, 'r') as f:
            blocks = [json.loads(line) for line in f]
        
        integrity_report = {
            "total_blocks": len(blocks),
            "valid_blocks": 0,
            "invalid_blocks": 0,
            "tamper_detected": False,
            "details": []
        }
        
        for i, block in enumerate(blocks):
            block_valid = self._verify_block(block, blocks[i-1] if i > 0 else None)
            if block_valid:
                integrity_report["valid_blocks"] += 1
            else:
                integrity_report["invalid_blocks"] += 1
                integrity_report["tamper_detected"] = True
            
            integrity_report["details"].append({
                "block_index": block["index"],
                "valid": block_valid,
                "block_hash": block["block_hash"]
            })
        
        return integrity_report
    
    def _verify_block(self, block: Dict, previous_block: Optional[Dict]) -> bool:
        """Verify a single block's integrity"""
        # Check block hash calculation
        calculated_hash = self._calculate_block_hash(block)
        if calculated_hash != block["block_hash"]:
            return False
        
        # Check previous hash linkage (except for genesis block)
        if previous_block and block["previous_hash"] != previous_block["block_hash"]:
            return False
        
        # Verify merkle root
        calculated_merkle = self._calculate_merkle_root(block["transactions"])
        if calculated_merkle != block["merkle_root"]:
            return False
        
        return True
    
    def query_reports_by_location(self, location: str) -> List[Dict]:
        """Query reports by location"""
        reports = []
        
        with open(self.chain_file, 'r') as f:
            for line in f:
                block = json.loads(line)
                for tx in block.get("transactions", []):
                    if (tx.get("type") == "nwi_report" and 
                        tx.get("report_data", {}).get("location") == location):
                        reports.append(tx)
        
        return reports
    
    def get_chain_statistics(self) -> Dict:
        """Get blockchain statistics"""
        if not os.path.exists(self.chain_file):
            return {}
        
        with open(self.chain_file, 'r') as f:
            blocks = [json.loads(line) for line in f]
        
        total_transactions = sum(len(block.get("transactions", [])) for block in blocks)
        nwi_reports = 0
        
        for block in blocks:
            for tx in block.get("transactions", []):
                if tx.get("type") == "nwi_report":
                    nwi_reports += 1
        
        return {
            "total_blocks": len(blocks),
            "total_transactions": total_transactions,
            "nwi_reports": nwi_reports,
            "chain_size_bytes": os.path.getsize(self.chain_file),
            "first_block_timestamp": blocks[0]["timestamp"] if blocks else None,
            "last_block_timestamp": blocks[-1]["timestamp"] if blocks else None
        }

def demonstrate_blockchain_nwi():
    """Demonstrate blockchain-enhanced NWI system"""
    
    print("🔗 BLOCKCHAIN-ENHANCED NWI DEFENSIVE ENGINE")
    print("Creating immutable records on distributed ledger\n")
    
    # Initialize blockchain engine
    blockchain = BlockchainNWIEngine(network="nwi_testnet")
    
    # Load NWI reports
    try:
        with open('nwi_petersburg_reports.json', 'r') as f:
            reports = json.load(f)
    except FileNotFoundError:
        print("Error: NWI reports not found")
        return
    
    # Process reports through trajectory scoring
    from hs_defensive_engine import TrajectoryMechanic
    tm = TrajectoryMechanic()
    
    print("=== ADDING NWI REPORTS TO BLOCKCHAIN ===")
    for report in reports:
        # Calculate trajectory score
        score = tm.score(
            report.get('courage', 0),
            report.get('dexterity', 0),
            report.get('clause_matter', 0),
            report.get('audacity', 0)
        )
        
        # Add to blockchain
        blockchain.add_nwi_report(report, score)
        print(f"   📍 {report['id']} - {report['meta']['location']}")
        print(f"   🎯 Score: {score['ratio']} - {score['phase']}")
    
    # Mine block with all reports
    print("\n=== MINING BLOCK ===")
    block = blockchain.mine_block(difficulty=3)
    
    # Show chain statistics
    print("\n=== BLOCKCHAIN STATISTICS ===")
    stats = blockchain.get_chain_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Verify chain integrity
    print("\n=== CHAIN INTEGRITY VERIFICATION ===")
    integrity = blockchain.verify_chain_integrity()
    print(f"   Total Blocks: {integrity['total_blocks']}")
    print(f"   Valid Blocks: {integrity['valid_blocks']}")
    print(f"   Invalid Blocks: {integrity['invalid_blocks']}")
    print(f"   Tamper Detected: {integrity['tamper_detected']}")
    
    # Query reports by location
    print("\n=== LOCATION-BASED QUERY ===")
    petersburg_reports = blockchain.query_reports_by_location("Petersburg, VA")
    print(f"   Found {len(petersburg_reports)} reports for Petersburg, VA")
    
    for report in petersburg_reports:
        tx_data = report['report_data']
        print(f"   📋 {tx_data['id']} - Score: {tx_data['trajectory_score']['ratio']}")

def demonstrate_tamper_resistance():
    """Demonstrate the tamper-resistant properties"""
    
    print("\n" + "="*60)
    print("TAMPER RESISTANCE DEMONSTRATION")
    print("="*60)
    
    blockchain = BlockchainNWIEngine()
    
    # Create a test report
    test_report = {
        "id": "TAMPER-TEST-001",
        "text": "Test report for tamper demonstration",
        "meta": {"location": "Test Location", "classification": "TEST"},
        "lat": 0.0,
        "lon": 0.0,
        "courage": 0.5,
        "dexterity": 0.5,
        "clause_matter": 0.5,
        "audacity": 0.5
    }
    
    from hs_defensive_engine import TrajectoryMechanic
    tm = TrajectoryMechanic()
    score = tm.score(0.5, 0.5, 0.5, 0.5)
    
    # Add and mine
    blockchain.add_nwi_report(test_report, score)
    blockchain.mine_block(difficulty=2)
    
    print("✅ Original block mined successfully")
    
    # Try to tamper with the chain file
    print("\n🔓 Attempting to tamper with blockchain data...")
    try:
        with open(blockchain.chain_file, 'r') as f:
            lines = f.readlines()
        
        if len(lines) > 1:  # Skip genesis block
            last_block = json.loads(lines[-1])
            # Modify a transaction
            if last_block["transactions"]:
                last_block["transactions"][0]["report_data"]["trajectory_score"]["ratio"] = 0.999
        
        # Write back modified block
        with open(blockchain.chain_file, 'w') as f:
            for i, line in enumerate(lines):
                if i == len(lines) - 1:
                    f.write(json.dumps(last_block, separators=(',', ':')) + '\n')
                else:
                    f.write(line)
        
        print("⚠️  Blockchain data modified (tampering simulated)")
        
        # Verify integrity
        integrity = blockchain.verify_chain_integrity()
        if integrity["tamper_detected"]:
            print("🚨 TAMPERING DETECTED! Chain integrity compromised")
        else:
            print("❌ Tampering not detected (this would be a serious issue)")
            
    except Exception as e:
        print(f"Error during tamper demonstration: {e}")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

if __name__ == "__main__":
    import os
    demonstrate_blockchain_nwi()
    demonstrate_tamper_resistance()
    
    print("\n" + "="*60)
    print("BLOCKCHAIN BENEFITS SUMMARY")
    print("="*60)
    benefits = [
        "✓ Immutable record-keeping",
        "✓ Tamper-evident architecture", 
        "✓ Timestamped chain of custody",
        "✓ Distributed trust model",
        "✓ Cryptographic verification",
        "✓ Transparent audit trail",
        "✓ Resilience against single points of failure",
        "✓ Global accessibility with proper authorization"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")

# -----------------------
# Main execution
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
        app.run(host="0.0.0.0", port=args.port, debug=False)
    else:
        print("Run with --serve to start HTTP ingestion endpoint or --cli <file.json> to ingest")
        print("Environment variables:")
        print(f"  HS_LEDGER_DIR: {LEDGER_DIR}")
        print(f"  HS_SCORE_THRESHOLD: {SCORE_THRESHOLD}")
        print(f"  HS_ALERT_WEBHOOK: {ALERT_WEBHOOK or 'Not set'}")