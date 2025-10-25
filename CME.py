# -*- coding: utf-8 -*-
"""
Crypto-Mining Enhanced NWI Defensive Engine
HSM-Enhanced Crypto Mining Engine
Simulated version: all logic preserved, syntax fixed.
"""

import hashlib, time, json, threading, os, secrets
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
from engine import BlockchainNWIEngine
import sys
from web3 import Web3
import json, os, time

try:
    from web3 import Web3
    load_web3 = True
except ImportError:
    load_web3 = False
    
w3 = Web3(Web3.HTTPProvider("https://sepolia.infura.io/v3/YOUR_INFURA_KEY"))
wallet_address = os.getenv("METAMASK_ADDRESS")
private_key = os.getenv("PRIVATE_KEY")
token_contract = w3.eth.contract(address=HSM_CONTRACT_ADDRESS, abi=HSM_ABI)
sys.stdout.reconfigure(encoding='utf-8')


try:
    import cupy as xp  # GPU version
except ImportError:
    import numpy as np  # CPU fallback

try:
    import cupy as xp  # GPU array if available
    gpu_enabled = True
except ImportError:
    xp = np
    gpu_enabled = False

load_dotenv()

def pmz_gpu(iterations: int, size: int = 10_000):
    x = xp.linspace(0.1, 1.0, size)
    for _ in range(iterations):
        x = xp.sqrt(x ** 2 + 1) / (1 + xp.abs(x))
    return xp.asnumpy(x) if hasattr(x, "get") else x

def pmz_live_loop(vector: float = 0.0102, delay: float = 0.01, decay: float = 0.999999):
    """Optimized continuous PMZ loop with adaptive precision and optional GPU."""
    v = xp.array([vector], dtype=xp.float64)
    t0 = time.time()
    iteration = 0

    try:
        while True:
            # core PMZ transform — harmonic convergence function
            v = xp.sqrt(v ** 2 + 1) / (1 + xp.abs(v))
            if gpu_enabled:
                v *= decay

            iteration += 1
            if iteration % 10000 == 0:
                current = float(v[0]) if gpu_enabled else v[0]
                elapsed = time.time() - t0
                print(f"[PMZ] iter={iteration:,}  vector={current:.8f}  elapsed={elapsed:.2f}s")
                t0 = time.time()
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\n🛑 PMZ loop stopped safely.")
        if gpu_enabled:
            v = xp.asnumpy(v)
        return float(v[0])

def subquantumlineate(self, cycles: int = 1000, gpu: bool = False):
        """Simulated PMZ recursion layer."""
        if gpu:
            print("⚙️ Running sub-quantumlineation on GPU (CuPy).")
            data = pmz_gpu(cycles)
        else:
            print("⚙️ Running sub-quantumlineation on CPU.")
            data = [pmz_recurse(cycles, i / 1000) for i in range(100)]
        self.nonce_patterns["pmz_signature"] = sum(data) / len(data)
        return self.nonce_patterns["pmz_signature"]

# --- optional wallet info ---
METAMASK_ADDRESS = os.getenv("METAMASK_ADDRESS", "none")
print(f"Connected to wallet: {METAMASK_ADDRESS}")

# --- load HSM defensive stubs ---
sys.path.append('.')
try:
    from hs_defensive_engine import TrajectoryMechanic, IncidentManager, append_ledger, utc_now_iso
except ImportError:
    class TrajectoryMechanic:
        def score(self, c,d,m,a):
            return {"phase": "Courage", "ratio": (c+d+m+a)/4, "C": c, "D": d, "M": m, "A": a}
    class IncidentManager: pass
    def append_ledger(x): pass
    def utc_now_iso(): return datetime.now(timezone.utc).isoformat()


