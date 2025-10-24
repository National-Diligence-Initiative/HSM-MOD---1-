#!/usr/bin/env python3
"""
Crypto-Mining Enhanced NWI Defensive Engine
Mines cryptocurrency while processing defensive intelligence reports
"""

import HSM
import hashlib
import time
import json
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import os
import secrets

class NWICryptoMiner:
    def __init__(self, blockchain_engine, difficulty: int = 4, reward: float = 0.001):
        self.blockchain = blockchain_engine
        self.difficulty = difficulty
        self.base_reward = reward
        self.mining_active = False
        self.miner_id = f"NWI-MINER-{secrets.token_hex(8)}"
        self.wallet_address = self._generate_wallet_address()
        self.mined_blocks = 0
        self.total_rewards = 0.0
        
    def _generate_wallet_address(self) -> str:
        """Generate a simulated wallet address"""
        return f"NWI_{hashlib.sha256(self.miner_id.encode()).hexdigest()[:40]}"
    
    def calculate_mining_reward(self, nwi_score: float, threat_level: str) -> float:
        """Calculate mining reward based on NWI report value"""
        base_multiplier = 1.0
        
        # Higher value reports get higher rewards
        if nwi_score >= 0.9:
            base_multiplier = 2.5  # Critical threats
        elif nwi_score >= 0.8:
            base_multiplier = 2.0  # High priority
        elif nwi_score >= 0.7:
            base_multiplier = 1.5  # Medium priority
        elif nwi_score >= 0.6:
            base_multiplier = 1.2  # Low priority
            
        # Threat level adjustments
        threat_multipliers = {
            "CRITICAL": 3.0,
            "HIGH": 2.0,
            "MEDIUM": 1.5,
            "LOW": 1.0
        }
        
        threat_multiplier = threat_multipliers.get(threat_level, 1.0)
        return self.base_reward * base_multiplier * threat_multiplier
    
    def mine_nwi_block(self, transactions: List[Dict], timeout: int = 30) -> Optional[Dict]:
        """Mine a block containing NWI transactions with proof-of-work"""
        
        start_time = time.time()
        last_block = self.blockchain._get_last_block()
        previous_hash = last_block["block_hash"] if last_block else "0" * 64
        
        print(f"⛏️  Mining NWI block with {len(transactions)} transactions...")
        print(f"   Target: {self.difficulty} leading zeros")
        print(f"   Miner: {self.miner_id}")
        
        nonce = 0
        hashes_calculated = 0
        
        while self.mining_active and (time.time() - start_time) < timeout:
            # Create candidate block
            candidate_block = self.blockchain._create_block(previous_hash, transactions, nonce)
            hashes_calculated += 1
            
            # Check if hash meets difficulty requirement
            if candidate_block["block_hash"][:self.difficulty] == "0" * self.difficulty:
                # Calculate rewards for NWI transactions
                total_reward = 0.0
                for tx in transactions:
                    if tx.get("type") == "nwi_report":
                        score = tx["report_data"]["trajectory_score"]["ratio"]
                        threat_level = "HIGH" if score >= 0.8 else "MEDIUM"
                        reward = self.calculate_mining_reward(score, threat_level)
                        total_reward += reward
                
                # Add mining reward transaction
                reward_tx = {
                    "tx_id": f"REWARD-{int(time.time())}",
                    "type": "mining_reward",
                    "timestamp": utc_now_iso(),
                    "miner_id": self.miner_id,
                    "wallet_address": self.wallet_address,
                    "reward_amount": total_reward,
                    "block_hash": candidate_block["block_hash"],
                    "transactions_mined": len([t for t in transactions if t["type"] == "nwi_report"])
                }
                
                candidate_block["transactions"].append(reward_tx)
                candidate_block["mining_data"] = {
                    "miner": self.miner_id,
                    "difficulty": self.difficulty,
                    "hashes_calculated": hashes_calculated,
                    "mining_time": time.time() - start_time,
                    "total_rewards": total_reward
                }
                
                # Recalculate hash with reward transaction
                candidate_block["block_hash"] = self.blockchain._calculate_block_hash(candidate_block)
                
                self.mined_blocks += 1
                self.total_rewards += total_reward
                
                print(f"✅ Block mined successfully!")
                print(f"   Nonce: {nonce}")
                print(f"   Hash: {candidate_block['block_hash']}")
                print(f"   Hashes calculated: {hashes_calculated}")
                print(f"   Mining time: {time.time() - start_time:.2f}s")
                print(f"   Total reward: {total_reward:.6f} NWI")
                
                return candidate_block
            
            nonce += 1
            
            # Progress update every 100,000 hashes
            if hashes_calculated % 100000 == 0:
                print(f"   ...{hashes_calculated} hashes computed...")
        
        print("❌ Mining timeout - no block found")
        return None
    
    def start_continuous_mining(self, transaction_pool, check_interval: int = 10):
        """Start continuous mining process"""
        self.mining_active = True
        
        def mining_loop():
            while self.mining_active:
                if len(transaction_pool) >= 1:  # Mine even with single transaction
                    block = self.mine_nwi_block(transaction_pool.copy(), timeout=60)
                    if block:
                        self.blockchain._add_block(block)
                        transaction_pool.clear()  # Clear mined transactions
                        print(f"💰 Total mined: {self.total_rewards:.6f} NWI")
                
                time.sleep(check_interval)
        
        mining_thread = threading.Thread(target=mining_loop, daemon=True)
        mining_thread.start()
        print(f"🔄 Continuous mining started (checking every {check_interval}s)")
    
    def stop_mining(self):
        """Stop the mining process"""
        self.mining_active = False
        print("🛑 Mining stopped")

