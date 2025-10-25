#!/usr/bin/env python3
"""
Lightweight Blockchain Engine for HSM / NWI Miner
Simulates a blockchain ledger for testing and development.
"""

import hashlib
import json
import time
from datetime import datetime, timezone


class BlockchainNWIEngine:
    def __init__(self, network="nwi_testnet"):
        self.network = network
        self.chain = []
        self.transaction_pool = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """Initialize blockchain with the genesis block"""
        genesis_block = {
            "index": 0,
            "timestamp": self.utc_now_iso(),
            "transactions": [],
            "previous_hash": "0" * 64,
            "nonce": 0,
            "block_hash": "GENESIS"
        }
        self.chain.append(genesis_block)

    def utc_now_iso(self):
        return datetime.now(timezone.utc).isoformat()

    def _calculate_block_hash(self, block):
        """Calculate SHA256 hash of a block"""
        block_str = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_str).hexdigest()

    def _get_last_block(self):
        """Return the last block in the chain"""
        return self.chain[-1] if self.chain else None

    def _create_block(self, previous_hash, transactions, nonce):
        """Create a new candidate block"""
        block = {
            "index": len(self.chain),
            "timestamp": self.utc_now_iso(),
            "transactions": transactions,
            "previous_hash": previous_hash,
            "nonce": nonce
        }
        block["block_hash"] = self._calculate_block_hash(block)
        return block

    def _add_block(self, block):
        """Add a validated block to the blockchain"""
        self.chain.append(block)
        print(f"🧱 Block added to {self.network}: {block['block_hash'][:12]}")

    def create_nwi_transaction(self, report, trajectory_score):
        """Simulate creation of a network intelligence transaction"""
        tx = {
            "tx_id": f"TX-{int(time.time())}",
            "type": "nwi_report",
            "timestamp": self.utc_now_iso(),
            "report_data": report,
            "trajectory_score": trajectory_score
        }
        return tx