# ===================================================================
# MAIN MINER
# ===================================================================
class HSMEnhancedMiner:
    def __init__(self, difficulty:int=4, base_reward:float=0.001):
        self.difficulty = difficulty
        self.base_reward = base_reward
        self.mining_active = False
        self.miner_id = f"HSM-MINER-{secrets.token_hex(8)}"
        self.wallet_address = f"NWI_{hashlib.sha256(self.miner_id.encode()).hexdigest()[:40]}"
        self.trajectory_engine = TrajectoryMechanic()
        self.incident_manager = IncidentManager()
        self.mined_blocks = 0
        self.total_rewards = 0.0
        self.threat_based_rewards = 0.0
        self.nonce_patterns = {}
        self.threat_profiles = {}
        print(f"[HSM🔧] Miner Initialized: {self.miner_id}")


    # -----------------------------------------------------------
    def calculate_mining_reward(self, score:float, threat_level:str)->float:
        base_mult = 1.0
        if score >= .9: base_mult=2.5
        elif score >= .8: base_mult=2.0
        elif score >= .7: base_mult=1.5
        elif score >= .6: base_mult=1.2
        threat_mult = {"CRITICAL":3,"HIGH":2,"MEDIUM":1.5,"LOW":1}.get(threat_level,1)
        return self.base_reward * base_mult * threat_mult

    def pmz_recurse(iterations: int, vector: float) -> float:
        """Simulated sub-quantum PMZ iteration (safe finite recursion)."""
        result = vector
        for i in range(iterations):
           # PMZ-style transformation (example harmonic oscillation)
           result = (result ** 2 + 1) ** 0.5 / (1 + abs(result))
        return result

    # -----------------------------------------------------------
    def generate_targeted_nonce(self, data:Dict[str,Any])->Dict[str,Any]:
        t = self.trajectory_engine.score(
            data.get("courage",0),data.get("dexterity",0),
            data.get("clause_matter",0),data.get("audacity",0))
        meta = {
            "nonce_id": f"HSM-NONCE-{int(time.time())}-{secrets.token_hex(4)}",
            "timestamp": utc_now_iso(),
            "trajectory_score": t,
            "miner_id": self.miner_id,
            "difficulty": self.difficulty
        }
        meta["base_nonce"] = self._calc_base_nonce(data,t)
        meta["nonce_range"] = self._calc_nonce_range(t)
        return meta

    # -----------------------------------------------------------
    def _calc_base_nonce(self,data,t)->int:
        c,d,m,a = [int(t[x]*1000) for x in ("C","D","M","A")]
        combo = (c ^ d) + (m | a)
        if "lat" in data and "lon" in data:
            combo ^= int(abs(data["lat"])*1e6)
            combo += int(abs(data["lon"])*1e6)
        return abs(combo)%1_000_000

    def _calc_nonce_range(self,t)->Tuple[int,int]:
        phase_mult = {
            "Initiation (Courage)":2.0,"Adaptation (Dexterity)":1.5,
            "Verification (Clause Matter)":1.2,"Action (Audacity)":0.8,
            "Equilibrium (Honor)":0.5}.get(t.get("phase",""),1.0)
        return (0,int(1_000_000*phase_mult))

    # -----------------------------------------------------------
    def _get_success_rate(self)->float:
        return 0.0 if self.mined_blocks==0 else min(1.0,self.mined_blocks/(self.mined_blocks+10))

    def _calc_candidate_hash(self,nonce:int,meta:Dict)->str:
        raw=f"{nonce}:{json.dumps(meta,sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _add_block(self, block):
        """Add a validated block to the blockchain safely."""
        try:
            # Compute a hash if it's missing or empty
            if not block.get("block_hash"):
                # Defensive fallback if _calculate_block_hash isn't defined
                try:
                    block["block_hash"] = self._calculate_block_hash(block)
                except Exception:
                    import hashlib, json
                    block["block_hash"] = hashlib.sha256(
                        json.dumps(block, sort_keys=True).encode()
                    ).hexdigest()

            # Append block
            self.chain.append(block)

            # Short print
            short_hash = block.get("block_hash", "NOHASH")[:12]
            print(f"🧱 Block added to {self.network}: {short_hash}")

        except Exception as e:
            import json
            print(f"[!] Failed to add block: {e}")
        print(f"   Block data: {json.dumps(block, indent=2)[:400]}")



    # -----------------------------------------------------------
    def mine_with_hsm_targeting(self,reports:List[Dict[str,Any]],timeout:int=20)->Optional[Dict]:
        if not reports:
            print("⚠️ No threat reports.")
            return None
        prefix="0"*self.difficulty
        best=None; best_score=0.0
        start=time.time()
        for r in reports:
            meta=self.generate_targeted_nonce(r)
            for n in range(*meta["nonce_range"]):
                if time.time()-start>timeout: break
                h=self._calc_candidate_hash(n,meta)
                if h.startswith(prefix):
                    ratio=meta["trajectory_score"]["ratio"]
                    if ratio>best_score:
                        best={"hash":h,"nonce":n,"meta":meta,"score":ratio}
                        best_score=ratio
                    break
        if best:
            reward=self.calculate_mining_reward(best["score"],"HIGH")
            self.mined_blocks+=1; self.total_rewards+=reward
            print(f"✅ Block mined | Score {best['score']:.3f} | Reward {reward:.6f}")
            return best
        print("❌ Timeout - no block found.")
        return None