class NWITokenEconomy:
    def __init__(self):
        self.token_supply = 0.0
        self.wallets = {}
        self.transaction_history = []
        
    def create_wallet(self, owner_id: str) -> str:
        """Create a new wallet for an entity"""
        wallet_address = f"NWI_WALLET_{hashlib.sha256(owner_id.encode()).hexdigest()[:32]}"
        self.wallets[wallet_address] = {
            "owner": owner_id,
            "balance": 0.0,
            "created": utc_now_iso(),
            "transactions": []
        }
        return wallet_address
    
    def distribute_rewards(self, miner_wallet: str, amount: float, block_hash: str):
        """Distribute mining rewards"""
        if miner_wallet not in self.wallets:
            self.wallets[miner_wallet] = {
                "owner": "unknown_miner",
                "balance": 0.0,
                "created": utc_now_iso(),
                "transactions": []
            }
        
        self.wallets[miner_wallet]["balance"] += amount
        self.token_supply += amount
        
        transaction = {
            "tx_id": f"TOKEN-{int(time.time())}",
            "type": "token_reward",
            "from": "network",
            "to": miner_wallet,
            "amount": amount,
            "block_hash": block_hash,
            "timestamp": utc_now_iso()
        }
        
        self.wallets[miner_wallet]["transactions"].append(transaction)
        self.transaction_history.append(transaction)
        
        print(f"💰 {amount:.6f} NWI tokens rewarded to {miner_wallet}")
    
    def transfer_tokens(self, from_wallet: str, to_wallet: str, amount: float) -> bool:
        """Transfer tokens between wallets"""
        if (from_wallet not in self.wallets or 
            self.wallets[from_wallet]["balance"] < amount):
            return False
        
        self.wallets[from_wallet]["balance"] -= amount
        
        if to_wallet not in self.wallets:
            self.create_wallet(f"recipient_{to_wallet}")
        
        self.wallets[to_wallet]["balance"] += amount
        
        transaction = {
            "tx_id": f"XFER-{int(time.time())}",
            "type": "transfer",
            "from": from_wallet,
            "to": to_wallet,
            "amount": amount,
            "timestamp": utc_now_iso()
        }
        
        self.transaction_history.append(transaction)
        return True
    
    def get_wallet_balance(self, wallet_address: str) -> float:
        """Get wallet balance"""
        return self.wallets.get(wallet_address, {}).get("balance", 0.0)
    
    def get_economy_stats(self) -> Dict[str, Any]:
        """Get token economy statistics"""
        total_wallets = len(self.wallets)
        active_wallets = len([w for w in self.wallets.values() if w["balance"] > 0])
        total_transactions = len(self.transaction_history)
        
        return {
            "token_supply": self.token_supply,
            "total_wallets": total_wallets,
            "active_wallets": active_wallets,
            "total_transactions": total_transactions,
            "average_balance": self.token_supply / active_wallets if active_wallets else 0
        }

