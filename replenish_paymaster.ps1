<#
.SYNOPSIS
    TGDK / HSM Paymaster Replenishment Daemon
    Monitors ETH balance of Paymaster and replenishes from local economy ledger.
#>

# --- CONFIGURATION ---
$RpcUrl         = "https://sepolia.infura.io/v3/YOUR_INFURA_KEY"
$PaymasterAddr  = "0xYourPaymasterAddress"
$LedgerPath     = "C:\Users\$env:USERNAME\OneDrive\Desktop\HSM-MOD---1--main\economy.json"
$ThresholdEth   = 0.01         # ETH threshold before triggering top-up
$TopUpAmount    = 0.05         # ETH to send when low
$ConversionRate = 10000        # 10,000 HSM = 1 ETH gas equivalence
$IntervalSec    = 60           # check every 60s
$Account        = "0xYourOperatorWallet"
$PrivateKey     = "YOUR_PRIVATE_KEY"  # ⚠️ Use env variable or encrypted vault in production

# --- WEB3 SETUP ---
npm install web3 | Out-Null
Add-Type -AssemblyName System.Web

$js = @"
const Web3 = require('web3');
const web3 = new Web3('$RpcUrl');
(async () => {
  const balance = await web3.eth.getBalance('$PaymasterAddr');
  console.log(balance);
})();
"@

function Get-EthBalanceWei {
    node -e $js 2>$null
}

function WeiToEth([decimal]$wei) {
    return [math]::Round(($wei / [math]::Pow(10,18)), 6)
}

function EthToWei([decimal]$eth) {
    return [math]::Floor($eth * [math]::Pow(10,18))
}

function Update-Ledger([decimal]$ethUsed, [decimal]$rate) {
    if (-not (Test-Path $LedgerPath)) {
        Write-Warning "Economy ledger not found: $LedgerPath"
        return
    }
    $ledger = Get-Content $LedgerPath | ConvertFrom-Json
    $tokenCost = [math]::Round($ethUsed * $rate, 3)
    $entry = [pscustomobject]@{
        timestamp  = (Get-Date).ToString("u")
        eth_used   = $ethUsed
        hsm_deduct = $tokenCost
        event      = "Paymaster top-up"
    }
    $ledger.gas_deductions += $entry
    $ledger.total_eth_spent += $ethUsed
    $ledger.total_hsm_deducted += $tokenCost
    $ledger | ConvertTo-Json -Depth 5 | Set-Content $LedgerPath
    Write-Host "[Ledger] Deducted $tokenCost HSM for $ethUsed ETH top-up" -ForegroundColor Cyan
}

# --- MAIN LOOP ---
Write-Host "=== TGDK HSM Paymaster Replenish Daemon ===" -ForegroundColor Yellow
Write-Host "Monitoring: $PaymasterAddr" -ForegroundColor Gray
Write-Host "Check interval: $IntervalSec sec | Threshold: $ThresholdEth ETH`n"

while ($true) {
    try {
        $balanceWei = Get-EthBalanceWei
        if (-not $balanceWei) {
            Write-Warning "Could not fetch ETH balance."
            Start-Sleep -Seconds $IntervalSec
            continue
        }
        $balanceEth = WeiToEth $balanceWei
        Write-Host ("[{0}] Paymaster balance: {1} ETH" -f (Get-Date -Format "HH:mm:ss"), $balanceEth) -ForegroundColor Green

        if ($balanceEth -lt $ThresholdEth) {
            Write-Host "[!] Low balance detected. Initiating top-up..." -ForegroundColor Yellow
            $ethUsed = $TopUpAmount
            Update-Ledger -ethUsed $ethUsed -rate $ConversionRate

            # (OPTIONAL) send ETH to Paymaster automatically if desired
            # Example using web3.js from Node
            $sendJS = @"
const Web3 = require('web3');
const web3 = new Web3('$RpcUrl');
(async () => {
  const tx = {
    from: '$Account',
    to: '$PaymasterAddr',
    value: web3.utils.toWei('$TopUpAmount', 'ether'),
    gas: 21000
  };
  const signed = await web3.eth.accounts.signTransaction(tx, '$PrivateKey');
  const receipt = await web3.eth.sendSignedTransaction(signed.rawTransaction);
  console.log(receipt.transactionHash);
})();
"@
            $txHash = node -e $sendJS 2>$null
            Write-Host "[Tx] Replenishment sent. Hash: $txHash" -ForegroundColor Magenta
        }

    } catch {
        Write-Warning "Error: $_"
    }

    Start-Sleep -Seconds $IntervalSec
}
