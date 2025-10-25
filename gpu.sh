#!/usr/bin/env bash
# TGDK / HSM Concurrent Mining Launcher
# Automatically launches optimal number of concurrent CME.py instances based on GPU capacity

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(command -v python3 || command -v python)"

echo "[TGDK] 🔧 Detecting GPU resources..."

# --- Detect GPU cores / SM count ---
GPU_COUNT=0
if command -v nvidia-smi >/dev/null 2>&1; then
    GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
    GPU_MODEL=$(nvidia-smi --query-gpu=gpu_name --format=csv,noheader | head -n1)
    echo "[GPU] NVIDIA detected: $GPU_MODEL ($GPU_COUNT GPU(s))"
elif command -v rocm-smi >/dev/null 2>&1; then
    GPU_COUNT=$(rocm-smi --showproductname | grep -c 'GPU')
    echo "[GPU] AMD ROCm detected ($GPU_COUNT GPU(s))"
else
    echo "[GPU] ⚠️  No GPU detected — using CPU fallback"
fi

# --- Determine optimal concurrency ---
if [[ $GPU_COUNT -gt 0 ]]; then
    # Aim for ~2 concurrent processes per GPU for good saturation
    INSTANCES=$((GPU_COUNT * 2))
else
    # CPU fallback: use half the logical cores
    CPU_CORES=$(grep -c ^processor /proc/cpuinfo 2>/dev/null || sysctl -n hw.logicalcpu)
    INSTANCES=$((CPU_CORES / 2))
    [[ $INSTANCES -lt 1 ]] && INSTANCES=1
fi

echo "[TGDK] Launching $INSTANCES concurrent HSM miners..."
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# --- Launch instances ---
for i in $(seq 1 $INSTANCES); do
    GPU_ID=$(( (i - 1) % (GPU_COUNT > 0 ? GPU_COUNT : 1) ))
    LOG_FILE="$LOG_DIR/miner_$i.log"
    echo "[Instance $i] Starting on GPU $GPU_ID → $LOG_FILE"
    
    # Optional: set CUDA_VISIBLE_DEVICES if GPUs exist
    if [[ $GPU_COUNT -gt 0 ]]; then
        CUDA_VISIBLE_DEVICES=$GPU_ID nohup "$PYTHON_BIN" "$SCRIPT_DIR/CME.py" >"$LOG_FILE" 2>&1 &
    else
        nohup "$PYTHON_BIN" "$SCRIPT_DIR/CME.py" >"$LOG_FILE" 2>&1 &
    fi
    
    sleep 1  # slight stagger
done

echo "[TGDK] ✅ All HSM miner instances launched."
echo "[TGDK] Logs are stored in: $LOG_DIR"
