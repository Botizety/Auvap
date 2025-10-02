"""
Manager Agent for Hierarchical AUVAP

The Manager is the high-level strategic agent that:
1. Selects sub-goals (reconnaissance, exploitation, privilege escalation, pivoting)
2. Chooses target hosts for each sub-goal
3. Assigns action budgets (e.g., "attempt exploit on web-01 with 6 actions max")
4. Monitors Worker progress and decides when to switch goals
5. Receives long-horizon rewards based on episode success

Manager observation space:
- Network topology summary (owned, discovered, unexplored)
- Current penetration phase  
- Recent Worker success/failure
- Goal progress

Manager action space:
- Sub-goal selection: {reconnaissance, web_exploitation, privilege_escalation, pivoting}
- Target selection: Which host to focus on
- Budget: Number of actions to allocate to Worker
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
from loguru import logger


class SubGoal(Enum):
    """High-level sub-goals the Manager can select"""
    RECONNAISSANCE = "reconnaissance"  # Discover network topology
    WEB_EXPLOITATION = "web_exploitation"  # Exploit web services
    PRIVILEGE_ESCALATION = "privilege_escalation"  # Escalate privileges on owned hosts
    PIVOTING = "pivoting"  # Lateral movement to new hosts


@dataclass
class ManagerDecision:
    """Manager's decision for the Worker"""
    subgoal: SubGoal
    target_host: Optional[str]
    budget: int  # Maximum actions Worker can take
    stop_condition: str  # When to stop (e.g., "session_obtained", "budget_exhausted")
    priority: float = 0.5  # Priority score (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'subgoal': self.subgoal.value,
            'target': self.target_host,
            'budget': self.budget,
            'stop_condition': self.stop_condition,
            'priority': self.priority
        }
    
    def __repr__(self) -> str:
        return f"Manager: {self.subgoal.value} on {self.target_host}, budget={self.budget}"


