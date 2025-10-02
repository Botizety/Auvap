"""
CyberBattleSim Wrapper for AUVAP Framework (Updated for cyberbattle package)

This module wraps CyberBattleSim to extract network state, observations,
and provides a standardized interface for the AUVAP hierarchical agents.

Key responsibilities:
- Initialize CyberBattleSim environments (chain, toyctf, custom topologies)
- Extract observation data (hosts, services, vulnerabilities, credentials)
- Provide action space with detailed metadata
- Track episode state and connectivity matrix
- Interface with CKG for real-time updates
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from loguru import logger

# CyberBattle imports
from cyberbattle._env.cyberbattle_env import CyberBattleEnv
from cyberbattle.samples.chainpattern import chainpattern
from cyberbattle.samples.toyctf import toy_ctf


@dataclass
class NetworkObservation:
    """Structured observation from CyberBattleSim"""
    discovered_hosts: List[str] = field(default_factory=list)
    discovered_services: Dict[str, List[Dict]] = field(default_factory=dict)
    discovered_credentials: List[Dict] = field(default_factory=list)
    owned_hosts: List[str] = field(default_factory=list)
    connectivity_matrix: Dict[str, List[str]] = field(default_factory=dict)
    privilege_levels: Dict[str, str] = field(default_factory=dict)
    current_node: Optional[str] = None
    step_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            'discovered_hosts': len(self.discovered_hosts),
            'discovered_services': sum(len(s) for s in self.discovered_services.values()),
            'discovered_credentials': len(self.discovered_credentials),
            'owned_hosts': len(self.owned_hosts),
            'connectivity': len(self.connectivity_matrix),
            'current_node': self.current_node,
            'step_count': self.step_count
        }


class CyberBattleSimWrapper:
    """
    Wrapper around CyberBattleSim environment that provides:
    1. Structured observation extraction
    2. Network state tracking
    3. Action metadata (for CKG integration)
    4. Episode metrics
    """
    
    def __init__(
        self,
        env_name: str = "chain",
        size: int = 6,
        maximum_total_credentials: int = 10,
        maximum_node_count: int = 10,
        **kwargs
    ):
        """
        Initialize CyberBattleSim wrapper
        
        Args:
            env_name: Type of environment ('chain', 'toyctf', 'tiny')
            size: Size of network (for chain topology, must be even)
            maximum_total_credentials: Max credentials to track
            maximum_node_count: Max nodes to track
            **kwargs: Additional arguments
        """
        # Create CyberBattle environment based on type
        if env_name.lower() in ['chain', 'cyberbattlechain', 'cyberbattlechain-v0']:
            logger.info(f"Creating chain network with {size} nodes")
            env_spec = chainpattern.new_environment(size=size)
            env = CyberBattleEnv(
                env_spec,
                maximum_total_credentials=maximum_total_credentials,
                maximum_node_count=maximum_node_count
            )
        elif env_name.lower() in ['toyctf', 'toy']:
            logger.info("Creating ToyCtf network")
            env_spec = toy_ctf.new_environment()
            env = CyberBattleEnv(
                env_spec,
                maximum_total_credentials=maximum_total_credentials,
                maximum_node_count=maximum_node_count
            )
        else:
            raise ValueError(f"Unknown environment type: {env_name}. Use 'chain' or 'toyctf'")
            
        self.env = env
        self.action_space = env.action_space
        self.observation_space = env.observation_space
        
        self.env_name = env_name
        self.episode_count = 0
        self.total_steps = 0
        
        # Track network state
        self.network_state = NetworkObservation()
        
        logger.info(f"Initialized CyberBattleSimWrapper with {env_name}")
        
    def reset(self, **kwargs) -> np.ndarray:
        """Reset environment and extract initial observations"""
        # CyberBattle reset returns (obs, info) tuple
        obs, info = self.env.reset(**kwargs)
        self.episode_count += 1
        
        # Initialize network state
        self.network_state = NetworkObservation()
        self._update_network_state(obs, info)
        
        logger.info(f"Episode {self.episode_count} started - Initial state: {self.network_state.to_dict()}")
        
        # Return just obs for gym.Env compatibility
        return self._flatten_observation(obs)
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute action and update network state"""
        # CyberBattle step returns (obs, reward, terminated, truncated, info)
        obs, reward, terminated, truncated, info = self.env.step(action)
        
        self.total_steps += 1
        self.network_state.step_count += 1
        
        # Update network state after action
        self._update_network_state(obs, info)
        
        # Add network state to info
        info['network_state'] = self.network_state
        
        # Combine terminated and truncated for gym.Env compatibility
        done = terminated or truncated
        
        return self._flatten_observation(obs), reward, done, info
    
    def _flatten_observation(self, obs: Dict) -> np.ndarray:
        """
        Convert CyberBattle's dict observation to flat array
        
        CyberBattle returns observations like:
        {
            'newly_discovered_nodes_count': 0,
            'leaked_credentials': array([...]),
            'lateral_move': array([...]),
            'customer_data_found': 0,
            'escalation': array([...]),
            ...
        }
        """
        # Extract key features and flatten to vector
        features = []
        
        # Scalar features
        features.append(float(obs.get('newly_discovered_nodes_count', 0)))
        features.append(float(obs.get('customer_data_found', 0)))
        features.append(float(obs.get('probe_result', 0)))
        
        # Array features (take first N elements or pad)
        array_keys = ['leaked_credentials', 'lateral_move', 'escalation', 
                      'discovered_ports', 'discovered_nodes']
        
        for key in array_keys:
            if key in obs and isinstance(obs[key], np.ndarray):
                arr = obs[key].flatten()[:10]  # Take first 10 elements
                features.extend(arr.tolist())
                # Pad if less than 10
                features.extend([0.0] * max(0, 10 - len(arr)))
            else:
                features.extend([0.0] * 10)
        
        return np.array(features, dtype=np.float32)
    
    def _update_network_state(self, obs: Dict, info: Dict):
        """Extract network state from CyberBattle observation"""
        # CyberBattle provides rich info in the observation dict
        
        # Track discovered nodes (from observation)
        if 'discovered_nodes' in obs:
            discovered_array = obs['discovered_nodes']
            if isinstance(discovered_array, np.ndarray):
                # Non-zero entries indicate discovered nodes
                discovered_indices = np.where(discovered_array > 0)[0]
                self.network_state.discovered_hosts = [f"node_{i}" for i in discovered_indices]
        
        # Track owned nodes (from environment state if available)
        if hasattr(self.env, 'environment'):
            env_state = self.env.environment
            if hasattr(env_state, 'network'):
                network = env_state.network
                # Extract owned nodes from network state
                owned_nodes = [node_id for node_id, node_data in network.nodes.items() 
                              if hasattr(node_data, 'agent_installed') and node_data.agent_installed]
                self.network_state.owned_hosts = owned_nodes
        
        # Track credentials
        if 'leaked_credentials' in obs:
            creds_array = obs['leaked_credentials']
            if isinstance(creds_array, np.ndarray):
                cred_count = int(np.sum(creds_array > 0))
                self.network_state.discovered_credentials = [{'id': i} for i in range(cred_count)]
        
        # Update step count
        if 'step_count' in info:
            self.network_state.step_count = info['step_count']
    
    def get_network_topology(self) -> Dict[str, Any]:
        """Get current network topology for CKG updates"""
        return {
            'hosts': self.network_state.discovered_hosts,
            'owned_hosts': self.network_state.owned_hosts,
            'services': self.network_state.discovered_services,
            'credentials': len(self.network_state.discovered_credentials),
            'connectivity': self.network_state.connectivity_matrix
        }
    
    def get_action_space_details(self) -> Dict[str, Any]:
        """Get detailed action space information"""
        return {
            'type': 'MultiDiscrete',
            'shape': self.env.action_space.nvec.tolist() if hasattr(self.env.action_space, 'nvec') else None,
            'size': int(np.prod(self.env.action_space.nvec)) if hasattr(self.env.action_space, 'nvec') else None
        }
    
    def close(self):
        """Close the environment"""
        if hasattr(self.env, 'close'):
            self.env.close()


