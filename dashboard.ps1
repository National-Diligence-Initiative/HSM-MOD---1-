<#
NDI HSM Miner Dashboard
-------------------------
Monitors HSM miner instances, GPU utilization, and block output in real time.
Compatible with gpu.ps1 and CME.py instances.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$LogDir = Join-Path $ScriptDir "logs"
if (-not (Test-Path $LogDir)) {
    Write-Host "[!] No log directory found. Start gpu.ps1 first." -ForegroundColor Yellow
    exit
}

Write-Host "[TGDK] 🧭 Launching Miner Dashboard..." -ForegroundColor Cyan
$gpuCmd = "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader"

# Track previous stats
$prevBlocks = 0
$startTime  = Get-Date

while ($true) {
    # Calculate uptime safely
    $uptime = (Get-Date) - $startTime
    $uptimeStr = "{0:D2}:{1:D2}:{2:D2}" -f $uptime.Hours, $uptime.Minutes, $uptime.Seconds

    Clear-Host
    Write-Host "=== TGDK / HSM Miner Dashboard ===" -ForegroundColor Cyan
    Write-Host ("Started: {0:yyyy-MM-dd HH:mm:ss} | Uptime: {1}" -f $startTime, $uptimeStr)
    Write-Host "----------------------------------"

    # GPU status
    try {
        $gpuStatus = & cmd /c $gpuCmd 2>$null
        if ($gpuStatus) {
            $gpuLines = $gpuStatus -split "`n"
            $i = 0
            foreach ($line in $gpuLines) {
                if ($line.Trim() -eq "") { continue }
                $fields = $line -split ","
                $util   = ($fields[0] -replace '[^\d]','')
                $memU   = ($fields[1] -replace '[^\d]','')
                $memT   = ($fields[2] -replace '[^\d]','')
                if (-not $memT -or $memT -eq 0) { $memT = 1 }
                $pct    = [int]($memU * 100 / $memT)
                Write-Host ("GPU[{0}] {1,3}% load | {2,3}% mem ({3} / {4} MiB)" -f $i, $util, $pct, $memU, $memT)
                $i++
            }
        } else {
            Write-Host "[GPU] No GPU data (CPU mode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[GPU] ⚠️ GPU query failed." -ForegroundColor Yellow
    }

    Write-Host "----------------------------------"

    # Parse miner logs for block count
    $logFiles = Get-ChildItem $LogDir -Filter "miner_*.log" -ErrorAction SilentlyContinue
    $totalBlocks = 0
    foreach ($log in $logFiles) {
        try {
            $count = (Select-String -Path $log.FullName -Pattern "Block mined" -SimpleMatch -ErrorAction SilentlyContinue).Count
            $totalBlocks += $count
        } catch {}
    }

    $delta = $totalBlocks - $prevBlocks
    Write-Host ("[Blocks] Total: {0} | Δ {1} since last refresh" -f $totalBlocks, $delta)
    $prevBlocks = $totalBlocks

    # Quick summary of active miner jobs (launched via gpu.ps1)
    try {
        $running = Get-Process | Where-Object { $_.ProcessName -match "python" -and $_.Path -match "CME.py" }
        Write-Host ("[Instances] {0} active miner process(es)" -f ($running.Count)) -ForegroundColor Green
    } catch {
        Write-Host "[Instances] ⚠️ Unable to detect active miners" -ForegroundColor Yellow
    }

    Write-Host "----------------------------------"
    Write-Host "Press Ctrl+C to exit dashboard." -ForegroundColor DarkGray
    Start-Sleep -Seconds 5
}
