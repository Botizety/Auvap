"""
State Manager for AUVAP Framework

Manages the global state of the penetration testing process, including:
- Connectivity and privilege matrices
- Discovery tracking (what's been found vs explored)
- Action history and effects
- Rate limiting for rescans
- State snapshots for hierarchical planning
"""

import time
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger
import numpy as np


@dataclass
class HostState:
    """State information for a single host"""
    host_id: str
    discovered: bool = False
    owned: bool = False
    privilege_level: str = "none"  # none, user, admin, system
    services: List[str] = field(default_factory=list)
    vulnerabilities: List[str] = field(default_factory=list)
    credentials_found: List[str] = field(default_factory=list)
    os_type: Optional[str] = None
    value: int = 0
    last_scan_time: float = 0.0
    scan_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'host_id': self.host_id,
            'discovered': self.discovered,
            'owned': self.owned,
            'privilege': self.privilege_level,
            'services': self.services,
            'vulnerabilities': len(self.vulnerabilities),
            'credentials': len(self.credentials_found),
            'os': self.os_type,
            'value': self.value
        }


@dataclass
class ActionRecord:
    """Record of a single action taken"""
    step: int
    action_type: str
    source_host: Optional[str]
    target_host: Optional[str]
    tool_used: Optional[str]
    success: bool
    reward: float
    cost: float
    noise_level: float
    discoveries: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class StateManager:
    """
    Manages the complete state of the penetration testing episode
    
    Responsibilities:
    - Track all hosts, services, vulnerabilities
    - Maintain connectivity and privilege matrices
    - Record action history
    - Provide state queries for Manager/Worker agents
    - Rate-limit rescans to prevent resource waste
    - Generate state snapshots for CKG updates
    """
    
    def __init__(self, scan_cooldown: float = 5.0):
        """
        Initialize state manager
        
        Args:
            scan_cooldown: Minimum time (in steps) between rescans of same target
        """
        self.scan_cooldown = scan_cooldown
        
        # Host tracking
        self.hosts: Dict[str, HostState] = {}
        
        # Connectivity: source -> set of reachable targets
        self.connectivity_matrix: Dict[str, Set[str]] = defaultdict(set)
        
        # Privilege: host -> privilege level
        self.privilege_matrix: Dict[str, str] = {}
        
        # Credentials: credential_id -> metadata
        self.credentials: Dict[str, Dict] = {}
        
        # Action history
        self.action_history: List[ActionRecord] = []
        
        # Current step counter
        self.current_step = 0
        
        # Current agent position
        self.current_host: Optional[str] = None
        
        # Goal tracking
        self.goal_hosts: Set[str] = set()
        self.compromised_goals: Set[str] = set()
        
        logger.info("StateManager initialized")
    
    def reset(self):
        """Reset state for new episode"""
        self.hosts.clear()
        self.connectivity_matrix.clear()
        self.privilege_matrix.clear()
        self.credentials.clear()
        self.action_history.clear()
        self.current_step = 0
        self.current_host = None
        self.goal_hosts.clear()
        self.compromised_goals.clear()
        
        logger.info("StateManager reset for new episode")
    
    def add_host(self, host_id: str, **kwargs) -> HostState:
        """
        Add or update a host in the state
        
        Args:
            host_id: Unique host identifier
            **kwargs: Additional host properties
        
        Returns:
            HostState object
        """
        if host_id not in self.hosts:
            self.hosts[host_id] = HostState(host_id=host_id, **kwargs)
            logger.debug(f"Added new host: {host_id}")
        else:
            # Update existing host
            for key, value in kwargs.items():
                if hasattr(self.hosts[host_id], key):
                    setattr(self.hosts[host_id], key, value)
        
        return self.hosts[host_id]
    
    def mark_discovered(self, host_id: str):
        """Mark a host as discovered"""
        if host_id in self.hosts:
            self.hosts[host_id].discovered = True
            logger.debug(f"Host {host_id} marked as discovered")
    
    def mark_owned(self, host_id: str, privilege: str = "user"):
        """Mark a host as owned with given privilege level"""
        if host_id in self.hosts:
            self.hosts[host_id].owned = True
            self.hosts[host_id].privilege_level = privilege
            self.privilege_matrix[host_id] = privilege
            
            # Check if goal compromised
            if host_id in self.goal_hosts:
                self.compromised_goals.add(host_id)
            
            logger.info(f"Host {host_id} owned with {privilege} privilege")
    
    def add_connection(self, source: str, target: str):
        """Add a network connection between hosts"""
        self.connectivity_matrix[source].add(target)
        logger.debug(f"Added connection: {source} -> {target}")
    
    def can_reach(self, source: str, target: str) -> bool:
        """Check if source can reach target"""
        return target in self.connectivity_matrix.get(source, set())
    
    def get_reachable_hosts(self, source: str) -> List[str]:
        """Get all hosts reachable from source"""
        return list(self.connectivity_matrix.get(source, set()))
    
    def add_service(self, host_id: str, service_name: str, vulnerabilities: List[str] = None):
        """Add a service to a host"""
        if host_id in self.hosts:
            if service_name not in self.hosts[host_id].services:
                self.hosts[host_id].services.append(service_name)
            
            if vulnerabilities:
                for vuln in vulnerabilities:
                    if vuln not in self.hosts[host_id].vulnerabilities:
                        self.hosts[host_id].vulnerabilities.append(vuln)
            
            logger.debug(f"Added service {service_name} to {host_id}")
    
    def add_credential(self, cred_id: str, cred_type: str, scope: List[str]):
        """Add discovered credential"""
        self.credentials[cred_id] = {
            'type': cred_type,
            'scope': scope,
            'discovered_at': self.current_step
        }
        logger.info(f"Credential {cred_id} discovered")
    
    def record_action(self, action: ActionRecord):
        """Record an action in history"""
        action.step = self.current_step
        self.action_history.append(action)
        self.current_step += 1
    
    def can_scan(self, host_id: str) -> bool:
        """
        Check if host can be scanned (rate limiting)
        
        Args:
            host_id: Target host to scan
        
        Returns:
            True if scan is allowed
        """
        if host_id not in self.hosts:
            return True
        
        host = self.hosts[host_id]
        steps_since_scan = self.current_step - host.last_scan_time
        
        return steps_since_scan >= self.scan_cooldown
    
    def mark_scanned(self, host_id: str):
        """Mark host as scanned (for rate limiting)"""
        if host_id in self.hosts:
            self.hosts[host_id].last_scan_time = self.current_step
            self.hosts[host_id].scan_count += 1
    
    def get_owned_hosts(self) -> List[str]:
        """Get list of all owned hosts"""
        return [h_id for h_id, h in self.hosts.items() if h.owned]
    
    def get_discovered_hosts(self) -> List[str]:
        """Get list of all discovered hosts"""
        return [h_id for h_id, h in self.hosts.items() if h.discovered]
    
    def get_unexplored_hosts(self) -> List[str]:
        """Get hosts that are discovered but not fully explored"""
        unexplored = []
        for h_id, h in self.hosts.items():
            if h.discovered and not h.owned:
                # Consider unexplored if not recently scanned
                if self.can_scan(h_id):
                    unexplored.append(h_id)
        return unexplored
    
    def get_host_by_id(self, host_id: str) -> Optional[HostState]:
        """Get host state by ID"""
        return self.hosts.get(host_id)
    
    def get_privilege(self, host_id: str) -> str:
        """Get current privilege level on host"""
        return self.privilege_matrix.get(host_id, "none")
    
    def has_credential_for(self, host_id: str) -> bool:
        """Check if we have credentials valid for target host"""
        for cred_id, cred in self.credentials.items():
            if host_id in cred['scope']:
                return True
        return False
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """
        Generate a complete state snapshot
        Used for CKG updates and Manager decision-making
        """
        return {
            'step': self.current_step,
            'current_host': self.current_host,
            'hosts': {h_id: h.to_dict() for h_id, h in self.hosts.items()},
            'connectivity': {src: list(targets) for src, targets in self.connectivity_matrix.items()},
            'privileges': dict(self.privilege_matrix),
            'credentials': len(self.credentials),
            'owned_count': len(self.get_owned_hosts()),
            'discovered_count': len(self.get_discovered_hosts()),
            'goals': {
                'total': len(self.goal_hosts),
                'compromised': len(self.compromised_goals)
            },
            'recent_actions': [
                {
                    'type': a.action_type,
                    'target': a.target_host,
                    'success': a.success
                }
                for a in self.action_history[-10:]  # Last 10 actions
            ]
        }
    
    def get_penetration_phase(self) -> str:
        """
        Determine current penetration testing phase
        
        Returns:
            Phase name: 'reconnaissance', 'initial_access', 'lateral_movement', 'privilege_escalation', 'goal_achieved'
        """
        owned = len(self.get_owned_hosts())
        discovered = len(self.get_discovered_hosts())
        
        # Goal achieved
        if self.goal_hosts and len(self.compromised_goals) == len(self.goal_hosts):
            return 'goal_achieved'
        
        # No hosts owned yet - reconnaissance/initial access
        if owned == 0:
            if discovered == 0:
                return 'reconnaissance'
            else:
                return 'initial_access'
        
        # Have foothold, looking to expand
        if owned > 0 and discovered > owned:
            return 'lateral_movement'
        
        # On owned hosts, trying to escalate
        if owned > 0:
            # Check if any owned hosts have low privilege
            for h_id in self.get_owned_hosts():
                priv = self.get_privilege(h_id)
                if priv in ['user', 'none']:
                    return 'privilege_escalation'
        
        return 'lateral_movement'
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get episode statistics"""
        return {
            'total_steps': self.current_step,
            'hosts_discovered': len(self.get_discovered_hosts()),
            'hosts_owned': len(self.get_owned_hosts()),
            'credentials_found': len(self.credentials),
            'services_found': sum(len(h.services) for h in self.hosts.values()),
            'vulnerabilities_found': sum(len(h.vulnerabilities) for h in self.hosts.values()),
            'successful_actions': sum(1 for a in self.action_history if a.success),
            'failed_actions': sum(1 for a in self.action_history if not a.success),
            'total_reward': sum(a.reward for a in self.action_history),
            'total_cost': sum(a.cost for a in self.action_history),
            'phase': self.get_penetration_phase(),
            'goal_progress': f"{len(self.compromised_goals)}/{len(self.goal_hosts)}" if self.goal_hosts else "N/A"
        }
    
    def __repr__(self) -> str:
        stats = self.get_statistics()
        return f"StateManager(step={stats['total_steps']}, owned={stats['hosts_owned']}, phase={stats['phase']})"


if __name__ == "__main__":
    # Test StateManager
    logger.info("Testing StateManager...")
    
    sm = StateManager()
    
    # Add some hosts
    sm.add_host("client", os_type="Windows10", value=10)
    sm.add_host("web-01", os_type="Ubuntu20", value=50)
    sm.add_host("db-01", os_type="Ubuntu20", value=100)
    
    # Mark discovery
    sm.mark_discovered("client")
    sm.mark_discovered("web-01")
    
    # Mark owned
    sm.mark_owned("client", privilege="admin")
    
    # Add connectivity
    sm.add_connection("client", "web-01")
    sm.add_connection("web-01", "db-01")
    
    # Add services
    sm.add_service("web-01", "http", ["CVE-2021-1234"])
    sm.add_service("db-01", "mysql", ["CVE-2021-5678"])
    
    # Print state
    print("\n=== State Snapshot ===")
    snapshot = sm.get_state_snapshot()
    for key, value in snapshot.items():
        print(f"{key}: {value}")
    
    print("\n=== Statistics ===")
    stats = sm.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print(f"\n{sm}")
    logger.info("Test completed!")