# ===================================================================
class NWITokenEconomy:
    def __init__(self):
        self.wallets={}; self.tx_history=[]; self.supply=0.0
    def create_wallet(self,owner:str)->str:
        addr=f"WALLET_{hashlib.sha256(owner.encode()).hexdigest()[:16]}"
        self.wallets[addr]={"owner":owner,"balance":0.0}; return addr
    def credit(self,addr:str,amt:float):
        if addr not in self.wallets: self.create_wallet(addr)
        self.wallets[addr]["balance"]+=amt; self.supply+=amt
        self.tx_history.append({"to":addr,"amt":amt,"time":utc_now_iso()})
    def stats(self)->Dict[str,Any]:
        return {"wallets":len(self.wallets),"supply":self.supply,"txs":len(self.tx_history)}


# ===================================================================
def demonstrate_hsm_enhanced_mining():
    miner = HSMEnhancedMiner(difficulty=3, base_reward=0.01)
    econ = NWITokenEconomy()
    wallet = econ.create_wallet(miner.miner_id)

    reports = [
        {"id": "LIVE-1", "lat": 37.22, "lon": -77.40,
         "courage": 0.8, "dexterity": 0.7, "clause_matter": 0.85, "audacity": 0.6},
        {"id": "LIVE-2", "lat": 37.54, "lon": -77.43,
         "courage": 0.7, "dexterity": 0.6, "clause_matter": 0.75, "audacity": 0.5}
    ]

    print("🔧 HSM Miner Initialized:", miner.miner_id)
    iteration = 0
    pmz_vector = 0.0102

    while True:  # continuous mining loop
        iteration += 1
        pmz_vector = (pmz_vector * 1.00037) % 1.0  # PMZ drift / subquantum lineation
        start_nonce = int(time.time() * 1000) % 1000000
        miner.base_reward = 0.01 * (1.0 + pmz_vector)

        block = miner.mine_with_hsm_targeting(reports, timeout=10)
        if block:
            econ.distribute_rewards(wallet, miner.base_reward, block.get("block_hash", "N/A"))
            score = block.get("threat_score", 0.0)
            reward = block.get("reward", miner.base_reward)
            print(f"? Block mined | Score {score:.3f} | Reward {reward:.6f}")
        else:
            print("⏳ No block found this cycle.")

        if iteration % 10 == 0:
            print(f"=== ECONOMY === {{'wallets': {len(econ.wallets)}, 'supply': {econ.token_supply:.3f}, 'txs': {len(econ.transaction_history)}}}")
            print(f"[PMZ] iter={iteration:,}  vector={pmz_vector:.8f}  time={time.strftime('%H:%M:%S')}")

        time.sleep(1)
        
def continuous_mining_loop(miner, threat_reports):
    while True:
        block = miner.mine_with_hsm_targeting(threat_reports, timeout=20)
        if block:
            blockchain._add_block(block)

            # Fix: pull values directly from the miner’s latest block
            block_hash = block.get("block_hash", "NOHASH")
            threat_score = block.get("threat_score", block.get("nonce_metadata", {}).get("trajectory_score", {}).get("ratio", 0.0))
            reward = block.get("reward", miner.base_reward * (1.0 + threat_score * 2.0))

            print(f"[+] Block mined: {block_hash} | Score: {threat_score:.3f} | Reward: {reward:.6f}")

        else:
            print("[-] Timeout, retrying...")

        time.sleep(2)

