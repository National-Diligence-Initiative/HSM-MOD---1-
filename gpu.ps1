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

if ($GPUCount -gt 0) {
    # Try to query memory safely
    try {
        $gpuInfo = & nvidia-smi.exe --query-gpu=memory.total --format=csv,noheader 2>$null
        if ($gpuInfo -is [string]) { $gpuInfo = @($gpuInfo) }  # ensure it's an array

        # Parse first GPU line robustly
        $gpuLine = $gpuInfo[0].ToString()
        $gpuMemory = ($gpuLine -replace '[^\d]', '') -as [int]

        if ($gpuMemory -eq 0 -or $null -eq $gpuMemory) {
            Write-Host "[GPU] ⚠️  Could not parse GPU memory, using fallback = 8192 MB" -ForegroundColor Yellow
            $gpuMemory = 8192
        }

        if ($gpuMemory -ge 16000) {
            $Instances = $GPUCount * 8
        } elseif ($gpuMemory -ge 8000) {
            $Instances = $GPUCount * 4
        } else {
            $Instances = $GPUCount * 2
        }
        Write-Host "[GPU] Memory per GPU: $gpuMemory MB → launching $Instances instances" -ForegroundColor Cyan

    } catch {
        Write-Host "[GPU] ⚠️  Could not detect GPU memory, defaulting to 2 instances" -ForegroundColor Yellow
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
