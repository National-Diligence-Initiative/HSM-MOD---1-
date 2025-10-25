# NDI Watchdog — Restarts CME miner if killed
$MinerPath = "C:\Users\jtart\OneDrive\Desktop\HSM-MOD---1--main\CME.py"
$Python    = "python"
$LogDir    = "C:\Users\jtart\OneDrive\Desktop\HSM-MOD---1--main\logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

while ($true) {
    $running = Get-Process | Where-Object { $_.ProcessName -match "python" -and $_.Path -match "CME.py" }
    if (-not $running) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $outFile   = Join-Path $LogDir "respawn_$timestamp.out.log"
        $errFile   = Join-Path $LogDir "respawn_$timestamp.err.log"
        Write-Host "[Watchdog] Restarting CME miner ($timestamp)..."
        Start-Process -FilePath $Python `
            -ArgumentList $MinerPath `
            -RedirectStandardOutput $outFile `
            -RedirectStandardError  $errFile `
            -WindowStyle Hidden
    }
    Start-Sleep -Seconds 10
}
