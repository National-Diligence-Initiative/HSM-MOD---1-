# TGDK HSM Miner Multi-Instance Scaler
# Automatically launches optimal number of CME miners based on GPU memory and load.

$Python   = "python"
$Miner    = "C:\Users\jtart\OneDrive\Desktop\HSM-MOD---1--main\CME.py"
$LogDir   = "C:\Users\jtart\OneDrive\Desktop\HSM-MOD---1--main\logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

# --- GPU info ---
Write-Host "[TGDK] 🔍 Detecting GPU..."
$gpuQuery = & nvidia-smi --query-gpu=memory.total,memory.used --format=csv,noheader 2>$null
if (-not $gpuQuery) {
    Write-Host "[TGDK] ⚠️  No NVIDIA GPU detected — defaulting to 2 CPU instances."
    $gpuTotalMiB = 8192
    $gpuUsedMiB  = 0
} else {
    $fields = $gpuQuery -split ","
    $gpuTotalMiB = [int]($fields[0] -replace "[^0-9]")
    $gpuUsedMiB  = [int]($fields[1] -replace "[^0-9]")
}

# --- Adaptive instance count ---
$freeMemMiB   = $gpuTotalMiB - $gpuUsedMiB
$memPerMiner  = 1024      # safe baseline: 1 GB per miner
$maxInstances = [math]::Max(2, [math]::Floor($freeMemMiB / $memPerMiner))
Write-Host "[TGDK] 🧠 GPU total $gpuTotalMiB MiB | free $freeMemMiB MiB → launching $maxInstances miner(s)..."

# --- Launch miners ---
for ($i=1; $i -le $maxInstances; $i++) {
    $outFile = Join-Path $LogDir ("miner_" + $i + ".out.log")
    $errFile = Join-Path $LogDir ("miner_" + $i + ".err.log")
    Write-Host ("[Instance {0}] Starting → GPU 0 | Log {1}" -f $i, $outFile)
    Start-Process -FilePath $Python `
        -ArgumentList $Miner `
        -RedirectStandardOutput $outFile `
        -RedirectStandardError  $errFile `
        -WindowStyle Hidden
    Start-Sleep -Milliseconds 250   # small stagger
}

Write-Host "[TGDK] ✅ All miner instances launched."
Write-Host "[TGDK] Logs: $LogDir"