class ManagerAgent:
    """
    High-level Manager agent for hierarchical RL
    
    Trained with PPO to learn:
    - When to switch between sub-goals
    - Which targets to prioritize
    - How much budget to allocate
    
    Receives rewards based on:
    - Worker success in achieving sub-goal
    - Episode completion (reaching goal hosts)
    - Efficiency (fewer steps to goal)
    """
    
    # Manager observation dimension (13 base + 4 current subgoal + 4 success rates = 21)
    OBS_DIM = 21
    
    # Manager action space: 4 subgoals × dynamic target selection
    # For simplicity, we'll use a discrete action space mapping to (subgoal, target_idx)
    NUM_SUBGOALS = len(SubGoal)
    
    def __init__(
        self,
        max_hosts: int = 10,
        default_budget: int = 6,
        budget_range: Tuple[int, int] = (3, 10)
    ):
        """
        Initialize Manager agent
        
        Args:
            max_hosts: Maximum number of hosts in network
            default_budget: Default action budget for Worker
            budget_range: (min, max) budget range
        """
        self.max_hosts = max_hosts
        self.default_budget = default_budget
        self.budget_range = budget_range
        
        # Decision history
        self.decision_history: List[ManagerDecision] = []
        self.current_decision: Optional[ManagerDecision] = None
        
        # Performance tracking
        self.subgoal_success_rates: Dict[SubGoal, List[bool]] = {
            sg: [] for sg in SubGoal
        }
        
        logger.info(f"ManagerAgent initialized (max_hosts={max_hosts}, budget={default_budget})")
    
    def get_observation_space_size(self) -> int:
        """Get observation space dimension"""
        return self.OBS_DIM
    
    def get_action_space_size(self) -> int:
        """
        Get action space size
        
        Action space is: NUM_SUBGOALS × max_hosts (subgoal-target pairs)
        """
        return self.NUM_SUBGOALS * self.max_hosts
    
    def build_observation(
        self,
        state_manager,
        worker_feedback: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Build Manager observation from current state
        
        Args:
            state_manager: StateManager with current episode state
            worker_feedback: Optional feedback from Worker's last execution
        
        Returns:
            Observation vector of shape (OBS_DIM,)
        """
        obs = np.zeros(self.OBS_DIM, dtype=np.float32)
        
        # Network state summary (10 features)
        owned_hosts = state_manager.get_owned_hosts()
        discovered_hosts = state_manager.get_discovered_hosts()
        unexplored = state_manager.get_unexplored_hosts()
        
        obs[0] = len(owned_hosts) / self.max_hosts
        obs[1] = len(discovered_hosts) / self.max_hosts
        obs[2] = len(unexplored) / self.max_hosts
        
        # Goal progress (2 features)
        if state_manager.goal_hosts:
            obs[3] = len(state_manager.compromised_goals) / len(state_manager.goal_hosts)
            obs[4] = 1.0 if len(state_manager.compromised_goals) == len(state_manager.goal_hosts) else 0.0
        
        # Penetration phase (4 features, one-hot)
        phase = state_manager.get_penetration_phase()
        phase_idx = {
            'reconnaissance': 0,
            'initial_access': 1,
            'lateral_movement': 2,
            'privilege_escalation': 3,
            'goal_achieved': 3
        }.get(phase, 0)
        obs[5 + phase_idx] = 1.0
        
        # Worker feedback (4 features)
        if worker_feedback:
            obs[9] = worker_feedback.get('success_rate', 0.5)
            obs[10] = worker_feedback.get('actions_used', 0) / 10.0
            obs[11] = worker_feedback.get('reward', 0.0) / 10.0
            obs[12] = 1.0 if worker_feedback.get('subgoal_achieved', False) else 0.0
        
        # Current decision context (4 features)
        if self.current_decision:
            subgoal_idx = list(SubGoal).index(self.current_decision.subgoal)
            obs[13 + subgoal_idx] = 1.0
        
        # Historical success rates (4 features)
        for i, subgoal in enumerate(SubGoal):
            success_history = self.subgoal_success_rates[subgoal]
            if success_history:
                obs[17 + i] = sum(success_history) / len(success_history)
            else:
                obs[17 + i] = 0.5  # Unknown, neutral
        
        return obs
    
    def action_to_decision(
        self,
        action: int,
        state_manager,
        adaptive_budget: bool = True
    ) -> ManagerDecision:
        """
        Convert discrete action to Manager decision
        
        Args:
            action: Discrete action ID
            state_manager: Current state
            adaptive_budget: If True, adapt budget based on state
        
        Returns:
            ManagerDecision object
        """
        # Decode action to (subgoal_idx, target_idx)
        subgoal_idx = action // self.max_hosts
        target_idx = action % self.max_hosts
        
        # Get subgoal
        subgoal = list(SubGoal)[subgoal_idx % self.NUM_SUBGOALS]
        
        # Get target host
        target_host = None
        if subgoal == SubGoal.RECONNAISSANCE:
            # Target unexplored or undiscovered hosts
            unexplored = state_manager.get_unexplored_hosts()
            if unexplored and target_idx < len(unexplored):
                target_host = unexplored[target_idx]
        
        elif subgoal == SubGoal.WEB_EXPLOITATION:
            # Target discovered but not owned hosts
            discovered = state_manager.get_discovered_hosts()
            owned = state_manager.get_owned_hosts()
            targets = [h for h in discovered if h not in owned]
            if targets and target_idx < len(targets):
                target_host = targets[target_idx]
        
        elif subgoal == SubGoal.PRIVILEGE_ESCALATION:
            # Target owned hosts with low privilege
            owned = state_manager.get_owned_hosts()
            targets = [h for h in owned if state_manager.get_privilege(h) in ['user', 'none']]
            if targets and target_idx < len(targets):
                target_host = targets[target_idx]
        
        elif subgoal == SubGoal.PIVOTING:
            # Target hosts reachable from owned hosts
            owned = state_manager.get_owned_hosts()
            targets = []
            for owned_host in owned:
                reachable = state_manager.get_reachable_hosts(owned_host)
                targets.extend([h for h in reachable if h not in owned])
            targets = list(set(targets))  # Remove duplicates
            if targets and target_idx < len(targets):
                target_host = targets[target_idx]
        
        # Determine budget
        if adaptive_budget:
            budget = self._compute_adaptive_budget(subgoal, target_host, state_manager)
        else:
            budget = self.default_budget
        
        # Determine stop condition
        stop_condition = self._get_stop_condition(subgoal)
        
        decision = ManagerDecision(
            subgoal=subgoal,
            target_host=target_host,
            budget=budget,
            stop_condition=stop_condition,
            priority=0.5
        )
        
        self.current_decision = decision
        self.decision_history.append(decision)
        
        logger.info(f"Manager decision: {decision}")
        
        return decision
    
    def _compute_adaptive_budget(
        self,
        subgoal: SubGoal,
        target: Optional[str],
        state_manager
    ) -> int:
        """
        Compute adaptive budget based on subgoal and state
        
        Args:
            subgoal: Selected subgoal
            target: Target host
            state_manager: Current state
        
        Returns:
            Budget (number of actions)
        """
        base_budget = self.default_budget
        
        # Adjust based on subgoal
        if subgoal == SubGoal.RECONNAISSANCE:
            # Reconnaissance is cheap, lower budget
            base_budget = max(self.budget_range[0], base_budget - 2)
        
        elif subgoal == SubGoal.WEB_EXPLOITATION:
            # Exploitation may need multiple attempts
            base_budget = min(self.budget_range[1], base_budget + 2)
        
        elif subgoal == SubGoal.PRIVILEGE_ESCALATION:
            # Privilege escalation is targeted
            base_budget = base_budget
        
        elif subgoal == SubGoal.PIVOTING:
            # Pivoting needs exploration
            base_budget = min(self.budget_range[1], base_budget + 1)
        
        # Adjust based on target value
        if target:
            host = state_manager.get_host_by_id(target)
            if host and host.value > 50:
                base_budget += 1  # High-value targets get more budget
        
        # Clamp to budget range
        return np.clip(base_budget, self.budget_range[0], self.budget_range[1])
    
    def _get_stop_condition(self, subgoal: SubGoal) -> str:
        """
        Get stop condition for subgoal
        
        Args:
            subgoal: Selected subgoal
        
        Returns:
            Stop condition string
        """
        conditions = {
            SubGoal.RECONNAISSANCE: "hosts_discovered",
            SubGoal.WEB_EXPLOITATION: "session_obtained",
            SubGoal.PRIVILEGE_ESCALATION: "privilege_escalated",
            SubGoal.PIVOTING: "lateral_movement_success"
        }
        
        return conditions.get(subgoal, "budget_exhausted")
    
    def record_worker_feedback(
        self,
        feedback: Dict[str, Any]
    ):
        """
        Record feedback from Worker execution
        
        Args:
            feedback: Dictionary with Worker performance metrics
        """
        if not self.current_decision:
            return
        
        subgoal = self.current_decision.subgoal
        success = feedback.get('subgoal_achieved', False)
        
        self.subgoal_success_rates[subgoal].append(success)
        
        logger.debug(f"Worker feedback for {subgoal.value}: success={success}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Manager performance statistics"""
        stats = {
            'total_decisions': len(self.decision_history),
            'subgoal_distribution': {},
            'subgoal_success_rates': {}
        }
        
        # Count decisions per subgoal
        for decision in self.decision_history:
            sg = decision.subgoal.value
            stats['subgoal_distribution'][sg] = stats['subgoal_distribution'].get(sg, 0) + 1
        
        # Compute success rates
        for subgoal, successes in self.subgoal_success_rates.items():
            if successes:
                stats['subgoal_success_rates'][subgoal.value] = sum(successes) / len(successes)
            else:
                stats['subgoal_success_rates'][subgoal.value] = 0.0
        
        return stats


if __name__ == "__main__":
    # Test Manager agent
    from ..environment.state_manager import StateManager
    
    logger.info("Testing ManagerAgent...")
    
    # Create mock state
    state = StateManager()
    state.add_host("client", value=10)
    state.mark_owned("client", privilege="admin")
    state.current_host = "client"
    
    state.add_host("web-01", value=50)
    state.mark_discovered("web-01")
    state.add_connection("client", "web-01")
    
    state.add_host("db-01", value=100)
    state.goal_hosts = {"db-01"}
    
    # Create Manager
    manager = ManagerAgent(max_hosts=5, default_budget=6)
    
    # Build observation
    obs = manager.build_observation(state)
    print(f"\n=== Manager Observation ===")
    print(f"Shape: {obs.shape}")
    print(f"Values: {obs}")
    
    # Make decision
    action = 1 * 5 + 0  # Web exploitation on first discovered target
    decision = manager.action_to_decision(action, state)
    print(f"\n=== Manager Decision ===")
    print(decision)
    print(decision.to_dict())
    
    # Simulate Worker feedback
    feedback = {
        'success_rate': 0.6,
        'actions_used': 4,
        'reward': 5.0,
        'subgoal_achieved': True
    }
    manager.record_worker_feedback(feedback)
    
    # Get statistics
    print(f"\n=== Manager Statistics ===")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    logger.info("Test completed!")
