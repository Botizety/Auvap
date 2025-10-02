"""
CyberBattleSim Wrapper for AUVAP Framework

This module wraps CyberBattleSim to extract network state, observations,
and provides a standardized interface for the AUVAP hierarchical agents.

Key responsibilities:
- Initialize CyberBattleSim environments (chain, mesh, custom topologies)
- Extract observation data (hosts, services, vulnerabilities, credentials)
- Provide action space with detailed metadata
- Track episode state and connectivity matrix
- Interface with CKG for real-time updates
"""

import gym
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from loguru import logger
import cyberbattle.simulation.model as model
import cyberbattle.simulation.generate_network as generate
from cyberbattle import _env


@dataclass
class NetworkObservation:
    """Structured observation from CyberBattleSim"""
    discovered_hosts: List[str] = field(default_factory=list)
    discovered_services: Dict[str, List[Dict]] = field(default_factory=dict)
    discovered_credentials: List[Dict] = field(default_factory=list)
    owned_hosts: List[str] = field(default_factory=list)
    connectivity_matrix: Dict[str, List[str]] = field(default_factory=dict)
    privilege_levels: Dict[str, str] = field(default_factory=dict)  # host -> privilege
    current_node: Optional[str] = None
    step_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            'discovered_hosts': self.discovered_hosts,
            'discovered_services': self.discovered_services,
            'discovered_credentials': len(self.discovered_credentials),
            'owned_hosts': self.owned_hosts,
            'connectivity': len(self.connectivity_matrix),
            'current_node': self.current_node,
            'step_count': self.step_count
        }


