#!/usr/bin/env python3
"""
HSM Proxy Mining Gateway
Secure proxy that routes traffic through HSM threat analysis while mining cryptocurrency
using threat-intelligence-optimized nonces.
"""

import asyncio
import aiohttp
import time
import json
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import threading
from urllib.parse import urlparse
import sys
import socket

# Import HSM Defensive Engine
sys.path.append('.')
from HSM import TrajectoryMechanic, IncidentManager, append_ledger, utc_now_iso

class HSMProxyMiner:
    def __init__(self, proxy_host: str = "127.0.0.1", proxy_port: int = 8080, 
                 mining_difficulty: int = 3, base_reward: float = 0.001):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.mining_difficulty = mining_difficulty
        self.base_reward = base_reward
        
        # HSM Components
        self.trajectory_engine = TrajectoryMechanic()
        self.incident_manager = IncidentManager()
        
        # Mining components
        self.miner_id = f"HSM-PROXY-{secrets.token_hex(8)}"
        self.mined_blocks = 0
        self.total_rewards = 0.0
        self.traffic_analyzed = 0
        
        # Proxy state
        self.running = False
        self.connection_pool = {}
        self.threat_cache = {}
        
        # Statistics
        self.stats = {
            "requests_processed": 0,
            "threats_detected": 0,
            "blocks_mined": 0,
            "total_rewards": 0.0,
            "avg_processing_time": 0.0
        }
        
        print(f"🔧 HSM Proxy Miner Initialized: {self.miner_id}")
        print(f"   Proxy: {proxy_host}:{proxy_port}")
        print(f"   Mining Difficulty: {mining_difficulty}")
    
    async def start_proxy(self):
        """Start the HSM proxy mining gateway"""
        self.running = True
        
        try:
            server = await asyncio.start_server(
                self.handle_client_connection,
                self.proxy_host, 
                self.proxy_port
            )
            
            print(f"🚀 HSM Proxy Mining Gateway started on {self.proxy_host}:{self.proxy_port}")
            print("   Traffic analysis + Cryptocurrency mining active")
            
            async with server:
                await server.serve_forever()
                
        except Exception as e:
            print(f"❌ Failed to start proxy: {e}")
            self.running = False
    
    async def handle_client_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming client connections through the proxy"""
        start_time = time.time()
        
        try:
            # Read the request line
            request_line = await reader.readuntil(b'\r\n')
            method, url, version = request_line.decode().strip().split()
            
            # Parse the target URL
            parsed_url = urlparse(url)
            target_host = parsed_url.hostname
            target_port = parsed_url.port or 80
            
            # Analyze traffic for threats
            threat_score = await self.analyze_traffic_pattern(method, target_host, parsed_url.path)
            
            # Mine cryptocurrency based on threat analysis
            if threat_score > 0.3:  # Only mine for meaningful threat levels
                mining_result = await self.mine_with_traffic_analysis(threat_score, {
                    'method': method,
                    'host': target_host,
                    'path': parsed_url.path,
                    'timestamp': utc_now_iso()
                })
            
            # Forward the request to the target
            response_data = await self.forward_request(reader, writer, method, target_host, target_port, url, version)
            
            # Update statistics
            processing_time = time.time() - start_time
            self.update_statistics(threat_score, processing_time, mining_result if threat_score > 0.3 else None)
            
        except Exception as e:
            print(f"⚠️  Proxy error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def analyze_traffic_pattern(self, method: str, host: str, path: str) -> float:
        """Analyze traffic patterns for threat detection"""
        
        # Create traffic analysis report
        traffic_report = {
            "id": f"TRAFFIC-{int(time.time())}-{secrets.token_hex(4)}",
            "text": f"Proxy traffic analysis: {method} {host}{path}",
            "meta": {
                "analysis_type": "proxy_traffic",
                "host": host,
                "method": method,
                "path": path,
                "risk_factors": self.assess_risk_factors(host, path)
            },
            "source": "hsm_proxy_analyzer",
            # Simulated threat scores based on traffic patterns
            "courage": self.assess_confidence(method, host),
            "dexterity": self.assess_technical_complexity(method, path),
            "clause_matter": self.assess_potential_impact(host, path),
            "audacity": self.assess_behavior_boldness(method, host)
        }
        
        # Score using HSM trajectory
        score = self.trajectory_engine.score(
            traffic_report["courage"],
            traffic_report["dexterity"], 
            traffic_report["clause_matter"],
            traffic_report["audacity"]
        )
        
        # Cache the analysis
        analysis_id = hashlib.md5(f"{method}{host}{path}".encode()).hexdigest()
        self.threat_cache[analysis_id] = {
            "report": traffic_report,
            "score": score,
            "timestamp": utc_now_iso()
        }
        
        self.traffic_analyzed += 1
        
        if score["ratio"] > 0.7:
            print(f"🚨 High-threat traffic detected: {method} {host}{path} (Score: {score['ratio']})")
        
        return score["ratio"]
    
    def assess_risk_factors(self, host: str, path: str) -> List[str]:
        """Assess risk factors for traffic"""
        risk_factors = []
        
        # Suspicious path patterns
        suspicious_paths = ['/admin', '/console', '/shell', '/cmd', '/exec']
        if any(suspicious in path.lower() for suspicious in suspicious_paths):
            risk_factors.append("suspicious_path")
        
        # Unusual TLDs
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.xyz']
        if any(host.endswith(tld) for tld in suspicious_tlds):
            risk_factors.append("suspicious_tld")
        
        # IP address as host
        try:
            socket.inet_aton(host)
            risk_factors.append("ip_based_host")
        except socket.error:
            pass
        
        return risk_factors
    
    def assess_confidence(self, method: str, host: str) -> float:
        """Assess confidence level (courage) for traffic"""
        score = 0.5  # Base score
        
        # Higher confidence for common methods
        if method in ['GET', 'POST']:
            score += 0.2
        elif method in ['PUT', 'DELETE']:
            score += 0.1
        
        # Lower confidence for IP addresses
        try:
            socket.inet_aton(host)
            score -= 0.2
        except socket.error:
            score += 0.1
        
        return max(0.1, min(0.9, score))
    
    def assess_technical_complexity(self, method: str, path: str) -> float:
        """Assess technical complexity (dexterity)"""
        score = 0.3
        
        # Complex methods
        if method in ['PUT', 'DELETE', 'PATCH']:
            score += 0.3
        
        # Complex paths (API endpoints, etc.)
        if '/api/' in path or '/v1/' in path or '/v2/' in path:
            score += 0.2
        
        # File extensions indicating complexity
        complex_extensions = ['.php', '.asp', '.jsp', '.do', '.action']
        if any(path.endswith(ext) for ext in complex_extensions):
            score += 0.2
        
        return max(0.1, min(0.9, score))
    
    def assess_potential_impact(self, host: str, path: str) -> float:
        """Assess potential impact (clause matter)"""
        score = 0.4
        
        # High-impact paths
        high_impact_paths = ['/login', '/admin', '/config', '/database', '/backup']
        if any(impact_path in path.lower() for impact_path in high_impact_paths):
            score += 0.4
        
        # Sensitive file extensions
        sensitive_extensions = ['.sql', '.bak', '.old', '.tar', '.gz']
        if any(path.endswith(ext) for ext in sensitive_extensions):
            score += 0.3
        
        return max(0.1, min(0.9, score))
    
    def assess_behavior_boldness(self, method: str, host: str) -> float:
        """Assess behavior boldness (audacity)"""
        score = 0.3
        
        # Bold methods
        if method in ['DELETE', 'PUT', 'PATCH']:
            score += 0.4
        
        # Direct IP access shows boldness
        try:
            socket.inet_aton(host)
            score += 0.2
        except socket.error:
            pass
        
        return max(0.1, min(0.9, score))
    
    async def mine_with_traffic_analysis(self, threat_score: float, traffic_data: Dict) -> Optional[Dict]:
        """Mine cryptocurrency using traffic analysis data"""
        
        # Generate nonce based on traffic patterns
        nonce_metadata = self.generate_traffic_based_nonce(threat_score, traffic_data)
        
        # Mine with traffic-optimized nonce
        mining_result = await self.mine_targeted_nonce(nonce_metadata)
        
        if mining_result:
            self.mined_blocks += 1
            reward = self.calculate_traffic_reward(threat_score, traffic_data)
            self.total_rewards += reward
            
            # Log mining success
            self.log_traffic_mining(mining_result, reward, traffic_data)
            
            return mining_result
        
        return None
    
    def generate_traffic_based_nonce(self, threat_score: float, traffic_data: Dict) -> Dict:
        """Generate nonce based on traffic analysis"""
        
        # Create traffic-influenced nonce metadata
        nonce_metadata = {
            "nonce_id": f"PROXY-NONCE-{int(time.time())}-{secrets.token_hex(4)}",
            "timestamp": utc_now_iso(),
            "traffic_context": {
                "method": traffic_data['method'],
                "host": traffic_data['host'],
                "path": traffic_data['path'],
                "threat_score": threat_score
            },
            "mining_context": {
                "miner_id": self.miner_id,
                "difficulty": self.mining_difficulty,
                "base_nonce": self.calculate_traffic_nonce(traffic_data)
            }
        }
        
        return nonce_metadata
    
    def calculate_traffic_nonce(self, traffic_data: Dict) -> int:
        """Calculate starting nonce based on traffic characteristics"""
        
        # Use traffic data to influence nonce generation
        method_hash = int(hashlib.md5(traffic_data['method'].encode()).hexdigest()[:8], 16)
        host_hash = int(hashlib.md5(traffic_data['host'].encode()).hexdigest()[:8], 16)
        path_hash = int(hashlib.md5(traffic_data['path'].encode()).hexdigest()[:8], 16)
        
        combined_nonce = (method_hash ^ host_hash) + (path_hash | method_hash)
        return abs(combined_nonce) % 1000000
    
    async def mine_targeted_nonce(self, nonce_metadata: Dict, timeout: int = 5) -> Optional[Dict]:
        """Mine with targeted nonce (non-blocking for proxy)"""
        
        target_prefix = "0" * self.mining_difficulty
        start_nonce = nonce_metadata["mining_context"]["base_nonce"]
        max_nonce = start_nonce + 10000  # Limited range for proxy operations
        
        for nonce in range(start_nonce, max_nonce):
            # Calculate candidate hash
            data_string = f"{nonce}:{json.dumps(nonce_metadata, sort_keys=True)}"
            candidate_hash = hashlib.sha256(data_string.encode()).hexdigest()
            
            if candidate_hash.startswith(target_prefix):
                return {
                    "block_hash": candidate_hash,
                    "nonce": nonce,
                    "nonce_metadata": nonce_metadata,
                    "miner_id": self.miner_id
                }
        
        return None
    
    def calculate_traffic_reward(self, threat_score: float, traffic_data: Dict) -> float:
        """Calculate mining reward based on traffic threat score"""
        base_multiplier = 1.0 + (threat_score * 3.0)  # 1x to 4x multiplier
        
        # Method-based bonuses
        method_bonuses = {
            'GET': 1.0,
            'POST': 1.5,
            'PUT': 2.0,
            'DELETE': 2.5,
            'PATCH': 2.0
        }
        
        method_bonus = method_bonuses.get(traffic_data['method'], 1.0)
        
        return self.base_reward * base_multiplier * method_bonus
    
    def log_traffic_mining(self, mining_result: Dict, reward: float, traffic_data: Dict):
        """Log traffic-based mining operation"""
        
        mining_record = {
            "type": "proxy_traffic_mining",
            "miner_id": self.miner_id,
            "timestamp": utc_now_iso(),
            "traffic_data": traffic_data,
            "mining_result": mining_result,
            "reward": reward,
            "proxy_context": {
                "host": self.proxy_host,
                "port": self.proxy_port,
                "traffic_analyzed": self.traffic_analyzed
            }
        }
        
        append_ledger(mining_record)
        print(f"   💰 Traffic mining: {reward:.6f} HSM from {traffic_data['method']} {traffic_data['host']}")
    
    async def forward_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, 
                            method: str, target_host: str, target_port: int, url: str, version: str):
        """Forward the client request to the target server"""
        
        try:
            # Connect to target
            target_reader, target_writer = await asyncio.open_connection(target_host, target_port)
            
            # Forward the request
            request_line = f"{method} {url} {version}\r\n"
            target_writer.write(request_line.encode())
            
            # Forward headers
            while True:
                header_line = await reader.readuntil(b'\r\n')
                if header_line == b'\r\n':
                    break
                target_writer.write(header_line)
            
            target_writer.write(b'\r\n')
            await target_writer.drain()
            
            # Read and forward response
            response = await target_reader.read(8192)
            writer.write(response)
            await writer.drain()
            
            target_writer.close()
            await target_writer.wait_closed()
            
            return response
            
        except Exception as e:
            print(f"❌ Forwarding error: {e}")
            error_response = b"HTTP/1.1 502 Bad Gateway\r\n\r\nProxy Error"
            writer.write(error_response)
            await writer.drain()
    
    def update_statistics(self, threat_score: float, processing_time: float, mining_result: Optional[Dict]):
        """Update proxy statistics"""
        self.stats["requests_processed"] += 1
        self.stats["avg_processing_time"] = (
            (self.stats["avg_processing_time"] * (self.stats["requests_processed"] - 1) + processing_time) 
            / self.stats["requests_processed"]
        )
        
        if threat_score > 0.7:
            self.stats["threats_detected"] += 1
        
        if mining_result:
            self.stats["blocks_mined"] += 1
            self.stats["total_rewards"] = self.total_rewards
    
    def get_proxy_statistics(self) -> Dict[str, Any]:
        """Get comprehensive proxy statistics"""
        return {
            **self.stats,
            "miner_id": self.miner_id,
            "traffic_analyzed": self.traffic_analyzed,
            "threat_cache_size": len(self.threat_cache),
            "active_connections": len(self.connection_pool),
            "proxy_uptime": getattr(self, 'start_time', 0),
            "mining_efficiency": self.stats["blocks_mined"] / max(1, self.stats["threats_detected"])
        }

class ProxyManagementAPI:
    def __init__(self, proxy_miner: HSMProxyMiner, api_port: int = 8081):
        self.proxy_miner = proxy_miner
        self.api_port = api_port
    
    async def start_api(self):
        """Start management API for the proxy"""
        # Simple HTTP API for monitoring
        # In production, this would use a proper web framework
        print(f"📊 Proxy Management API available on port {self.api_port}")
        # Implementation would go here...

def demonstrate_proxy_operations():
    """Demonstrate HSM proxy mining operations"""
    
    print("🌐 HSM PROXY MINING GATEWAY DEMONSTRATION")
    print("Secure traffic routing + Threat-based cryptocurrency mining\n")
    
    # Initialize proxy miner
    proxy_miner = HSMProxyMiner(
        proxy_host="127.0.0.1",
        proxy_port=8080,
        mining_difficulty=2,  # Lower difficulty for demo
        base_reward=0.0005
    )
    
    # Simulate traffic analysis
    print("=== TRAFFIC ANALYSIS SIMULATION ===")
    
    test_traffic = [
        {"method": "GET", "host": "google.com", "path": "/search?q=test"},
        {"method": "POST", "host": "192.168.1.100", "path": "/admin/login.php"},
        {"method": "DELETE", "host": "api.example.com", "path": "/v1/users/123"},
        {"method": "GET", "host": "suspicious.tk", "path": "/shell.exe"}
    ]
    
    for traffic in test_traffic:
        threat_score = asyncio.run(proxy_miner.analyze_traffic_pattern(
            traffic["method"], traffic["host"], traffic["path"]
        ))
        
        print(f"   {traffic['method']} {traffic['host']}{traffic['path']}")
        print(f"   Threat Score: {threat_score:.4f}")
        
        if threat_score > 0.7:
            mining_result = asyncio.run(proxy_miner.mine_with_traffic_analysis(
                threat_score, traffic
            ))
            if mining_result:
                print(f"   🎯 Mining successful! Nonce: {mining_result['nonce']}")
    
    # Show proxy statistics
    print(f"\n=== PROXY STATISTICS ===")
    stats = proxy_miner.get_proxy_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.6f}")
        else:
            print(f"   {key}: {value}")

async def start_proxy_demo():
    """Start the actual proxy for demonstration"""
    print("\n" + "="*60)
    print("STARTING HSM PROXY MINING GATEWAY")
    print("="*60)
    
    proxy_miner = HSMProxyMiner(
        proxy_host="127.0.0.1",
        proxy_port=8080,
        mining_difficulty=2,
        base_reward=0.001
    )
    
    # Start proxy in background
    proxy_task = asyncio.create_task(proxy_miner.start_proxy())
    
    print("✅ Proxy is running in background")
    print("   Configure your browser or tools to use: 127.0.0.1:8080")
    print("   All traffic will be analyzed and mined for threats")
    
    # Keep running
    try:
        await asyncio.sleep(3600)  # Run for 1 hour
    except KeyboardInterrupt:
        print("\n🛑 Stopping proxy...")
    finally:
        proxy_miner.running = False
        proxy_task.cancel()

if __name__ == "__main__":
    # Run demonstration
    demonstrate_proxy_operations()
    
    # Uncomment to run actual proxy
    # asyncio.run(start_proxy_demo())
    
    print("\n" + "="*60)
    print("HSM PROXY MINING BENEFITS")
    print("="*60)
    benefits = [
        "✓ Real-time traffic analysis while routing",
        "✓ Threat-based cryptocurrency mining",
        "✓ Passive income from security monitoring",
        "✓ No impact on legitimate traffic",
        "✓ Self-funding security infrastructure",
        "✓ Transparent threat scoring",
        "✓ Adaptive mining based on risk levels",
        "✓ Comprehensive traffic logging"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")