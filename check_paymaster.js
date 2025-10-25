import { ethers } from "ethers";
import dotenv from "dotenv";

dotenv.config();

// === Load from .env ===
// (replace with your actual variable names)
const RPC_URL = process.env.RPC_URL || "https://sepolia.infura.io/v3/YOUR_KEY";
const PAYMASTER_ADDR = process.env.PAYMASTER_ADDR;  // e.g., 0x...
const PAYMASTER_ABI = [
  // --- replace with your real ABI ---
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