class CyberBattleSimWrapper(gym.Wrapper):
    """
    Wrapper around CyberBattleSim environment that provides:
    1. Structured observation extraction
    2. Network state tracking
    3. Action metadata (for CKG integration)
    4. Episode metrics
    """
    
    def __init__(
        self,
        env_name: str = "CyberBattleTiny-v0",
        custom_network: Optional[model.Environment] = None,
        **kwargs
    ):
        """
        Initialize CyberBattleSim wrapper
        
        Args:
            env_name: Name of CBS environment ('CyberBattleTiny-v0', 'CyberBattleChain-v0', etc.)
            custom_network: Optional custom network environment
            **kwargs: Additional arguments passed to gym.make()
        """
        # Create base environment
        if custom_network:
            self.base_env = gymenvs.CyberBattleEnv(custom_network, **kwargs)
            env = self.base_env
        else:
            env = gym.make(env_name)
            self.base_env = env
            
        super().__init__(env)
        
        self.env_name = env_name
        self.episode_count = 0
        self.total_steps = 0
        
        # Track network state
        self.network_state = NetworkObservation()
        
        # CBS-specific attributes
        self.simulation = None
        
        logger.info(f"Initialized CyberBattleSimWrapper with {env_name}")
        
    def reset(self, **kwargs) -> np.ndarray:
        """Reset environment and extract initial observations"""
        obs = self.env.reset(**kwargs)
        self.episode_count += 1
        
        # Access CBS simulation object
        if hasattr(self.env, 'environment'):
            self.simulation = self.env.environment
        elif hasattr(self.env, 'unwrapped') and hasattr(self.env.unwrapped, 'environment'):
            self.simulation = self.env.unwrapped.environment
            
        # Initialize network state
        self.network_state = NetworkObservation()
        self._update_network_state()
        
        logger.info(f"Episode {self.episode_count} started - Initial state: {self.network_state.to_dict()}")
        
        return obs
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute action and update network state"""
        obs, reward, done, info = self.env.step(action)
        self.total_steps += 1
        self.network_state.step_count += 1
        
        # Update network state after action
        self._update_network_state()
        
        # Add network state to info
        info['network_state'] = self.network_state
        info['action_metadata'] = self._get_action_metadata(action)
        
        return obs, reward, done, info
    
    def _update_network_state(self):
        """Extract current network state from CyberBattleSim"""
        if not self.simulation:
            return
            
        # Get discovered nodes
        discovered = self.simulation.get_discovered_nodes()
        self.network_state.discovered_hosts = list(discovered)
        
        # Get owned nodes
        owned = self.simulation.get_owned_nodes()
        self.network_state.owned_hosts = list(owned)
        
        # Get current node
        if hasattr(self.simulation, 'current_node'):
            self.network_state.current_node = self.simulation.current_node
        
        # Extract services per host
        for node_id in discovered:
            node_data = self.simulation.get_node(node_id)
            if node_data:
                services = []
                
                # Extract service information
                if hasattr(node_data, 'services'):
                    for service_name, service in node_data.services.items():
                        service_info = {
                            'name': service_name,
                            'type': getattr(service, 'type', 'unknown'),
                            'vulnerabilities': []
                        }
                        
                        # Extract vulnerabilities
                        if hasattr(service, 'vulnerabilities'):
                            for vuln_id, vuln in service.vulnerabilities.items():
                                vuln_info = {
                                    'id': vuln_id,
                                    'type': getattr(vuln, 'type', 'unknown'),
                                    'outcome': getattr(vuln, 'outcome', None)
                                }
                                service_info['vulnerabilities'].append(vuln_info)
                        
                        services.append(service_info)
                
                self.network_state.discovered_services[node_id] = services
        
        # Extract connectivity (which nodes can reach which)
        connectivity = {}
        for node_id in owned:
            node_data = self.simulation.get_node(node_id)
            if node_data and hasattr(node_data, 'connections'):
                connectivity[node_id] = list(node_data.connections)
        
        self.network_state.connectivity_matrix = connectivity
        
        # Extract privilege levels
        privilege = {}
        for node_id in owned:
            # Check if we have admin/system privileges
            node_data = self.simulation.get_node(node_id)
            if node_data:
                # CBS tracks privilege through ownership flags
                privilege[node_id] = 'admin' if node_id in owned else 'user'
        
        self.network_state.privilege_levels = privilege
        
        # Extract discovered credentials
        if hasattr(self.simulation, 'credentials'):
            creds = []
            for cred_id, cred in self.simulation.credentials.items():
                cred_info = {
                    'id': cred_id,
                    'type': getattr(cred, 'type', 'unknown'),
                    'scope': getattr(cred, 'scope', [])
                }
                creds.append(cred_info)
            self.network_state.discovered_credentials = creds
    
    def _get_action_metadata(self, action: int) -> Dict[str, Any]:
        """
        Extract metadata about the action taken
        This will be used by CKG for feature extraction
        """
        if not hasattr(self.env, 'action_space'):
            return {}
        
        # CBS actions are typically structured as tuples or discrete
        # We need to decode the action into its components
        metadata = {
            'action_id': action,
            'action_type': 'unknown',
            'target': None,
            'tool': None,
            'parameters': {}
        }
        
        # Try to extract action details from CBS
        if hasattr(self.env, 'decode_action'):
            decoded = self.env.decode_action(action)
            metadata.update(decoded)
        
        return metadata
    
    def get_network_topology(self) -> Dict[str, Any]:
        """
        Extract full network topology for CKG initialization
        """
        if not self.simulation:
            return {}
        
        topology = {
            'nodes': {},
            'edges': [],
            'credentials': []
        }
        
        # Get all nodes from environment
        if hasattr(self.simulation, 'network'):
            network = self.simulation.network
            
            for node_id, node_data in network.nodes.items():
                node_info = {
                    'id': node_id,
                    'value': getattr(node_data, 'value', 0),
                    'services': {},
                    'properties': {}
                }
                
                # Extract services
                if hasattr(node_data, 'services'):
                    for svc_name, svc in node_data.services.items():
                        node_info['services'][svc_name] = {
                            'name': svc_name,
                            'vulnerabilities': list(getattr(svc, 'vulnerabilities', {}).keys())
                        }
                
                # Extract node properties (OS, etc.)
                if hasattr(node_data, 'properties'):
                    node_info['properties'] = node_data.properties
                
                topology['nodes'][node_id] = node_info
            
            # Extract edges (connections)
            for src_id, src_node in network.nodes.items():
                if hasattr(src_node, 'connections'):
                    for target_id in src_node.connections:
                        topology['edges'].append({
                            'source': src_id,
                            'target': target_id,
                            'type': 'network_connection'
                        })
        
        return topology
    
    def get_action_space_info(self) -> Dict[str, Any]:
        """
        Get detailed information about the action space
        Used for CKG action masking
        """
        info = {
            'type': type(self.action_space).__name__,
            'size': self.action_space.n if hasattr(self.action_space, 'n') else None,
            'actions': []
        }
        
        # CBS typically uses Discrete action spaces
        if hasattr(self.env, 'get_action_space'):
            info['actions'] = self.env.get_action_space()
        
        return info
    
    def get_observation_space_info(self) -> Dict[str, Any]:
        """Get detailed information about observation space"""
        info = {
            'type': type(self.observation_space).__name__,
            'shape': self.observation_space.shape if hasattr(self.observation_space, 'shape') else None,
            'features': []
        }
        
        return info
    
    @property
    def current_state(self) -> NetworkObservation:
        """Get current network observation"""
        return self.network_state
    
    def render(self, mode='human'):
        """Render environment state"""
        if mode == 'human':
            print(f"\n=== CyberBattleSim State (Step {self.network_state.step_count}) ===")
            print(f"Discovered Hosts: {self.network_state.discovered_hosts}")
            print(f"Owned Hosts: {self.network_state.owned_hosts}")
            print(f"Current Node: {self.network_state.current_node}")
            print(f"Services: {len(self.network_state.discovered_services)} hosts mapped")
            print(f"Credentials: {len(self.network_state.discovered_credentials)} discovered")
            print("=" * 60)
        
        return super().render(mode=mode)


def create_chain_network(size: int = 5) -> model.Environment:
    """
    Create a chain topology network for testing
    
    Args:
        size: Number of nodes in chain (default 5)
    
    Returns:
        CyberBattleSim Environment
    """
    logger.info(f"Creating chain network with {size} nodes")
    
    # Use CBS's chain network generator
    return generate.create_chain_network(size)


def create_custom_network(config: Dict[str, Any]) -> model.Environment:
    """
    Create a custom network topology from configuration
    
    Args:
        config: Network configuration dictionary
    
    Returns:
        CyberBattleSim Environment
    """
    logger.info(f"Creating custom network from config")
    
    # This would parse a YAML/JSON config and build CBS network
    # Implementation depends on config format
    
    raise NotImplementedError("Custom network creation from config not yet implemented")


if __name__ == "__main__":
    # Test the wrapper
    logger.info("Testing CyberBattleSimWrapper...")
    
    # Try to create wrapper with chain environment
    try:
        env = CyberBattleSimWrapper(env_name="CyberBattleChain-v0")
        
        obs = env.reset()
        print(f"Initial observation shape: {obs.shape}")
        print(f"Initial network state: {env.current_state.to_dict()}")
        
        # Take a few random steps
        for i in range(5):
            action = env.action_space.sample()
            obs, reward, done, info = env.step(action)
            print(f"\nStep {i+1}: reward={reward:.3f}, done={done}")
            print(f"Network state: {info['network_state'].to_dict()}")
            
            if done:
                break
        
        env.close()
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        logger.info("Install CyberBattleSim: pip install cyberbattlesim")