# Convenience function for creating chain networks
def create_chain_network(size: int = 6) -> CyberBattleSimWrapper:
    """
    Create a chain network environment
    
    Args:
        size: Number of nodes (must be even)
        
    Returns:
        CyberBattleSimWrapper instance
    """
    return CyberBattleSimWrapper(env_name='chain', size=size)


# Convenience function for creating toyctf network
def create_toyctf_network() -> CyberBattleSimWrapper:
    """
    Create a ToyCtf network environment
    
    Returns:
        CyberBattleSimWrapper instance
    """
    return CyberBattleSimWrapper(env_name='toyctf')


# Test code
if __name__ == "__main__":
    logger.info("Testing CyberBattleSimWrapper...")
    
    # Test chain environment
    try:
        env = create_chain_network(size=6)
        logger.info(f"✓ Created chain environment: {env.get_action_space_details()}")
        
        obs = env.reset()
        logger.info(f"✓ Reset successful - observation shape: {obs.shape}")
        logger.info(f"  Network state: {env.network_state.to_dict()}")
        
        # Take a random action
        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)
        logger.info(f"✓ Step successful - reward: {reward:.2f}, done: {done}")
        logger.info(f"  Network state: {env.network_state.to_dict()}")
        
        logger.success("✓ All tests passed!")
        
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
