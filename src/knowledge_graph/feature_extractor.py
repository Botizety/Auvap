"""
Feature Extractor for CKG

Extracts per-action features from the Knowledge Graph to inform agent decisions.
Features include:
- CVSS scores (exploitability, impact)
- Action cost (time/resources)
- Noise level (detection probability)
- Credential requirements
- Success probability estimates
- Target value

These features are used by both Manager and Worker agents to make informed decisions.
"""

from typing import List, Dict, Any, Optional
from loguru import logger
import numpy as np

from .ckg_manager import CKGManager
from ..environment.state_manager import StateManager


class FeatureExtractor:
    """
    Extracts features for actions based on CKG state
    
    Features are used to augment the observation space with domain knowledge,
    helping agents learn faster by encoding:
    - Which actions are high-value (CVSS, target value)
    - Which actions are risky (noise, cost)
    - Which actions are likely to succeed (success rate, credentials)
    """
    
    # Feature dimension (per action)
    FEATURE_DIM = 10
    
    def __init__(self, ckg_manager: CKGManager, state_manager: StateManager):
        """
        Initialize feature extractor
        
        Args:
            ckg_manager: CKG manager for graph queries
            state_manager: State manager for current episode state
        """
        self.ckg = ckg_manager
        self.state = state_manager
        
        logger.info("FeatureExtractor initialized")
    
    def extract_action_features(
        self,
        action: Dict[str, Any],
        current_host: str
    ) -> np.ndarray:
        """
        Extract feature vector for a single action
        
        Args:
            action: Action metadata
            current_host: Current host ID
        
        Returns:
            Feature vector of shape (FEATURE_DIM,)
        """
        features = np.zeros(self.FEATURE_DIM, dtype=np.float32)
        
        # Feature 0: Action type (one-hot encoded)
        action_type = action.get('type', 'unknown')
        if action_type == 'local':
            features[0] = 1.0
        elif action_type == 'remote':
            features[0] = 0.5
        elif action_type == 'connect':
            features[0] = 0.0
        
        # Feature 1: Cost (normalized 0-1)
        cost = action.get('cost', 1.0)
        features[1] = min(cost / 10.0, 1.0)  # Assume max cost is 10
        
        # Feature 2: Noise level (0-1)
        features[2] = action.get('noise_level', 0.5)
        
        # Feature 3: Requires credential (binary)
        features[3] = 1.0 if action.get('requires_cred', False) else 0.0
        
        # Feature 4: Has credential (binary)
        target = action.get('target')
        if target and features[3] > 0:
            features[4] = 1.0 if self.state.has_credential_for(target) else 0.0
        
        # Feature 5: Target value (normalized 0-1)
        if target:
            host = self.state.get_host_by_id(target)
            if host:
                features[5] = min(host.value / 100.0, 1.0)
        
        # Feature 6: Target already owned (binary)
        if target:
            host = self.state.get_host_by_id(target)
            features[6] = 1.0 if (host and host.owned) else 0.0
        
        # Feature 7: CVSS score (from CKG, normalized 0-1)
        cvss = self._get_max_cvss_for_target(target) if target else 0.0
        features[7] = cvss / 10.0  # CVSS is 0-10 scale
        
        # Feature 8: Number of exploitable vulns (normalized)
        vuln_count = self._get_vuln_count(target) if target else 0
        features[8] = min(vuln_count / 5.0, 1.0)  # Normalize by max expected
        
        # Feature 9: Distance to goal (heuristic)
        features[9] = self._compute_goal_distance(target) if target else 1.0
        
        return features
    
    def extract_action_batch_features(
        self,
        actions: List[Dict[str, Any]],
        current_host: str
    ) -> np.ndarray:
        """
        Extract features for multiple actions at once
        
        Args:
            actions: List of action metadata
            current_host: Current host ID
        
        Returns:
            Feature matrix of shape (len(actions), FEATURE_DIM)
        """
        features = np.zeros((len(actions), self.FEATURE_DIM), dtype=np.float32)
        
        for i, action in enumerate(actions):
            features[i] = self.extract_action_features(action, current_host)
        
        return features
    
    def _get_max_cvss_for_target(self, target: Optional[str]) -> float:
        """
        Get maximum CVSS score for vulnerabilities on target host
        
        Args:
            target: Target host ID
        
        Returns:
            Maximum CVSS score (0-10)
        """
        if not target or not self.ckg.connected:
            return 0.0
        
        # Query CKG for vulnerabilities
        query = """
        MATCH (h:Host {id: $host_id})-[:RUNS]->(s:Service)-[:EXPOSES]->(v:VulnerabilityTechnique)
        RETURN max(v.cvss_score) as max_cvss
        """
        
        results = self.ckg.execute_query(query, {'host_id': target})
        
        if results and results[0].get('max_cvss'):
            return float(results[0]['max_cvss'])
        
        return 0.0
    
    def _get_vuln_count(self, target: Optional[str]) -> int:
        """
        Get count of exploitable vulnerabilities on target
        
        Args:
            target: Target host ID
        
        Returns:
            Number of vulnerabilities
        """
        if not target:
            return 0
        
        # Use state manager for quick check
        host = self.state.get_host_by_id(target)
        if host:
            return len(host.vulnerabilities)
        
        # Otherwise query CKG
        if not self.ckg.connected:
            return 0
        
        query = """
        MATCH (h:Host {id: $host_id})-[:RUNS]->(s:Service)-[:EXPOSES]->(v:VulnerabilityTechnique)
        RETURN count(v) as vuln_count
        """
        
        results = self.ckg.execute_query(query, {'host_id': target})
        
        if results:
            return int(results[0].get('vuln_count', 0))
        
        return 0
    
    def _compute_goal_distance(self, target: Optional[str]) -> float:
        """
        Compute heuristic distance to goal
        
        A simple heuristic based on:
        - Whether target is a goal host (distance = 0)
        - Number of hops to nearest goal (if known)
        - Default distance otherwise
        
        Args:
            target: Target host ID
        
        Returns:
            Normalized distance (0=goal, 1=far from goal)
        """
        if not target:
            return 1.0
        
        # Check if target is a goal
        if target in self.state.goal_hosts:
            return 0.0
        
        # Check if target is already compromised goal
        if target in self.state.compromised_goals:
            return 0.1
        
        # Simple heuristic: distance based on ownership
        host = self.state.get_host_by_id(target)
        if host:
            if host.owned:
                return 0.3  # Already owned, not critical
            elif host.discovered:
                return 0.6  # Discovered, might lead to goal
            else:
                return 0.9  # Undiscovered
        
        return 1.0  # Unknown
    
    def get_feature_names(self) -> List[str]:
        """
        Get human-readable names for features
        
        Returns:
            List of feature names
        """
        return [
            "action_type",           # 0: local/remote/connect
            "cost",                  # 1: resource cost
            "noise_level",           # 2: detection probability
            "requires_credential",   # 3: needs auth
            "has_credential",        # 4: credential available
            "target_value",          # 5: target worth
            "target_owned",          # 6: already compromised
            "max_cvss_score",        # 7: vulnerability severity
            "vulnerability_count",   # 8: number of vulns
            "goal_distance",         # 9: heuristic distance to goal
        ]
    
    def explain_features(
        self,
        features: np.ndarray,
        action: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable explanation of feature values
        
        Args:
            features: Feature vector
            action: Action metadata
        
        Returns:
            Explanation string
        """
        names = self.get_feature_names()
        
        lines = [f"Features for action {action.get('id', '?')}:"]
        lines.append(f"  Type: {action.get('type')} - {action.get('tool')}")
        lines.append(f"  Target: {action.get('target', 'N/A')}")
        lines.append("")
        
        for i, (name, value) in enumerate(zip(names, features)):
            # Format based on feature type
            if i in [0, 3, 4, 6]:  # Binary/categorical
                lines.append(f"  {name}: {'Yes' if value > 0.5 else 'No'}")
            else:  # Continuous
                lines.append(f"  {name}: {value:.3f}")
        
        return "\n".join(lines)
    
    def compute_action_value_estimate(
        self,
        features: np.ndarray
    ) -> float:
        """
        Compute a simple heuristic value estimate for an action
        Based on feature values (not learned, just heuristic)
        
        Args:
            features: Feature vector
        
        Returns:
            Estimated value (0-1)
        """
        # Simple weighted sum of positive features
        value = 0.0
        
        # High CVSS = good
        value += features[7] * 0.3
        
        # High target value = good
        value += features[5] * 0.3
        
        # Low cost = good
        value += (1.0 - features[1]) * 0.1
        
        # Low noise = good
        value += (1.0 - features[2]) * 0.1
        
        # Close to goal = good
        value += (1.0 - features[9]) * 0.2
        
        return min(value, 1.0)


if __name__ == "__main__":
    # Test feature extractor
    from .ckg_manager import CKGManager
    from ..environment.state_manager import StateManager
    
    logger.info("Testing FeatureExtractor...")
    
    # Create mock state
    state = StateManager()
    state.add_host("client", value=10)
    state.mark_owned("client", privilege="admin")
    state.current_host = "client"
    
    state.add_host("web-01", value=50)
    state.mark_discovered("web-01")
    state.add_connection("client", "web-01")
    state.add_service("web-01", "http", ["CVE-2021-1234"])
    
    # Create mock CKG
    ckg = CKGManager()
    
    extractor = FeatureExtractor(ckg, state)
    
    # Mock action
    action = {
        'id': 1,
        'type': 'remote',
        'tool': 'exploit',
        'target': 'web-01',
        'cost': 2.0,
        'noise_level': 0.7,
        'requires_cred': False
    }
    
    # Extract features
    features = extractor.extract_action_features(action, "client")
    
    print("\n=== Feature Vector ===")
    print(features)
    
    print("\n=== Feature Explanation ===")
    print(extractor.explain_features(features, action))
    
    print("\n=== Value Estimate ===")
    value = extractor.compute_action_value_estimate(features)
    print(f"Estimated action value: {value:.3f}")
    
    print("\n=== Feature Names ===")
    for i, name in enumerate(extractor.get_feature_names()):
        print(f"{i}: {name}")
    
    logger.info("Test completed!")
