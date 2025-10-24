#!/usr/bin/env bash
# ===============================================================
# TGDK Acorn Firewall - ULTIMATE UNIFIED EDITION
# Author: Black Raven (Sean Tichenor)
# License: TGDK BFE-ST-144SEC-ULTIMATE
# Purpose: AI-aware defensive firewall with HexQuarantine routing,
#          PID-level isolation, and cross-platform pkill-safe control.
# ===============================================================

set -euo pipefail

ROOT="${HOME:-/root}/TGDKVault"
VAULT_PATH="$ROOT/AcornFirewall"
LOG_FILE="$VAULT_PATH/acorn_firewall.log"
KEY_FILE="$VAULT_PATH/.qquap_key.pem"
TMP_HASH="/tmp/.acorn_temp.qquap"
QUAR_LIST="$ROOT/HexQuarantine/quarantine_vectors.txt"
HOST_SEAL="TGDK::OLIVIA::SECURE::ROOT"

mkdir -p "$VAULT_PATH" "$ROOT/HexQuarantine"
touch "$QUAR_LIST"

# === UTILITIES ==================================================
log_event() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

generate_key() {
  [[ -f "$KEY_FILE" ]] || { log_event "[Acorn] Generating QQUAp key..."; openssl genrsa -out "$KEY_FILE" 4096 >/dev/null 2>&1; }
}

apply_firewall() {
  log_event "[Acorn] Applying local firewall rules..."
  iptables -F 2>/dev/null || true
  ip6tables -F 2>/dev/null || true
  iptables -P INPUT DROP
  iptables -P FORWARD DROP
  iptables -P OUTPUT ACCEPT
  iptables -A INPUT -i lo -j ACCEPT
  iptables -A OUTPUT -o lo -j ACCEPT
  log_event "[FIREWALL] Baseline lockdown complete."
}

is_quarantined() {
  local ip="$1" port="${2:-}"
  [[ -n "$port" && $(grep -Fx "${ip}:${port}" "$QUAR_LIST" 2>/dev/null) ]] && return 0
  grep -Fxq "$ip" "$QUAR_LIST" 2>/dev/null
}

find_pid_by_socket() {
  local ip="$1" port="$2" pid=""
  if command -v ss >/dev/null 2>&1; then
    pid=$(ss -tnp state established 2>/dev/null | awk -v R="${ip}:${port}" '$0~R && match($0,/pid=([0-9]+)/,m){print m[1];exit}')
  elif command -v lsof >/dev/null 2>&1; then
    pid=$(lsof -nP -i@"${ip}:${port}" -sTCP:ESTABLISHED -t 2>/dev/null | head -n1)
  elif command -v netstat >/dev/null 2>&1; then
    pid=$(netstat -tnp 2>/dev/null | awk -v R="${ip}:${port}" '$0~R && match($7,/^([0-9]+)\//,m){print m[1];exit}')
  fi
  [[ -n "$pid" ]] && echo "$pid" && return 0
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command "
      \$r='${ip}';\$p=${port};
      \$c=Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
      Where-Object { \$_.RemoteAddress -eq \$r -and \$_.RemotePort -eq \$p };
      if(\$c){\$c.OwningProcess}
    " 2>/dev/null | tr -d '\r'
  fi
}

terminate_pid() {
  local pid="$1"
  if [[ -z "$pid" ]]; then return; fi
  if command -v kill >/dev/null 2>&1; then
    kill -TERM "$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null
  elif command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command "Stop-Process -Id $pid -Force" 2>/dev/null
  fi
}

process_line() {
  local line="$1"
  echo "$line" | grep -q "$HOST_SEAL" && return 0
  local remote_raw port ip
  remote_raw=$(echo "$line" | awk '{print $5}' | tr -d '[]')
  port="${remote_raw##*:}"
  ip="${remote_raw%:*}"
  [[ -z "$ip" ]] && return
  if ! is_quarantined "$ip" "$port"; then
    log_event "[SKIP] $ip:$port not quarantined."
    return
  fi
  local pid
  pid=$(find_pid_by_socket "$ip" "$port" 2>/dev/null || true)
  if [[ -z "$pid" ]]; then
    log_event "[WARN] No PID for $ip:$port"
    return
  fi
  log_event "[ACTION] Terminating PID $pid linked to quarantined vector $ip:$port"
  terminate_pid "$pid"
}

monitor_network() {
  log_event "[Acorn] Monitoring started..."
  while true; do
    netstat -tn 2>/dev/null | grep ESTABLISHED | while read -r line; do
      process_line "$line"
    done
    sleep 4
  done
}

launch_mirrorblade() {
  log_event "[Acorn] MirrorBlade engaged for adaptive defense..."
}

# === MAIN =======================================================
# === MAIN =======================================================
main() {
  log_event "[Acorn ULTIMATE] Starting..."
  generate_key
  apply_firewall
  launch_mirrorblade &
  monitor_network
}

# === KEEP-ALIVE LOOP ============================================
while true; do
  main
  log_event "[Acorn] process stopped - restarting in 5 seconds..."
  sleep 5
done

