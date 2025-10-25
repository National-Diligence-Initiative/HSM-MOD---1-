# TGDK Watchdog — Restarts CME miner if killed
$MinerPath = "C:\Users\jtart\OneDrive\Desktop\HSM-MOD---1--main\CME.py"
$Python = "python"
$LogDir = "C:\Users\jtart\OneDrive\Desktop\HSM-MOD---1--main\logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

while ($true) {
    $running = Get-Process | Where-Object { $_.ProcessName -match "python" -and $_.Path -match "CME.py" }
    if (-not $running) {
        $logFile = Join-Path $LogDir ("respawn_" + (Get-Date -Format "HHmmss") + ".log")
        Write-Host "[Watchdog] Restarting CME miner..."
        Start-Process -FilePath $Python -ArgumentList $MinerPath -RedirectStandardOutput $logFile -RedirectStandardError $logFile
    }
    Start-Sleep -Seconds 10
}