def demonstrate_crypto_mining():
    """Demonstrate the cryptocurrency mining integration"""
    
    print("💰 CRYPTO-MINING NWI DEFENSIVE ENGINE")
    print("Mining cryptocurrency while processing threat intelligence\n")
    
    # Import and initialize blockchain
    from blockchain_nwi_engine import BlockchainNWIEngine
    blockchain = BlockchainNWIEngine(network="nwi_mainnet")
    
    # Initialize crypto miner
    miner = NWICryptoMiner(blockchain, difficulty=3, reward=0.01)
    
    # Initialize token economy
    token_economy = NWITokenEconomy()
    token_economy.create_wallet(miner.miner_id)
    
    # Load NWI reports
    try:
        with open('nwi_petersburg_reports.json', 'r') as f:
            reports = json.load(f)
    except FileNotFoundError:
        print("Error: NWI reports not found")
        return
    
    # Process reports and create transactions
    from hs_defensive_engine import TrajectoryMechanic
    tm = TrajectoryMechanic()
    
    transaction_pool = []
    
    print("=== PROCESSING NWI REPORTS FOR MINING ===")
    for report in reports:
        # Calculate trajectory score
        score = tm.score(
            report.get('courage', 0),
            report.get('dexterity', 0),
            report.get('clause_matter', 0),
            report.get('audacity', 0)
        )
        
        # Create blockchain transaction
        transaction = blockchain.create_nwi_transaction(report, score)
        transaction_pool.append(transaction)
        
        threat_level = "HIGH" if score['ratio'] >= 0.8 else "MEDIUM"
        potential_reward = miner.calculate_mining_reward(score['ratio'], threat_level)
        
        print(f"📊 {report['id']}")
        print(f"   Score: {score['ratio']} | Threat: {threat_level}")
        print(f"   Mining Reward Potential: {potential_reward:.6f} NWI")
    
    # Mine the block
    print(f"\n=== MINING BLOCK WITH {len(transaction_pool)} TRANSACTIONS ===")
    mined_block = miner.mine_nwi_block(transaction_pool, timeout=60)
    
    if mined_block:
        # Add to blockchain
        blockchain._add_block(mined_block)
        
        # Distribute token rewards
        reward_tx = next((tx for tx in mined_block["transactions"] 
                         if tx["type"] == "mining_reward"), None)
        
        if reward_tx:
            token_economy.distribute_rewards(
                reward_tx["wallet_address"],
                reward_tx["reward_amount"],
                mined_block["block_hash"]
            )
    
    # Show mining statistics
    print("\n=== MINING STATISTICS ===")
    print(f"   Miner ID: {miner.miner_id}")
    print(f"   Wallet: {miner.wallet_address}")
    print(f"   Blocks Mined: {miner.mined_blocks}")
    print(f"   Total Rewards: {miner.total_rewards:.6f} NWI")
    
    # Show token economy
    print("\n=== TOKEN ECONOMY ===")
    stats = token_economy.get_economy_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.6f}")
        else:
            print(f"   {key}: {value}")
    
    print(f"   Miner Balance: {token_economy.get_wallet_balance(miner.wallet_address):.6f} NWI")

def continuous_mining_demo():
    """Demonstrate continuous mining operation"""
    
    print("\n" + "="*60)
    print("CONTINUOUS MINING DEMONSTRATION")
    print("="*60)
    
    from blockchain_nwi_engine import BlockchainNWIEngine
    blockchain = BlockchainNWIEngine(network="nwi_testnet")
    
    miner = NWICryptoMiner(blockchain, difficulty=2, reward=0.005)
    token_economy = NWITokenEconomy()
    token_economy.create_wallet(miner.miner_id)
    
    transaction_pool = []
    
    # Start continuous mining
    miner.start_continuous_mining(transaction_pool, check_interval=5)
    
    # Simulate incoming NWI reports
    from hs_defensive_engine import TrajectoryMechanic
    tm = TrajectoryMechanic()
    
    sample_reports = [
        {
            "id": "LIVE-NWI-001",
            "text": "Real-time network anomaly detection",
            "meta": {"location": "Petersburg, VA", "confidence": "high"},
            "lat": 37.2279, "lon": -77.4019,
            "courage": 0.8, "dexterity": 0.7, "clause_matter": 0.85, "audacity": 0.6
        },
        {
            "id": "LIVE-NWI-002", 
            "text": "Secondary confirmation of activity",
            "meta": {"location": "Richmond, VA", "confidence": "medium"},
            "lat": 37.5407, "lon": -77.4360,
            "courage": 0.7, "dexterity": 0.6, "clause_matter": 0.75, "audacity": 0.5
        }
    ]
    
    print("\n📡 Simulating real-time NWI report ingestion...")
    
    for i, report in enumerate(sample_reports):
        print(f"\n📨 Incoming Report: {report['id']}")
        score = tm.score(report['courage'], report['dexterity'], 
                        report['clause_matter'], report['audacity'])
        
        transaction = blockchain.create_nwi_transaction(report, score)
        transaction_pool.append(transaction)
        
        print(f"   Added to mining pool (Total: {len(transaction_pool)} transactions)")
        print(f"   Current pool value: {sum(miner.calculate_mining_reward(score['ratio'], 'HIGH') for _ in transaction_pool):.6f} NWI")
        
        time.sleep(8)  # Simulate time between reports
    
    # Let mining continue for a bit
    time.sleep(15)
    
    # Stop mining and show final results
    miner.stop_mining()
    
    print(f"\n=== FINAL MINING RESULTS ===")
    print(f"   Total Blocks Mined: {miner.mined_blocks}")
    print(f"   Total Rewards: {miner.total_rewards:.6f} NWI")
    print(f"   Final Balance: {token_economy.get_wallet_balance(miner.wallet_address):.6f} NWI")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

if __name__ == "__main__":
    demonstrate_crypto_mining()
    continuous_mining_demo()
    
    print("\n" + "="*60)
    print("CRYPTO-MINING NWI BENEFITS")
    print("="*60)
    benefits = [
        "✓ Dual-purpose system: Security + Value creation",
        "✓ Incentivizes threat reporting and analysis",
        "✓ Cryptographic proof of work secures the network",
        "✓ Token economy rewards accurate detection",
        "✓ Self-sustaining defensive ecosystem",
        "✓ Global participation in threat intelligence",
        "✓ Transparent reward distribution",
        "✓ Aligns economic incentives with security goals"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")