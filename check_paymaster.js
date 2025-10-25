require('dotenv').config();
const { ethers } = require('ethers');

// === Load from .env ===
const RPC_URL = process.env.RPC_URL || "https://sepolia.infura.io/v3/YOUR_KEY";
const PAYMASTER_ADDR = process.env.PAYMASTER_ADDR;

const PAYMASTER_ABI = [
  {
    "inputs": [],
    "name": "getBalance",
    "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
    "stateMutability": "view",
    "type": "function"
  }
];

async function main() {
  const provider = new ethers.providers.JsonRpcProvider(RPC_URL);
  const paymaster = new ethers.Contract(PAYMASTER_ADDR, PAYMASTER_ABI, provider);

  const balance = await paymaster.getBalance();
  console.log(`[TGDK] Paymaster Balance: ${ethers.utils.formatEther(balance)} ETH`);
}

main().catch(err => console.error(err));
