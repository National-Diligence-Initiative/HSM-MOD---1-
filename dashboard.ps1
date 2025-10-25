<#
TGDK HSM Miner Dashboard (PowerShell Edition)
Monitors CME.py instances, GPU utilization, and block output.
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
    Clear-Host
    Write-Host "=== TGDK / HSM Miner Dashboard ===" -ForegroundColor Cyan
    Write-Host ("Started: {0} | Uptime: {1}" -f $startTime, (Get-Date) - $startTime)
    Write-Host "----------------------------------"

    # GPU status
    try {
        $gpuStatus = & cmd /c $gpuCmd 2>$null
        if ($gpuStatus) {
            $gpuLines = $gpuStatus -split "`n"
            $i = 0
            foreach ($line in $gpuLines) {
                $fields = $line -split ","
                $util   = ($fields[0] -replace '[^\d]','')
                $memU   = ($fields[1] -replace '[^\d]','')
                $memT   = ($fields[2] -replace '[^\d]','')
                $pct    = [int]($memU * 100 / [Math]::Max($memT,1))
                Write-Host ("GPU[$i] {0,3}% load | {1,4}% mem ({2} / {3} MiB)" -f $util, $pct, $memU, $memT)
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
    $logFiles = Get-ChildItem $LogDir -Filter "miner_*.log"
    $totalBlocks = 0
    foreach ($log in $logFiles) {
        $count = (Select-String -Path $log.FullName -Pattern "Block mined" -SimpleMatch).Count
        $totalBlocks += $count
    }

    $delta = $totalBlocks - $prevBlocks
    Write-Host ("[Blocks] Total: {0} | Δ {1} since last refresh" -f $totalBlocks, $delta)
    $prevBlocks = $totalBlocks

    # Quick summary of active jobs
    $running = Get-Job | Where-Object { $_.State -eq 'Running' }
    Write-Host ("[Instances] {0} active miner(s)" -f $running.Count)

    Write-Host "----------------------------------"
    Write-Host "Press Ctrl+C to exit dashboard."
    Start-Sleep -Seconds 5
}
