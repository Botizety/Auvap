"""
Worker Agent for Hierarchical AUVAP

The Worker is the low-level tactical agent that:
1. Receives sub-goals and budgets from Manager
2. Executes CyberBattleSim actions (scan, exploit, connect)
3. Uses CKG action masking to filter valid actions
4. Uses CKG features to guide action selection
5. Reports progress back to Manager

Worker observation space:
- CBS environment observation
- CKG per-action features
- Current sub-goal and budget remaining
- Action validity mask

Worker action space:
- CyberBattleSim action space (masked by CKG)
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from loguru import logger

from .manager import ManagerDecision, SubGoal


class WorkerAgent:
    """
    Low-level Worker agent for hierarchical RL
    
    Trained with PPO/DQN to learn:
    - Which specific actions to take given a sub-goal
    - How to utilize CKG features for action selection
    - When to stop (subgoal achieved or budget exhausted)
    
    Receives rewards based on:
    - Step rewards (DynPen-style: result - cost)
    - Sub-goal achievement bonus
    - Action validity (penalty for invalid actions)
    """
    
    def __init__(
        self,
        cbs_obs_dim: int,
        ckg_feature_dim: int = 10,
        max_actions: int = 100
    ):
        """
        Initialize Worker agent
        
        Args:
            cbs_obs_dim: CyberBattleSim observation dimension
            ckg_feature_dim: CKG feature dimension per action
            max_actions: Maximum number of possible actions
        """
        self.cbs_obs_dim = cbs_obs_dim
        self.ckg_feature_dim = ckg_feature_dim
        self.max_actions = max_actions
        
        # Current task from Manager
        self.current_task: Optional[ManagerDecision] = None
        self.budget_remaining = 0
        self.actions_taken = 0
        
        # Performance tracking
        self.step_rewards: List[float] = []
        self.actions_success: List[bool] = []
        
        logger.info(f"WorkerAgent initialized (obs={cbs_obs_dim}, features={ckg_feature_dim})")
    
    def get_observation_space_size(self) -> int:
        """
        Get observation space dimension
        
        Observation = CBS obs + task encoding + budget + CKG features
        """
        task_encoding = 10  # Sub-goal one-hot (4) + budget (1) + target encoding (5)
        return self.cbs_obs_dim + task_encoding
    
    def get_action_space_size(self) -> int:
        """Get action space size (same as CBS environment)"""
        return self.max_actions
    
    def set_task(self, decision: ManagerDecision):
        """
        Set new task from Manager
        
        Args:
            decision: Manager's decision
        """
        self.current_task = decision
        self.budget_remaining = decision.budget
        self.actions_taken = 0
        self.step_rewards = []
        self.actions_success = []
        
        logger.info(f"Worker received task: {decision}")
    
    def build_observation(
        self,
        cbs_obs: np.ndarray,
        ckg_features: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Build Worker observation from CBS obs + task context
        
        Args:
            cbs_obs: CyberBattleSim observation
            ckg_features: Optional CKG features (not included in obs, used separately)
        
        Returns:
            Observation vector
        """
        # Start with CBS observation
        obs_parts = [cbs_obs.flatten()]
        
        # Add task encoding
        task_encoding = np.zeros(10, dtype=np.float32)
        
        if self.current_task:
            # Sub-goal one-hot (indices 0-3)
            subgoal_idx = list(SubGoal).index(self.current_task.subgoal)
            task_encoding[subgoal_idx] = 1.0
            
            # Budget remaining (normalized, index 4)
            if self.current_task.budget > 0:
                task_encoding[4] = self.budget_remaining / self.current_task.budget
            
            # Target host encoding (simple hash, indices 5-9)
            if self.current_task.target_host:
                # Simple encoding: hash target name to 5 features
                target_hash = hash(self.current_task.target_host) % 32
                for i in range(5):
                    if target_hash & (1 << i):
                        task_encoding[5 + i] = 1.0
        
        obs_parts.append(task_encoding)
        
        # Concatenate
        full_obs = np.concatenate(obs_parts)
        
        return full_obs
    
    def should_stop(self, feedback: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if Worker should stop execution
        
        Args:
            feedback: Feedback from last action
        
        Returns:
            (should_stop, reason)
        """
        if not self.current_task:
            return True, "no_task"
        
        # Budget exhausted
        if self.budget_remaining <= 0:
            return True, "budget_exhausted"
        
        # Stop condition met
        stop_condition = self.current_task.stop_condition
        
        if stop_condition == "session_obtained":
            if feedback.get('new_host_owned', False):
                return True, "session_obtained"
        
        elif stop_condition == "hosts_discovered":
            if feedback.get('new_hosts_discovered', 0) > 0:
                return True, "hosts_discovered"
        
        elif stop_condition == "privilege_escalated":
            if feedback.get('privilege_escalated', False):
                return True, "privilege_escalated"
        
        elif stop_condition == "lateral_movement_success":
            if feedback.get('lateral_movement', False):
                return True, "lateral_movement_success"
        
        return False, "continue"
    
    def record_action(self, reward: float, success: bool):
        """
        Record action result
        
        Args:
            reward: Step reward received
            success: Whether action was successful
        """
        self.step_rewards.append(reward)
        self.actions_success.append(success)
        self.actions_taken += 1
        self.budget_remaining -= 1
    
    def get_feedback(self) -> Dict[str, Any]:
        """
        Generate feedback for Manager
        
        Returns:
            Dictionary with Worker performance metrics
        """
        if not self.step_rewards:
            return {
                'success_rate': 0.0,
                'actions_used': 0,
                'reward': 0.0,
                'subgoal_achieved': False
            }
        
        return {
            'success_rate': sum(self.actions_success) / len(self.actions_success),
            'actions_used': self.actions_taken,
            'reward': sum(self.step_rewards),
            'avg_reward': np.mean(self.step_rewards),
            'subgoal_achieved': self.check_subgoal_achieved()
        }
    
    def check_subgoal_achieved(self) -> bool:
        """
        Check if sub-goal was achieved
        
        This is a simplified check; in practice, would query state manager
        """
        if not self.current_task:
            return False
        
        # Simple heuristic: if we got positive cumulative reward and some successes
        if self.step_rewards and self.actions_success:
            total_reward = sum(self.step_rewards)
            success_rate = sum(self.actions_success) / len(self.actions_success)
            
            # Heuristic thresholds
            return total_reward > 0 and success_rate > 0.5
        
        return False
    
    def reset(self):
        """Reset Worker for new episode"""
        self.current_task = None
        self.budget_remaining = 0
        self.actions_taken = 0
        self.step_rewards = []
        self.actions_success = []


if __name__ == "__main__":
    # Test Worker agent
    from .manager import ManagerAgent, ManagerDecision, SubGoal
    
    logger.info("Testing WorkerAgent...")
    
    # Create Worker
    worker = WorkerAgent(cbs_obs_dim=50, ckg_feature_dim=10, max_actions=100)
    
    # Create mock task from Manager
    task = ManagerDecision(
        subgoal=SubGoal.WEB_EXPLOITATION,
        target_host="web-01",
        budget=6,
        stop_condition="session_obtained"
    )
    
    worker.set_task(task)
    
    # Mock CBS observation
    cbs_obs = np.random.rand(50).astype(np.float32)
    
    # Build Worker observation
    obs = worker.build_observation(cbs_obs)
    print(f"\n=== Worker Observation ===")
    print(f"Shape: {obs.shape}")
    print(f"Expected: {worker.get_observation_space_size()}")
    
    # Simulate some actions
    print(f"\n=== Simulating Worker Actions ===")
    for i in range(3):
        reward = np.random.uniform(-1, 2)
        success = reward > 0
        worker.record_action(reward, success)
        print(f"Action {i+1}: reward={reward:.2f}, success={success}, budget_remaining={worker.budget_remaining}")
        
        # Check stop condition
        feedback = {'new_host_owned': (i == 2)}  # Success on 3rd action
        should_stop, reason = worker.should_stop(feedback)
        if should_stop:
            print(f"Stopping: {reason}")
            break
    
    # Get feedback
    print(f"\n=== Worker Feedback ===")
    feedback = worker.get_feedback()
    for key, value in feedback.items():
        print(f"{key}: {value}")
    
    logger.info("Test completed!")
