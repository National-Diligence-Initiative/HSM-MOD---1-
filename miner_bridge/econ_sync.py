import json, time, os
from web3 import Web3

provider = Web3(Web3.HTTPProvider("https://sepolia.infura.io/v3/YOUR_KEY"))
paymaster_address = "0xYOUR_PAYMASTER"
paymaster_abi = json.load(open("HSMTokenPaymaster.json"))
paymaster = provider.eth.contract(address=paymaster_address, abi=paymaster_abi)

economy_path = "miner_bridge/ledger/economy.json"

def sync_gas_deductions():
    last_block = 0
    while True:
        events = paymaster.events.GasSpent.createFilter(fromBlock=last_block).get_all_entries()
        if events:
            with open(economy_path, "r+") as f:
                econ = json.load(f)
                for e in events:
                    u = e["args"]
                    econ["gas_deductions"].append({
                        "user": u["user"],
                        "eth_cost": str(u["ethCost"]),
                        "token_cost": str(u["tokenCost"]),
                        "tx_hash": u["txHash"].hex()
                    })
                f.seek(0)
                json.dump(econ, f, indent=2)
            last_block = provider.eth.block_number
        time.sleep(30)

