#!/usr/bin/env python3
"""
Crypto-Mining Enhanced NWI Defensive Engine
HSM-Enhanced Crypto Mining Engine
Simulated version: all logic preserved, syntax fixed.
"""

import hashlib, time, json, threading, os, secrets, sys
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
load_dotenv()

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
        print(f"🔧 HSM Miner Initialized: {self.miner_id}")

    # -----------------------------------------------------------
    def calculate_mining_reward(self, score:float, threat_level:str)->float:
        base_mult = 1.0
        if score >= .9: base_mult=2.5
        elif score >= .8: base_mult=2.0
        elif score >= .7: base_mult=1.5
        elif score >= .6: base_mult=1.2
        threat_mult = {"CRITICAL":3,"HIGH":2,"MEDIUM":1.5,"LOW":1}.get(threat_level,1)
        return self.base_reward * base_mult * threat_mult

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
    miner=HSMEnhancedMiner(difficulty=3,base_reward=0.01)
    econ=NWITokenEconomy(); wallet=econ.create_wallet(miner.miner_id)

    reports=[
        {"id":"LIVE-1","lat":37.22,"lon":-77.40,"courage":0.8,"dexterity":0.7,"clause_matter":0.85,"audacity":0.6},
        {"id":"LIVE-2","lat":37.54,"lon":-77.43,"courage":0.7,"dexterity":0.6,"clause_matter":0.75,"audacity":0.5}
    ]

    block=miner.mine_with_hsm_targeting(reports)
    if block:
        econ.credit(wallet,miner.total_rewards)
        print(f"Wallet {wallet} credited {miner.total_rewards:.6f}")
    print("=== ECONOMY ===",econ.stats())


# ===================================================================
if __name__=="__main__":
    demonstrate_hsm_enhanced_mining()
