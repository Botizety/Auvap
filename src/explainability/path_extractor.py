"""
Explanation Path Extractor

Extracts reasoning paths from the CKG to explain agent decisions:
- Why was this action selected?
- What knowledge supported this decision?
- What were the preconditions?
- What was the expected outcome?

Example path:
Host(web-01) -[:RUNS]-> Service(http:80) -[:EXPOSES]-> Vuln(CVE-2021-1234) 
  -[:EXPLOITED_BY]-> Ability(metasploit) => SELECTED because CVSS=7.5, low_noise
"""

from typing import List, Dict, Any, Optional
from loguru import logger


class ExplanationPathExtractor:
    """
    Extract explanation paths from CKG for agent decisions
    
    Provides interpretability by showing the knowledge graph reasoning
    that led to action selection.
    """
    
    def __init__(self, ckg_manager):
        """
        Initialize path extractor
        
        Args:
            ckg_manager: CKG manager for graph queries
        """
        self.ckg = ckg_manager
        logger.info("ExplanationPathExtractor initialized")
    
    def extract_action_explanation(
        self,
        action: Dict[str, Any],
        state_manager
    ) -> Dict[str, Any]:
        """
        Extract explanation for why an action was selected
        
        Args:
            action: Action metadata
            state_manager: Current state
        
        Returns:
            Explanation dictionary with paths and reasoning
        """
        explanation = {
            'action': action,
            'reasoning_paths': [],
            'preconditions': [],
            'expected_outcome': '',
            'risk_assessment': {}
        }
        
        action_type = action.get('type', 'unknown')
        target = action.get('target')
        tool = action.get('tool', 'unknown')
        
        # Extract reasoning based on action type
        if action_type == 'remote' and target:
            # Find path: Current -> Target with vulnerabilities
            paths = self._find_exploit_paths(target)
            explanation['reasoning_paths'] = paths
            
            # Preconditions
            explanation['preconditions'] = [
                f"Host {target} is reachable",
                f"Service vulnerable to {tool}",
            ]
            
            # Expected outcome
            explanation['expected_outcome'] = f"Compromise {target} via {tool}"
            
            # Risk assessment
            explanation['risk_assessment'] = {
                'noise_level': action.get('noise_level', 0.5),
                'success_probability': action.get('success_rate', 0.7),
                'cost': action.get('cost', 1.0)
            }
        
        elif action_type == 'local':
            explanation['reasoning_paths'] = [f"Execute {tool} on current host"]
            explanation['preconditions'] = ["Host is owned"]
            explanation['expected_outcome'] = "Discover local resources or escalate privilege"
        
        elif action_type == 'connect':
            explanation['reasoning_paths'] = [f"Move to owned host {target}"]
            explanation['preconditions'] = [f"Host {target} is owned", "Network path exists"]
            explanation['expected_outcome'] = f"Pivot to {target} for further exploitation"
        
        return explanation
    
    def _find_exploit_paths(self, target_host: str) -> List[str]:
        """
        Find exploitation paths to target host
        
        Args:
            target_host: Target host ID
        
        Returns:
            List of path descriptions
        """
        if not self.ckg.connected:
            return [f"Direct exploitation of {target_host} (CKG unavailable)"]
        
        # Query for vulnerability paths
        query = """
        MATCH path = (h:Host {id: $target})-[:RUNS]->(s:Service)-[:EXPOSES]->(v:VulnerabilityTechnique)
        OPTIONAL MATCH (v)-[:EXPLOITED_BY]->(a:Ability)
        RETURN 
            h.id as host,
            s.name as service,
            v.cve_id as cve,
            v.cvss_score as cvss,
            collect(a.tool_name) as exploits
        LIMIT 5
        """
        
        results = self.ckg.execute_query(query, {'target': target_host})
        
        paths = []
        for result in results:
            host = result.get('host', target_host)
            service = result.get('service', 'unknown')
            cve = result.get('cve', 'N/A')
            cvss = result.get('cvss', 0.0)
            exploits = result.get('exploits', [])
            
            exploit_str = ', '.join(exploits) if exploits else 'manual'
            path = f"{host} → Service({service}) → {cve} (CVSS={cvss:.1f}) → Exploit({exploit_str})"
            paths.append(path)
        
        return paths if paths else [f"Exploitation path to {target_host}"]
    
    def generate_decision_tree(
        self,
        manager_decision,
        worker_actions: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a decision tree showing Manager-Worker coordination
        
        Args:
            manager_decision: Manager's decision
            worker_actions: List of Worker actions taken
        
        Returns:
            Text-based decision tree
        """
        tree = []
        tree.append("Decision Tree:")
        tree.append(f"├─ Manager: {manager_decision.subgoal.value}")
        tree.append(f"│  ├─ Target: {manager_decision.target_host}")
        tree.append(f"│  ├─ Budget: {manager_decision.budget}")
        tree.append(f"│  └─ Stop Condition: {manager_decision.stop_condition}")
        tree.append(f"│")
        
        for i, action in enumerate(worker_actions):
            is_last = (i == len(worker_actions) - 1)
            prefix = "└─" if is_last else "├─"
            
            tree.append(f"{prefix} Worker Action {i+1}: {action.get('type')} - {action.get('tool')}")
            
            if not is_last:
                tree.append(f"│")
        
        return "\n".join(tree)
    
    def explain_failure(
        self,
        action: Dict[str, Any],
        error: str
    ) -> str:
        """
        Generate explanation for why an action failed
        
        Args:
            action: Failed action
            error: Error message
        
        Returns:
            Human-readable explanation
        """
        explanation_parts = [
            f"Action {action.get('type')} failed:",
            f"  Tool: {action.get('tool')}",
            f"  Target: {action.get('target', 'N/A')}",
            f"  Error: {error}",
            "",
            "Possible reasons:",
        ]
        
        # Add contextual reasons based on action type
        action_type = action.get('type')
        if action_type == 'remote':
            explanation_parts.extend([
                "  - Target may not be reachable",
                "  - Service may not be vulnerable",
                "  - Credentials may be required",
                "  - Exploit may have failed (low success rate)"
            ])
        elif action_type == 'local':
            explanation_parts.extend([
                "  - Insufficient privileges",
                "  - Resource not available",
                "  - Tool not applicable to current OS"
            ])
        
        return "\n".join(explanation_parts)


if __name__ == "__main__":
    # Test explanation path extractor
    from ..knowledge_graph.ckg_manager import CKGManager
    from ..environment.state_manager import StateManager
    
    logger.info("Testing ExplanationPathExtractor...")
    
    # Create components
    ckg = CKGManager()
    state = StateManager()
    extractor = ExplanationPathExtractor(ckg)
    
    # Mock action
    action = {
        'id': 1,
        'type': 'remote',
        'tool': 'metasploit',
        'target': 'web-01',
        'cost': 2.0,
        'noise_level': 0.7
    }
    
    # Extract explanation
    explanation = extractor.extract_action_explanation(action, state)
    
    print("\n=== Action Explanation ===")
    print(f"Action: {explanation['action']['type']} - {explanation['action']['tool']}")
    print(f"\nReasoning Paths:")
    for path in explanation['reasoning_paths']:
        print(f"  {path}")
    print(f"\nPreconditions:")
    for pre in explanation['preconditions']:
        print(f"  • {pre}")
    print(f"\nExpected Outcome: {explanation['expected_outcome']}")
    print(f"\nRisk Assessment:")
    for key, value in explanation['risk_assessment'].items():
        print(f"  {key}: {value}")
    
    logger.info("Test completed!")
