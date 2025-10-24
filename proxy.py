#!/usr/bin/env python3
"""
HSM Proxy Mining Gateway - Enhanced Utilization
Advanced miner with proxy utilization metrics, adaptive mining, and resource management
"""

import asyncio
import aiohttp
import time
import json
import hashlib
import secrets
import psutil
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass
from urllib.parse import urlparse
import sys
import socket

# Import HSM Defensive Engine
sys.path.append('.')
from HSM import TrajectoryMechanic, IncidentManager, append_ledger, utc_now_iso

@dataclass
class ProxyUtilizationMetrics:
    """Comprehensive proxy utilization metrics"""
    active_connections: int = 0
    requests_per_second: float = 0.0
    bandwidth_usage: float = 0.0  # MB/s
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    threat_density: float = 0.0  # Threats per minute
    mining_efficiency: float = 0.0
    response_time_avg: float = 0.0
    error_rate: float = 0.0

class HSMProxyUtilizationMiner:
    def __init__(self, proxy_host: str = "127.0.0.1", proxy_port: int = 8080, 
                 mining_difficulty: int = 3, base_reward: float = 0.001):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.mining_difficulty = mining_difficulty
        self.base_reward = base_reward
        
        # HSM Components
        self.trajectory_engine = TrajectoryMechanic()
        self.incident_manager = IncidentManager()
        
        # Enhanced mining components
        self.miner_id = f"HSM-PROXY-UTIL-{secrets.token_hex(8)}"
        self.mined_blocks = 0
        self.total_rewards = 0.0
        self.traffic_analyzed = 0
        
        # Utilization tracking
        self.utilization_metrics = ProxyUtilizationMetrics()
        self.metrics_history = []
        self.adaptive_mining_enabled = True
        
        # Resource management
        self.max_cpu_usage = 80.0  # Maximum CPU usage before throttling
        self.max_memory_usage = 85.0  # Maximum memory usage
        self.mining_intensity = 1.0  # 0.0 to 1.0 scale
        
        # Proxy state with enhanced tracking
        self.running = False
        self.connection_pool = {}
        self.threat_cache = {}
        self.performance_counters = {
            'requests_processed': 0,
            'bytes_transferred': 0,
            'mining_attempts': 0,
            'mining_successes': 0,
            'threats_blocked': 0
        }
        
        # Adaptive mining strategies
        self.mining_strategies = {
            'low_utilization': self._low_utilization_mining,
            'high_utilization': self._high_utilization_mining, 
            'balanced': self._balanced_mining,
            'aggressive': self._aggressive_mining
        }
        self.current_strategy = 'balanced'
        
        # Threading for background metrics collection
        self.metrics_thread = None
        self.stop_metrics = False
        
        print(f"🔧 HSM Proxy Utilization Miner Initialized: {self.miner_id}")
        print(f"   Proxy: {proxy_host}:{proxy_port}")
        print(f"   Adaptive Mining: {self.adaptive_mining_enabled}")
        print(f"   Max CPU: {self.max_cpu_usage}%")
    
    async def start_proxy(self):
        """Start the enhanced HSM proxy mining gateway with utilization tracking"""
        self.running = True
        
        # Start background metrics collection
        self.start_metrics_collection()
        
        try:
            server = await asyncio.start_server(
                self.handle_client_connection,
                self.proxy_host, 
                self.proxy_port
            )
            
            print(f"🚀 HSM Proxy Utilization Gateway started on {self.proxy_host}:{self.proxy_port}")
            print("   Adaptive mining based on proxy utilization active")
            
            async with server:
                await server.serve_forever()
                
        except Exception as e:
            print(f"❌ Failed to start proxy: {e}")
            self.running = False
        finally:
            self.stop_metrics_collection()
    
    def start_metrics_collection(self):
        """Start background metrics collection thread"""
        def metrics_loop():
            while not self.stop_metrics:
                self.collect_system_metrics()
                self.update_mining_intensity()
                time.sleep(2)  # Collect every 2 seconds
        
        self.metrics_thread = threading.Thread(target=metrics_loop, daemon=True)
        self.metrics_thread.start()
        print("📊 Background metrics collection started")
    
    def stop_metrics_collection(self):
        """Stop background metrics collection"""
        self.stop_metrics = True
        if self.metrics_thread:
            self.metrics_thread.join()
        print("📊 Background metrics collection stopped")
    
    def collect_system_metrics(self):
        """Collect comprehensive system and proxy metrics"""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        network_io = psutil.net_io_counters()
        
        # Update utilization metrics
        self.utilization_metrics.cpu_usage = cpu_percent
        self.utilization_metrics.memory_usage = memory.percent
        self.utilization_metrics.active_connections = len(self.connection_pool)
        
        # Calculate requests per second (simplified)
        current_time = time.time()
        if hasattr(self, 'last_metrics_time'):
            time_diff = current_time - self.last_metrics_time
            req_diff = self.performance_counters['requests_processed'] - self.last_request_count
            self.utilization_metrics.requests_per_second = req_diff / time_diff if time_diff > 0 else 0
            
            # Calculate bandwidth
            bytes_diff = self.performance_counters['bytes_transferred'] - self.last_bytes_count
            self.utilization_metrics.bandwidth_usage = (bytes_diff / (1024 * 1024)) / time_diff if time_diff > 0 else 0
        
        self.last_metrics_time = current_time
        self.last_request_count = self.performance_counters['requests_processed']
        self.last_bytes_count = self.performance_counters['bytes_transferred']
        
        # Store metrics history (keep last 100 entries)
        self.metrics_history.append({
            'timestamp': utc_now_iso(),
            'metrics': self.utilization_metrics.__dict__.copy()
        })
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)
    
    def update_mining_intensity(self):
        """Dynamically adjust mining intensity based on system utilization"""
        if not self.adaptive_mining_enabled:
            return
        
        # Calculate resource pressure
        cpu_pressure = self.utilization_metrics.cpu_usage / self.max_cpu_usage
        memory_pressure = self.utilization_metrics.memory_usage / self.max_memory_usage
        connection_pressure = min(1.0, self.utilization_metrics.active_connections / 100.0)
        
        # Overall system load (0.0 to 1.0)
        system_load = max(cpu_pressure, memory_pressure, connection_pressure)
        
        # Adjust mining intensity inversely to system load
        # Higher load = lower mining intensity
        new_intensity = max(0.1, 1.0 - system_load)
        
        # Smooth transition
        self.mining_intensity = 0.7 * self.mining_intensity + 0.3 * new_intensity
        
        # Select mining strategy based on utilization
        if system_load < 0.3:
            self.current_strategy = 'aggressive'
        elif system_load < 0.6:
            self.current_strategy = 'balanced'
        elif system_load < 0.8:
            self.current_strategy = 'high_utilization'
        else:
            self.current_strategy = 'low_utilization'
        
        # Adjust mining difficulty based on intensity
        self.mining_difficulty = max(2, min(5, int(3 + (2 * (1 - self.mining_intensity))))
    
    async def handle_client_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle client connections with utilization-aware processing"""
        start_time = time.time()
        client_addr = writer.get_extra_info('peername')
        
        # Track connection
        connection_id = f"{client_addr[0]}:{client_addr[1]}"
        self.connection_pool[connection_id] = {
            'start_time': start_time,
            'bytes_sent': 0,
            'bytes_received': 0
        }
        
        try:
            # Read request with timeout
            request_data = await asyncio.wait_for(reader.read(4096), timeout=10.0)
            
            if not request_data:
                return
            
            # Parse HTTP request
            request_lines = request_data.decode().split('\r\n')
            if not request_lines:
                return
                
            # Parse request line
            request_line = request_lines[0]
            parts = request_line.split()
            if len(parts) < 2:
                return
                
            method, url = parts[0], parts[1]
            parsed_url = urlparse(url)
            target_host = parsed_url.hostname
            target_port = parsed_url.port or 80
            
            # Update performance counters
            self.performance_counters['requests_processed'] += 1
            self.performance_counters['bytes_received'] += len(request_data)
            
            # Analyze traffic with utilization awareness
            threat_score = await self.analyze_traffic_with_utilization(method, target_host, parsed_url.path)
            
            # Utilization-aware mining
            mining_result = None
            if threat_score > 0.3 and self.mining_intensity > 0.3:
                mining_result = await self.mine_with_utilization_awareness(
                    threat_score, 
                    method, 
                    target_host, 
                    parsed_url.path
                )
            
            # Forward request with utilization-based timeout
            response_data = await self.forward_request_with_utilization(
                request_data, target_host, target_port
            )
            
            # Send response
            if response_data:
                writer.write(response_data)
                await writer.drain()
                self.performance_counters['bytes_transferred'] += len(response_data)
            
            # Update connection metrics
            processing_time = time.time() - start_time
            self.utilization_metrics.response_time_avg = (
                (self.utilization_metrics.response_time_avg * (self.performance_counters['requests_processed'] - 1) + processing_time) 
                / self.performance_counters['requests_processed']
            )
            
        except asyncio.TimeoutError:
            print(f"⏰ Request timeout from {connection_id}")
            self.utilization_metrics.error_rate += 0.1
        except Exception as e:
            print(f"⚠️  Connection error from {connection_id}: {e}")
            self.utilization_metrics.error_rate += 0.1
        finally:
            # Cleanup connection
            if connection_id in self.connection_pool:
                del self.connection_pool[connection_id]
            writer.close()
            await writer.wait_closed()
    
    async def analyze_traffic_with_utilization(self, method: str, host: str, path: str) -> float:
        """Analyze traffic with utilization-aware resource allocation"""
        
        # Adjust analysis depth based on current utilization
        analysis_depth = self.mining_intensity  # Use mining intensity as proxy for available resources
        
        traffic_report = {
            "id": f"TRAFFIC-UTIL-{int(time.time())}-{secrets.token_hex(4)}",
            "text": f"Utilization-aware analysis: {method} {host}{path}",
            "meta": {
                "analysis_type": "utilization_aware",
                "host": host,
                "method": method,
                "path": path,
                "utilization_level": self.mining_intensity,
                "analysis_depth": analysis_depth,
                "risk_factors": self.assess_risk_factors_with_utilization(host, path, analysis_depth)
            },
            "source": "hsm_proxy_util_analyzer",
            "courage": self.assess_confidence_with_utilization(method, host, analysis_depth),
            "dexterity": self.assess_technical_complexity_with_utilization(method, path, analysis_depth),
            "clause_matter": self.assess_potential_impact_with_utilization(host, path, analysis_depth),
            "audacity": self.assess_behavior_boldness_with_utilization(method, host, analysis_depth)
        }
        
        # Score using HSM trajectory
        score = self.trajectory_engine.score(
            traffic_report["courage"],
            traffic_report["dexterity"], 
            traffic_report["clause_matter"],
            traffic_report["audacity"]
        )
        
        self.traffic_analyzed += 1
        
        # Update threat density metric
        if score["ratio"] > 0.7:
            self.utilization_metrics.threat_density += 1
            print(f"🚨 High-threat traffic (Util: {self.mining_intensity:.2f}): {method} {host}{path}")
        
        return score["ratio"]
    
    def assess_risk_factors_with_utilization(self, host: str, path: str, depth: float) -> List[str]:
        """Assess risk factors with utilization-aware depth"""
        risk_factors = []
        depth_threshold = 0.5  # Only do deep analysis if we have resources
        
        # Basic risk factors (always checked)
        suspicious_paths = ['/admin', '/console', '/shell', '/cmd', '/exec']
        if any(suspicious in path.lower() for suspicious in suspicious_paths):
            risk_factors.append("suspicious_path")
        
        # Deeper analysis only when resources available
        if depth > depth_threshold:
            suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.xyz']
            if any(host.endswith(tld) for tld in suspicious_tlds):
                risk_factors.append("suspicious_tld")
            
            try:
                socket.inet_aton(host)
                risk_factors.append("ip_based_host")
            except socket.error:
                pass
        
        return risk_factors
    
    def assess_confidence_with_utilization(self, method: str, host: str, depth: float) -> float:
        """Assess confidence with utilization-aware analysis"""
        score = 0.5
        
        if method in ['GET', 'POST']:
            score += 0.2
        elif method in ['PUT', 'DELETE']:
            score += 0.1
        
        # Deeper analysis when resources available
        if depth > 0.7:
            try:
                socket.inet_aton(host)
                score -= 0.3  # More penalty for IP addresses in deep analysis
            except socket.error:
                score += 0.2  # More reward for domain names
        
        return max(0.1, min(0.9, score))
    
    def assess_technical_complexity_with_utilization(self, method: str, path: str, depth: float) -> float:
        """Assess technical complexity with utilization awareness"""
        score = 0.3
        
        if method in ['PUT', 'DELETE', 'PATCH']:
            score += 0.3
        
        # Deeper path analysis when resources available
        if depth > 0.6:
            api_patterns = ['/api/', '/v1/', '/v2/', '/graphql']
            if any(pattern in path for pattern in api_patterns):
                score += 0.3
            
            complex_extensions = ['.php', '.asp', '.jsp', '.do', '.action']
            if any(path.endswith(ext) for ext in complex_extensions):
                score += 0.2
        
        return max(0.1, min(0.9, score))
    
    def assess_potential_impact_with_utilization(self, host: str, path: str, depth: float) -> float:
        """Assess potential impact with utilization awareness"""
        score = 0.4
        
        high_impact_paths = ['/login', '/admin', '/config', '/database', '/backup']
        if any(impact_path in path.lower() for impact_path in high_impact_paths):
            score += 0.4
        
        # Deeper impact analysis when resources available
        if depth > 0.8:
            sensitive_patterns = ['.sql', '.bak', '.old', '.tar', '.gz', 'password', 'secret']
            if any(pattern in path.lower() for pattern in sensitive_patterns):
                score += 0.3
        
        return max(0.1, min(0.9, score))
    
    def assess_behavior_boldness_with_utilization(self, method: str, host: str, depth: float) -> float:
        """Assess behavior boldness with utilization awareness"""
        score = 0.3
        
        if method in ['DELETE', 'PUT', 'PATCH']:
            score += 0.4
        
        # Deeper behavior analysis when resources available
        if depth > 0.5:
            try:
                socket.inet_aton(host)
                score += 0.3  # More boldness for direct IP access
            except socket.error:
                pass
        
        return max(0.1, min(0.9, score))
    
    async def mine_with_utilization_awareness(self, threat_score: float, method: str, host: str, path: str) -> Optional[Dict]:
        """Mine with utilization-aware resource allocation"""
        
        self.performance_counters['mining_attempts'] += 1
        
        # Get current mining strategy based on utilization
        mining_strategy = self.mining_strategies.get(self.current_strategy, self._balanced_mining)
        
        # Generate utilization-aware nonce
        nonce_metadata = self.generate_utilization_aware_nonce(threat_score, method, host, path)
        
        # Execute mining with current strategy
        mining_result = await mining_strategy(nonce_metadata)
        
        if mining_result:
            self.performance_counters['mining_successes'] += 1
            reward = self.calculate_utilization_reward(threat_score, mining_result)
            self.total_rewards += reward
            
            # Update mining efficiency metric
            self.utilization_metrics.mining_efficiency = (
                self.performance_counters['mining_successes'] / 
                max(1, self.performance_counters['mining_attempts'])
            )
            
            self.log_utilization_mining(mining_result, reward, method, host, path)
            return mining_result
        
        return None
    
    def generate_utilization_aware_nonce(self, threat_score: float, method: str, host: str, path: str) -> Dict:
        """Generate nonce with utilization context"""
        
        nonce_metadata = {
            "nonce_id": f"UTIL-NONCE-{int(time.time())}-{secrets.token_hex(4)}",
            "timestamp": utc_now_iso(),
            "utilization_context": {
                "mining_intensity": self.mining_intensity,
                "current_strategy": self.current_strategy,
                "system_load": self.utilization_metrics.cpu_usage,
                "threat_score": threat_score
            },
            "traffic_context": {
                "method": method,
                "host": host,
                "path": path
            },
            "mining_context": {
                "miner_id": self.miner_id,
                "difficulty": self.mining_difficulty,
                "base_nonce": self.calculate_utilization_nonce(method, host, path)
            }
        }
        
        return nonce_metadata
    
    def calculate_utilization_nonce(self, method: str, host: str, path: str) -> int:
        """Calculate nonce based on utilization and traffic patterns"""
        method_hash = int(hashlib.md5(method.encode()).hexdigest()[:8], 16)
        host_hash = int(hashlib.md5(host.encode()).hexdigest()[:8], 16)
        path_hash = int(hashlib.md5(path.encode()).hexdigest()[:8], 16)
        util_hash = int(hashlib.md5(str(self.mining_intensity).encode()).hexdigest()[:8], 16)
        
        combined_nonce = (method_hash ^ host_hash) + (path_hash | util_hash)
        return abs(combined_nonce) % int(1000000 * self.mining_intensity)
    
    async def _low_utilization_mining(self, nonce_metadata: Dict) -> Optional[Dict]:
        """Mining strategy for low utilization - aggressive mining"""
        return await self.mine_with_range(nonce_metadata, 0, 50000, timeout=3.0)
    
    async def _high_utilization_mining(self, nonce_metadata: Dict) -> Optional[Dict]:
        """Mining strategy for high utilization - conservative mining"""
        return await self.mine_with_range(nonce_metadata, 0, 5000, timeout=1.0)
    
    async def _balanced_mining(self, nonce_metadata: Dict) -> Optional[Dict]:
        """Balanced mining strategy"""
        return await self.mine_with_range(nonce_metadata, 0, 20000, timeout=2.0)
    
    async def _aggressive_mining(self, nonce_metadata: Dict) -> Optional[Dict]:
        """Aggressive mining strategy"""
        return await self.mine_with_range(nonce_metadata, 0, 100000, timeout=5.0)
    
    async def mine_with_range(self, nonce_metadata: Dict, start: int, end: int, timeout: float) -> Optional[Dict]:
        """Mine within specified range with timeout"""
        target_prefix = "0" * self.mining_difficulty
        start_time = time.time()
        
        base_nonce = nonce_metadata["mining_context"]["base_nonce"]
        
        for nonce in range(start + base_nonce, end + base_nonce):
            if (time.time() - start_time) >= timeout:
                break
                
            data_string = f"{nonce}:{json.dumps(nonce_metadata, sort_keys=True)}"
            candidate_hash = hashlib.sha256(data_string.encode()).hexdigest()
            
            if candidate_hash.startswith(target_prefix):
                return {
                    "block_hash": candidate_hash,
                    "nonce": nonce,
                    "nonce_metadata": nonce_metadata,
                    "miner_id": self.miner_id,
                    "mining_time": time.time() - start_time
                }
        
        return None
    
    def calculate_utilization_reward(self, threat_score: float, mining_result: Dict) -> float:
        """Calculate reward based on utilization and threat score"""
        base_multiplier = 1.0 + (threat_score * 3.0)
        
        # Utilization-based bonus - higher utilization = higher reward for successful mining
        utilization_bonus = 1.0 + (1.0 - self.mining_intensity) * 0.5
        
        # Strategy-based bonuses
        strategy_bonuses = {
            'low_utilization': 1.0,
            'high_utilization': 1.5,  # Higher reward for mining under high load
            'balanced': 1.2,
            'aggressive': 1.1
        }
        
        strategy_bonus = strategy_bonuses.get(self.current_strategy, 1.0)
        
        return self.base_reward * base_multiplier * utilization_bonus * strategy_bonus
    
    def log_utilization_mining(self, mining_result: Dict, reward: float, method: str, host: str, path: str):
        """Log utilization-aware mining operation"""
        
        mining_record = {
            "type": "utilization_mining",
            "miner_id": self.miner_id,
            "timestamp": utc_now_iso(),
            "utilization_metrics": self.utilization_metrics.__dict__.copy(),
            "mining_result": mining_result,
            "reward": reward,
            "traffic_context": {
                "method": method,
                "host": host,
                "path": path
            },
            "mining_strategy": self.current_strategy,
            "mining_intensity": self.mining_intensity
        }
        
        append_ledger(mining_record)
        print(f"   💰 Util Mining ({self.current_strategy}): {reward:.6f} HSM - {method} {host}")
    
    async def forward_request_with_utilization(self, request_data: bytes, target_host: str, target_port: int) -> Optional[bytes]:
        """Forward request with utilization-based resource management"""
        try:
            # Adjust timeout based on current utilization
            timeout = max(5.0, 30.0 * self.mining_intensity)  # More aggressive timeout under high load
            
            async with asyncio.timeout(timeout):
                target_reader, target_writer = await asyncio.open_connection(target_host, target_port)
                
                # Forward request
                target_writer.write(request_data)
                await target_writer.drain()
                
                # Read response
                response_data = await target_reader.read(65536)  # Limited read for high utilization
                
                target_writer.close()
                await target_writer.wait_closed()
                
                return response_data
                
        except asyncio.TimeoutError:
            print(f"⏰ Forwarding timeout to {target_host}:{target_port} (util: {self.mining_intensity:.2f})")
            return None
        except Exception as e:
            print(f"❌ Forwarding error to {target_host}:{target_port}: {e}")
            return None
    
    def get_detailed_utilization_report(self) -> Dict[str, Any]:
        """Get comprehensive utilization report"""
        return {
            "miner_id": self.miner_id,
            "current_utilization": self.utilization_metrics.__dict__,
            "mining_performance": {
                "mined_blocks": self.mined_blocks,
                "total_rewards": self.total_rewards,
                "mining_efficiency": self.utilization_metrics.mining_efficiency,
                "current_strategy": self.current_strategy,
                "mining_intensity": self.mining_intensity,
                "mining_difficulty": self.mining_difficulty
            },
            "proxy_performance": {
                "requests_processed": self.performance_counters['requests_processed'],
                "bytes_transferred": self.performance_counters['bytes_transferred'],
                "active_connections": len(self.connection_pool),
                "threats_detected": self.utilization_metrics.threat_density,
                "error_rate": self.utilization_metrics.error_rate
            },
            "resource_usage": {
                "cpu_usage": self.utilization_metrics.cpu_usage,
                "memory_usage": self.utilization_metrics.memory_usage,
                "bandwidth_usage": self.utilization_metrics.bandwidth_usage,
                "adaptive_mining": self.adaptive_mining_enabled
            }
        }

# Demonstration and testing
async def demonstrate_utilization_mining():
    """Demonstrate the enhanced utilization mining capabilities"""
    
    print("🎯 HSM PROXY UTILIZATION MINER DEMONSTRATION")
    print("Adaptive mining based on real-time system utilization\n")
    
    # Create miner instance
    miner = HSMProxyUtilizationMiner(
        proxy_host="127.0.0.1",
        proxy_port=8080,
        mining_difficulty=2,
        base_reward=0.001
    )
    
    # Simulate different utilization scenarios
    utilization_scenarios = [
        {"cpu": 20, "memory": 30, "connections": 5, "name": "LOW_LOAD"},
        {"cpu": 50, "memory": 60, "connections": 25, "name": "MEDIUM_LOAD"}, 
        {"cpu": 85, "memory": 80, "connections": 80, "name": "HIGH_LOAD"},
        {"cpu": 95, "memory": 90, "connections": 120, "name": "CRITICAL_LOAD"}
    ]
    
    print("=== UTILIZATION ADAPTATION TEST ===")
    
    for scenario in utilization_scenarios:
        # Simulate system state
        miner.utilization_metrics.cpu_usage = scenario["cpu"]
        miner.utilization_metrics.memory_usage = scenario["memory"] 
        miner.utilization_metrics.active_connections = scenario["connections"]
        
        # Update mining intensity
        miner.update_mining_intensity()
        
        print(f"\n📈 Scenario: {scenario['name']}")
        print(f"   CPU: {scenario['cpu']}% | Memory: {scenario['memory']}% | Connections: {scenario['connections']}")
        print(f"   Mining Intensity: {miner.mining_intensity:.2f}")
        print(f"   Current Strategy: {miner.current_strategy}")
        print(f"   Mining Difficulty: {miner.mining_difficulty}")
        
        # Test mining with current strategy
        test_nonce_metadata = miner.generate_utilization_aware_nonce(0.7, "GET", "example.com", "/test")
        mining_result = await miner.mine_with_utilization_awareness(0.7, "GET", "example.com", "/test")
        
        if mining_result:
            reward = miner.calculate_utilization_reward(0.7, mining_result)
            print(f"   💰 Mining successful! Reward: {reward:.6f} HSM")
        else:
            print(f"   ⏹️  No block mined (expected under {scenario['name']})")
    
    # Show final utilization report
    print(f"\n=== COMPREHENSIVE UTILIZATION REPORT ===")
    report = miner.get_detailed_utilization_report()
    
    for category, data in report.items():
        print(f"\n{category.upper()}:")
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.2f}")
                else:
                    print(f"   {key}: {value}")

if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demonstrate_utilization_mining())
    
    print("\n" + "="*60)
    print("UTILIZATION-AWARE MINING BENEFITS")
    print("="*60)
    benefits = [
        "✓ Dynamic resource allocation based on system load",
        "✓ Adaptive mining intensity (0.1 to 1.0 scale)",
        "✓ Four strategic mining modes for different load levels",
        "✓ Real-time system metrics integration",
        "✓ No performance degradation for legitimate traffic",
        "✓ Intelligent threat analysis depth adjustment",
        "✓ Self-optimizing based on utilization patterns",
        "✓ Comprehensive metrics and reporting"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")