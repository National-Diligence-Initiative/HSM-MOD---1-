# --- Decrypt .env.enc and export to environment ---
$secPass = Read-Host "Enter decrypt passphrase" -AsSecureString
$ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secPass)
$plainPass = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)

$openssl = "openssl"
$envFile = ".env.enc"

if (Test-Path $envFile) {
    $output = & $openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -d -in $envFile -pass pass:$plainPass 2>$null
    if ($LASTEXITCODE -eq 0) {
        $lines = $output -split "`n"
        foreach ($line in $lines) {
            if ($line -match "=") {
                $pair = $line -split "=", 2
                $key = $pair[0].Trim()
                $value = $pair[1].Trim()
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }
        }
        Write-Host "[TGDK] ✅ Environment loaded in memory only."
    } else {
        Write-Host "[TGDK] ❌ Decryption failed — wrong passphrase or file missing."
    }
} else {
    Write-Host "[TGDK] ⚠️ No .env.enc file found in current directory."
}
