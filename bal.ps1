$RPC_URL = "https://sepolia.infura.io/v3/b63da16ef1444755ba05b324dfc2f540"
$ADDRESS = ""

$body = @{
  jsonrpc = "2.0"
  method  = "eth_getBalance"
  params  = @($ADDRESS, "latest")
  id      = 1
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri $RPC_URL -Method POST -ContentType "application/json" -Body $body
$data = $response.Content | ConvertFrom-Json
$balanceWei = [System.Numerics.BigInteger]::Parse($data.result.Substring(2), [System.Globalization.NumberStyles]::HexNumber)
$balanceEth = $balanceWei / [math]::Pow(10,18)
Write-Host "💰 Paymaster Balance:" $balanceEth "ETH"
