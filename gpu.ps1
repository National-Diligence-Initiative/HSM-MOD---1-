<#
TGDK / HSM Concurrent Mining Launcher (PowerShell Edition)
Auto-detects GPU or CPU capacity and launches optimal CME.py instances
Logs output per instance in .\logs\
#>

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

# --- Determine optimal concurrency dynamically ---
if ($GPUCount -gt 0) {
    # Query GPU memory to scale instance count
    $gpuInfo = & nvidia-smi.exe --query-gpu=memory.total --format=csv,noheader 2>$null
    $gpuMemory = [int]($gpuInfo[0].Split()[0])
    
    if ($gpuMemory -ge 16000) {
        # High-memory GPU (RTX 3080, 4080, etc.)
        $Instances = $GPUCount * 8
    } elseif ($gpuMemory -ge 8000) {
        # Mid-range GPU
        $Instances = $GPUCount * 4
    } else {
        # Low-memory GPU
        $Instances = $GPUCount * 2
    }
} else {
    # CPU fallback
    $CPUCount = [Environment]::ProcessorCount
    $Instances = [Math]::Max([int]($CPUCount * 0.75), 2)
}


# --- Launch miners ---
for ($i = 1; $i -le $Instances; $i++) {
    $LogFile = Join-Path $LogDir ("miner_{0}.log" -f $i)
    $GPUIndex = if ($GPUCount -gt 0) { ($i - 1) % $GPUCount } else { 0 }
    Write-Host "[Instance $i] Starting on GPU $GPUIndex → $LogFile" -ForegroundColor Magenta

    # Set CUDA_VISIBLE_DEVICES if NVIDIA GPU exists
    if ($GPUCount -gt 0) {
        $env:CUDA_VISIBLE_DEVICES = "$GPUIndex"
    }

    # Use Out-File for non-conflicting output redirection
    Start-Job -ScriptBlock {
        param($Python, $ScriptDir, $LogFile)
        & $Python "$ScriptDir\CME.py" *>> $LogFile
    } -ArgumentList $Python, $ScriptDir, $LogFile | Out-Null

    Start-Sleep -Milliseconds 500
}

Write-Host "[TGDK] ✅ All HSM miner instances launched."
Write-Host "[TGDK] Logs available in: $LogDir" -ForegroundColor Cyan