class NWITokenEconomy:
    def __init__(self):
        self.token_supply = 0.0
        self.wallets = {}
        self.transaction_history = []

    def create_wallet(self, owner_id: str) -> str:
        """Create a new wallet for an entity."""
        wallet_address = f"WALLET_{hashlib.sha256(owner_id.encode()).hexdigest()[:16]}"
        self.wallets[wallet_address] = {
            "owner": owner_id,
            "balance": 0.0,
            "created": datetime.now(timezone.utc).isoformat(),
            "transactions": []
        }
        return wallet_address

    def distribute_rewards(self, miner_wallet: str, amount: float, block_hash: str):
        """Distribute mining rewards to a wallet, record locally, and optionally send to MetaMask."""
    # --- initialize wallet if missing ---
        if miner_wallet not in self.wallets:
            self.wallets[miner_wallet] = {
                "owner": "unknown_miner",
                "balance": 0.0,
                "created": datetime.now(timezone.utc).isoformat(),
                "transactions": []
            }

    # --- credit wallet and supply ---
        self.wallets[miner_wallet]["balance"] += amount
        self.token_supply += amount

    # --- build transaction record ---
        transaction = {
            "tx_id": f"TOKEN-{int(time.time())}",
            "type": "token_reward",
            "from": "network",
            "to": miner_wallet,
            "amount": amount,
            "block_hash": block_hash,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.wallets[miner_wallet]["transactions"].append(transaction)
        self.transaction_history.append(transaction)

    # --- persist locally ---
        self._save_economy()
        print(f"✅ {amount:.6f} HSM tokens rewarded to {miner_wallet}")

    # --- optional on-chain broadcast ---
        metamask_addr = os.getenv("METAMASK_ADDRESS")
        priv_key = os.getenv("PRIVATE_KEY")
        rpc_url = os.getenv("RPC_URL", "https://sepolia.infura.io/v3/YOUR_INFURA_KEY")
        token_address = os.getenv("HSM_TOKEN_CONTRACT")   # optional ERC-20 contract

        if load_web3 and metamask_addr and priv_key and token_address:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if not w3.is_connected():
                    print("⚠️ Web3 connection failed; local record only.")
                    return

                abi_path = os.getenv("HSM_TOKEN_ABI", "hsm_token_abi.json")
                with open(abi_path, "r") as f:
                    token_abi = json.load(f)

                token = w3.eth.contract(address=token_address, abi=token_abi)
                decimals = token.functions.decimals().call()
                wei_amount = int(amount * (10 ** decimals))

                tx = token.functions.transfer(metamask_addr, wei_amount).build_transaction({
                    "from": metamask_addr,
                    "nonce": w3.eth.get_transaction_count(metamask_addr),
                    "gas": 100000,
                    "gasPrice": w3.to_wei("20", "gwei"),
                })

                signed = w3.eth.account.sign_transaction(tx, private_key=priv_key)
                tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
                print(f"🌐 Sent {amount:.6f} HSM to {metamask_addr} on-chain → TX: {tx_hash.hex()}")

            except Exception as e:
                print(f"⚠️ On-chain send failed: {e}")
        else:
            print("💾 Local mode: reward recorded only in economy.json")


def _save_economy(self):
    """Write current economy state to economy.json safely."""
    try:
        data = {
            "token_supply": round(self.token_supply, 6),
            "total_wallets": len(self.wallets),
            "wallets": self.wallets,
            "transaction_history": self.transaction_history
        }
        with open("economy.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[!] Failed to save economy.json: {e}")


def _save_economy(self):
    """Write current economy state to economy.json safely."""
    try:
        data = {
            "token_supply": round(self.token_supply, 6),
            "total_wallets": len(self.wallets),
            "wallets": self.wallets,
            "transaction_history": self.transaction_history
        }
        with open("economy.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[!] Failed to save economy.json: {e}")

    def get_economy_stats(self):
        return {
            "token_supply": self.token_supply,
            "total_wallets": len(self.wallets),
            "total_transactions": len(self.transaction_history)
        }


# ===================================================================
if __name__ == "__main__":
    # Initialize miner and economy
    blockchain = BlockchainNWIEngine(network="nwi_mainnet")
    hsm_miner = HSMEnhancedMiner(difficulty=3, base_reward=0.01)

    econ = NWITokenEconomy()
    wallet = econ.create_wallet(hsm_miner.miner_id)

    # Example threat data
    threat_reports = [
        {"id": "LIVE-1", "lat": 37.22, "lon": -77.40,
         "courage": 0.8, "dexterity": 0.7, "clause_matter": 0.85, "audacity": 0.6},
        {"id": "LIVE-2", "lat": 37.54, "lon": -77.43,
         "courage": 0.7, "dexterity": 0.6, "clause_matter": 0.75, "audacity": 0.5}
    ]

    print(f"Connected to wallet: {wallet}")
    print(f"🔧 HSM Miner Initialized: {hsm_miner.miner_id}")

    # PMZ initialization
    pmz_vector = 0.0102
    iteration = 0
    base_delay = 0.05
    continuous_mining_loop(hsm_miner, threat_reports)

    # Continuous subquantum loop
    while True:
        iteration += 1
        pmz_vector = (pmz_vector * 1.00037) % 1.0  # self-stabilizing PMZ rotation

        # Update difficulty dynamically based on PMZ vector balance
        hsm_miner.difficulty = max(1, int(4 * (1.0 - pmz_vector)))
        start_nonce = int(time.time() * 1000) % 1000000

        # Attempt mining
        block = hsm_miner.mine_with_hsm_targeting(threat_reports, timeout=12)
        if block:
            econ.distribute_rewards(wallet, hsm_miner.base_reward, block.get("block_hash", "N/A"))
            print(f"✅ Block mined | Score {block['threat_score']:.3f} | Reward {hsm_miner.base_reward:.6f}")
        else:
            print("⏳ No block found this cycle.")

        # Every 20 iterations print system state
        if iteration % 20 == 0:
            print(f"=== ECONOMY === {{'wallets': {len(econ.wallets)}, 'supply': {econ.token_supply:.3f}, 'txs': {len(econ.transaction_history)}}}")
            print(f"[PMZ] iter={iteration:,}  vector={pmz_vector:.8f}  difficulty={hsm_miner.difficulty}  time={time.strftime('%H:%M:%S')}")

        time.sleep(base_delay)








