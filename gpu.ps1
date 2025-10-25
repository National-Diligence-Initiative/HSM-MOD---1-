<#
TGDK / HSM Concurrent Mining Launcher (PowerShell Edition)
Auto-detects GPU or CPU capacity and launches optimal CME.py instances
Logs output per instance in .\logs\
#>

# --- Configuration ---
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Python = "python.exe"
$LogDir = Join-Path $ScriptDir "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

Write-Host "[TGDK] 🔧 Detecting GPU resources..." -ForegroundColor Cyan

# --- Detect GPU count ---
$GPUCount = 0
try {
    $nvidia = & nvidia-smi.exe --query-gpu=name --format=csv,noheader 2>$null
    if ($nvidia) {
        $GPUCount = ($nvidia | Measure-Object).Count
        Write-Host "[GPU] NVIDIA detected: $($nvidia[0]) ($GPUCount GPU(s))" -ForegroundColor Green
    } else {
        throw
    }
} catch {
    try {
        $rocm = & rocm-smi.exe --showproductname 2>$null
        if ($rocm) {
            $GPUCount = ($rocm | Select-String "GPU").Count
            Write-Host "[GPU] AMD ROCm detected ($GPUCount GPU(s))" -ForegroundColor Green
        } else {
            throw
        }
    } catch {
        Write-Host "[GPU] ⚠️  No GPU detected — using CPU fallback" -ForegroundColor Yellow
    }
}

# --- Determine optimal concurrency ---
if ($GPUCount -gt 0) {
    $Instances = $GPUCount * 2
} else {
    $CPUCount = [Environment]::ProcessorCount
    $Instances = [Math]::Max([int]($CPUCount / 2), 1)
}

Write-Host "[TGDK] Launching $Instances concurrent HSM miner instance(s)..." -ForegroundColor Cyan

# --- Launch miners ---
for ($i = 1; $i -le $Instances; $i++) {
    $LogFile = Join-Path $LogDir ("miner_{0}.log" -f $i)
    $GPUIndex = if ($GPUCount -gt 0) { ($i - 1) % $GPUCount } else { 0 }
    Write-Host "[Instance $i] Starting on GPU $GPUIndex → $LogFile" -ForegroundColor Magenta

    # Set CUDA_VISIBLE_DEVICES if NVIDIA GPU exists
    if ($GPUCount -gt 0) {
        $env:CUDA_VISIBLE_DEVICES = "$GPUIndex"
    }

    Start-Process -FilePath $Python `
        -ArgumentList "$ScriptDir\CME.py" `
        -RedirectStandardOutput $LogFile `
        -RedirectStandardError $LogFile `
        -WindowStyle Hidden
    Start-Sleep -Seconds 1
}

Write-Host "[TGDK] ✅ All HSM miner instances launched."
Write-Host "[TGDK] Logs available in: $LogDir" -ForegroundColor Cyan
