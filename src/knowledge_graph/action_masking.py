"""
Action Masking with CKG

Uses the Cybersecurity Knowledge Graph to determine which actions are valid
at any given state. This prevents the agent from trying impossible actions
(e.g., exploiting a service that doesn't exist, connecting to unreachable hosts).

Action masking is a key AUVAP component that:
1. Reduces invalid actions (improves learning efficiency)
2. Encodes domain knowledge (preconditions for actions)
3. Provides interpretability (why certain actions are/aren't available)
"""

from typing import List, Dict, Any, Set, Optional, Tuple
from loguru import logger
import numpy as np

from .ckg_manager import CKGManager
from ..environment.state_manager import StateManager


class ActionMasker:
    """
    Provides action masking based on CKG state
    
    Given current state, determines which actions are:
    - VALID: Preconditions met, can be executed
    - INVALID: Preconditions not met (masked out)
    - SUBOPTIMAL: Valid but recently tried or low-value
    """
    
    def __init__(self, ckg_manager: CKGManager, state_manager: StateManager):
        """
        Initialize action masker
        
        Args:
            ckg_manager: CKG manager for graph queries
            state_manager: State manager for current episode state
        """
        self.ckg = ckg_manager
        self.state = state_manager
        
        logger.info("ActionMasker initialized")
    
    def get_valid_actions(
        self,
        action_space_size: int,
        action_metadata: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Get binary mask for valid actions
        
        Args:
            action_space_size: Total number of possible actions
            action_metadata: Metadata for each action (type, target, requirements)
        
        Returns:
            Binary mask (1=valid, 0=invalid) of shape (action_space_size,)
        """
        mask = np.zeros(action_space_size, dtype=np.float32)
        
        current_host = self.state.current_host
        if not current_host:
            # No current host, only basic discovery actions allowed
            for i, action in enumerate(action_metadata):
                if action.get('type') in ['discover', 'scan']:
                    mask[i] = 1.0
            return mask
        
        # Check each action's preconditions
        for i, action in enumerate(action_metadata):
            if self._check_action_preconditions(action, current_host):
                mask[i] = 1.0
        
        # Ensure at least one action is valid (fallback)
        if mask.sum() == 0:
            logger.warning("No valid actions found, allowing all")
            mask = np.ones(action_space_size, dtype=np.float32)
        
        valid_count = int(mask.sum())
        logger.debug(f"Valid actions: {valid_count}/{action_space_size}")
        
        return mask
    
    def _check_action_preconditions(
        self,
        action: Dict[str, Any],
        current_host: str
    ) -> bool:
        """
        Check if action preconditions are satisfied
        
        Args:
            action: Action metadata
            current_host: Current host ID
        
        Returns:
            True if action is valid
        """
        action_type = action.get('type', '')
        target_host = action.get('target')
        requires_cred = action.get('requires_cred', False)
        
        # Local actions: Must own current host
        if action_type == 'local':
            if not self.state.get_host_by_id(current_host):
                return False
            host = self.state.get_host_by_id(current_host)
            return host.owned if host else False
        
        # Remote actions: Target must be reachable
        elif action_type == 'remote':
            if not target_host:
                return False
            
            # Check reachability
            if not self.state.can_reach(current_host, target_host):
                return False
            
            # Check credential requirement
            if requires_cred and not self.state.has_credential_for(target_host):
                return False
            
            # Check if target is already owned (might be redundant)
            target = self.state.get_host_by_id(target_host)
            if target and target.owned:
                # Already owned, but privilege escalation might be valid
                if action.get('tool') in ['privesc', 'escalate']:
                    return target.privilege_level in ['user', 'none']
                return False  # Other remote actions redundant
            
            return True
        
        # Connect actions: Move between owned hosts
        elif action_type == 'connect':
            if not target_host:
                return False
            
            # Target must be owned
            target = self.state.get_host_by_id(target_host)
            if not target or not target.owned:
                return False
            
            # Must be reachable
            if not self.state.can_reach(current_host, target_host):
                return False
            
            return True
        
        # Discovery actions: Generally always valid
        elif action_type in ['discover', 'scan', 'probe']:
            return True
        
        # Unknown action type
        logger.warning(f"Unknown action type: {action_type}")
        return True  # Allow by default
    
    def get_action_priorities(
        self,
        action_metadata: List[Dict[str, Any]],
        valid_mask: np.ndarray
    ) -> np.ndarray:
        """
        Compute priority scores for valid actions
        
        Higher priority = more valuable action based on:
        - CVSS score of exploitable vulnerabilities
        - Host value
        - Discovery potential
        - Not recently attempted
        
        Args:
            action_metadata: Metadata for each action
            valid_mask: Binary validity mask
        
        Returns:
            Priority scores (0-1) for each action
        """
        priorities = np.zeros(len(action_metadata), dtype=np.float32)
        
        for i, action in enumerate(action_metadata):
            if valid_mask[i] == 0:
                continue  # Skip invalid actions
            
            priority = 0.5  # Base priority
            
            # Prioritize actions on high-value targets
            target = action.get('target')
            if target:
                host = self.state.get_host_by_id(target)
                if host:
                    priority += 0.3 * (host.value / 100.0)  # Normalize to 0-1
            
            # Prioritize unexplored targets
            if target:
                host = self.state.get_host_by_id(target)
                if host and not host.owned:
                    priority += 0.2
            
            # Penalize recently scanned targets (rate limiting)
            if target and not self.state.can_scan(target):
                priority *= 0.5
            
            # Prioritize exploit actions over scan
            if action.get('type') == 'remote' and action.get('tool') in ['exploit', 'metasploit']:
                priority += 0.3
            
            priorities[i] = min(priority, 1.0)
        
        return priorities
    
    def get_exploitable_vulnerabilities(self, host_id: str) -> List[Dict[str, Any]]:
        """
        Query CKG for exploitable vulnerabilities on a host
        
        Args:
            host_id: Target host ID
        
        Returns:
            List of vulnerability dictionaries with exploit info
        """
        if not self.ckg.connected:
            return []
        
        # Query: Find vulnerabilities on host's services with available exploits
        query = """
        MATCH (h:Host {id: $host_id})-[:RUNS]->(s:Service)-[:EXPOSES]->(v:VulnerabilityTechnique)
        OPTIONAL MATCH (v)-[:EXPLOITED_BY]->(a:Ability)
        RETURN v, collect(a) as exploits
        """
        
        results = self.ckg.execute_query(query, {'host_id': host_id})
        
        vulnerabilities = []
        for result in results:
            vuln = result.get('v', {})
            exploits = result.get('exploits', [])
            
            vulnerabilities.append({
                'id': vuln.get('id'),
                'cve_id': vuln.get('cve_id'),
                'cvss_score': vuln.get('cvss_score', 0.0),
                'exploit_count': len(exploits),
                'exploits': exploits
            })
        
        return vulnerabilities
    
    def explain_invalid_action(self, action: Dict[str, Any], current_host: str) -> str:
        """
        Generate human-readable explanation for why an action is invalid
        
        Args:
            action: Action metadata
            current_host: Current host ID
        
        Returns:
            Explanation string
        """
        action_type = action.get('type', 'unknown')
        target = action.get('target')
        
        if action_type == 'local':
            host = self.state.get_host_by_id(current_host)
            if not host or not host.owned:
                return f"Cannot execute local action: Host {current_host} is not owned"
        
        elif action_type == 'remote':
            if not target:
                return "Remote action requires a target"
            
            if not self.state.can_reach(current_host, target):
                return f"Cannot reach {target} from {current_host}"
            
            if action.get('requires_cred') and not self.state.has_credential_for(target):
                return f"Action requires credentials for {target}, but none available"
            
            target_obj = self.state.get_host_by_id(target)
            if target_obj and target_obj.owned:
                return f"Target {target} is already owned"
        
        elif action_type == 'connect':
            if not target:
                return "Connect action requires a target"
            
            target_obj = self.state.get_host_by_id(target)
            if not target_obj or not target_obj.owned:
                return f"Cannot connect to {target}: not owned"
            
            if not self.state.can_reach(current_host, target):
                return f"No network path from {current_host} to {target}"
        
        return "Unknown reason"
    
    def get_recommended_actions(
        self,
        action_metadata: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Tuple[int, Dict[str, Any], float]]:
        """
        Get top-K recommended actions based on masking + priorities
        
        Args:
            action_metadata: Metadata for all actions
            top_k: Number of recommendations
        
        Returns:
            List of (action_id, action_data, priority_score) tuples
        """
        valid_mask = self.get_valid_actions(len(action_metadata), action_metadata)
        priorities = self.get_action_priorities(action_metadata, valid_mask)
        
        # Get valid actions with priorities
        recommendations = []
        for i, (valid, priority) in enumerate(zip(valid_mask, priorities)):
            if valid > 0:
                recommendations.append((i, action_metadata[i], priority))
        
        # Sort by priority (descending)
        recommendations.sort(key=lambda x: x[2], reverse=True)
        
        return recommendations[:top_k]


if __name__ == "__main__":
    # Test action masker
    from .ckg_manager import CKGManager
    from ..environment.state_manager import StateManager
    
    logger.info("Testing ActionMasker...")
    
    # Create mock state
    state = StateManager()
    state.add_host("client")
    state.mark_owned("client", privilege="admin")
    state.current_host = "client"
    
    state.add_host("web-01")
    state.mark_discovered("web-01")
    state.add_connection("client", "web-01")
    
    # Create mock CKG (disconnected for testing)
    ckg = CKGManager()
    
    masker = ActionMasker(ckg, state)
    
    # Mock action space
    actions = [
        {'id': 0, 'type': 'local', 'tool': 'scan', 'target': None},
        {'id': 1, 'type': 'remote', 'tool': 'nmap', 'target': 'web-01'},
        {'id': 2, 'type': 'remote', 'tool': 'exploit', 'target': 'web-01'},
        {'id': 3, 'type': 'remote', 'tool': 'exploit', 'target': 'db-01'},  # Not reachable
        {'id': 4, 'type': 'connect', 'tool': 'ssh', 'target': 'web-01'},  # Not owned
    ]
    
    # Get valid actions
    mask = masker.get_valid_actions(len(actions), actions)
    print("\n=== Action Validity ===")
    for i, (action, valid) in enumerate(zip(actions, mask)):
        status = "VALID" if valid else "INVALID"
        print(f"{i}. {action['type']}:{action['tool']} -> {action.get('target', 'N/A')}: {status}")
        if not valid:
            explanation = masker.explain_invalid_action(action, "client")
            print(f"   Reason: {explanation}")
    
    # Get priorities
    priorities = masker.get_action_priorities(actions, mask)
    print("\n=== Action Priorities ===")
    for i, (action, priority) in enumerate(zip(actions, priorities)):
        if mask[i]:
            print(f"{i}. {action['type']}:{action['tool']}: priority={priority:.3f}")
    
    # Get recommendations
    recs = masker.get_recommended_actions(actions, top_k=3)
    print("\n=== Top Recommendations ===")
    for i, (action_id, action, priority) in enumerate(recs, 1):
        print(f"{i}. Action {action_id} - {action['type']}:{action['tool']}: {priority:.3f}")
    
    logger.info("Test completed!")
