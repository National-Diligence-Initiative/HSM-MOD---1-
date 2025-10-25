<#
NDI HSM Miner Dashboard
Monitors TGDK / HSM miner performance, GPU load, blocks, and wallet earnings.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$LogDir    = Join-Path $ScriptDir "logs"
$Economy   = Join-Path $ScriptDir "economy.json"

if (-not (Test-Path $LogDir)) {
    Write-Host "[!] No log directory found. Start gpu.ps1 first." -ForegroundColor Yellow
    exit
}

Write-Host "[TGDK] 🧭 Launching Miner Dashboard..." -ForegroundColor Cyan
$gpuCmd = "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader"

$prevBlocks = 0
$prevRewards = 0
$startTime = Get-Date

function Get-WalletData {
    param($Path)
    if (-not (Test-Path $Path)) { return $null }
    try {
        $json = Get-Content $Path -Raw | ConvertFrom-Json
        return $json
    } catch { return $null }
}

while ($true) {
    $uptime = (Get-Date) - $startTime
    $uptimeStr  = "{0:D2}:{1:D2}:{2:D2}" -f $uptime.Hours, $uptime.Minutes, $uptime.Seconds
    $startedStr = $startTime.ToString("yyyy-MM-dd HH:mm:ss")

    Clear-Host
    Write-Host "=== TGDK / HSM Miner Dashboard ===" -ForegroundColor Cyan
    Write-Host ("Started: " + $startedStr + " | Uptime: " + $uptimeStr)
    Write-Host "----------------------------------"

    # GPU Status
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

    # Block tracking
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

    # Wallet & Rewards
    $walletData = Get-WalletData $Economy
    if ($walletData) {
        $supply = [math]::Round($walletData.supply, 6)
        $txs = $walletData.txs
        $wallets = $walletData.wallets
        $rate = 0
        if ($uptime.TotalHours -gt 0) {
            $rate = [math]::Round(($supply - $prevRewards) / $uptime.TotalHours, 6)
        }
        Write-Host ("[Wallets] {0} | [Supply] {1} TGDK | [Txs] {2} | [Rate] {3} TGDK/hr" -f $wallets, $supply, $txs, $rate)
        $prevRewards = $supply
    } else {
        Write-Host "[Wallet] No economy.json found — mining offline." -ForegroundColor Yellow
    }

    # Miner instance detection
    try {
        $running = Get-Process | Where-Object { $_.ProcessName -match "python" -and $_.Path -match "CME.py" }
        $count = if ($running) { $running.Count } else { 0 }
        Write-Host ("[Instances] {0} active miner process(es)" -f $count) -ForegroundColor Green
    } catch {
        Write-Host "[Instances] ⚠️ Unable to detect active miners" -ForegroundColor Yellow
    }

    Write-Host "----------------------------------"
    Write-Host "Press Ctrl+C to exit dashboard." -ForegroundColor DarkGray
    Start-Sleep -Seconds 5
}
