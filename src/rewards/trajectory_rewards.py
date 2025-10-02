"""
Trajectory Reward Model

Implements preference-based trajectory rewards for long-horizon quality assessment.
This is trained separately using human preferences or heuristic quality metrics.

For now, implements a heuristic-based trajectory reward that considers:
- Efficiency (steps to goal)
- Coverage (hosts compromised)
- Stealth (noise level)
- Goal achievement
"""

from typing import List, Dict, Any
import numpy as np
from loguru import logger


class TrajectoryRewardModel:
    """
    Compute trajectory-level rewards for episode quality
    
    This provides long-horizon signals that complement step rewards:
    - Step rewards: immediate tactical feedback
    - Trajectory rewards: strategic episode quality
    """
    
    def __init__(
        self,
        efficiency_weight: float = 0.4,
        coverage_weight: float = 0.3,
        stealth_weight: float = 0.2,
        goal_weight: float = 0.1
    ):
        """
        Initialize trajectory reward model
        
        Args:
            efficiency_weight: Weight for efficiency metric
            coverage_weight: Weight for coverage metric
            stealth_weight: Weight for stealth metric
            goal_weight: Weight for goal achievement
        """
        self.efficiency_weight = efficiency_weight
        self.coverage_weight = coverage_weight
        self.stealth_weight = stealth_weight
        self.goal_weight = goal_weight
        
        # Normalize weights
        total = efficiency_weight + coverage_weight + stealth_weight + goal_weight
        self.efficiency_weight /= total
        self.coverage_weight /= total
        self.stealth_weight /= total
        self.goal_weight /= total
        
        logger.info("TrajectoryRewardModel initialized (heuristic-based)")
    
    def compute_trajectory_reward(
        self,
        trajectory: List[Dict[str, Any]],
        episode_stats: Dict[str, Any]
    ) -> float:
        """
        Compute reward for entire episode trajectory
        
        Args:
            trajectory: List of (state, action, reward) tuples
            episode_stats: Episode statistics
        
        Returns:
            Trajectory reward (0-1 scale)
        """
        # Efficiency: Prefer shorter episodes that achieve goal
        efficiency = self._compute_efficiency(episode_stats)
        
        # Coverage: Prefer compromising more hosts
        coverage = self._compute_coverage(episode_stats)
        
        # Stealth: Prefer lower noise actions
        stealth = self._compute_stealth(trajectory)
        
        # Goal: Bonus for achieving goals
        goal_bonus = self._compute_goal_bonus(episode_stats)
        
        # Weighted sum
        trajectory_reward = (
            self.efficiency_weight * efficiency +
            self.coverage_weight * coverage +
            self.stealth_weight * stealth +
            self.goal_weight * goal_bonus
        )
        
        logger.debug(
            f"Trajectory reward: {trajectory_reward:.3f} "
            f"(eff={efficiency:.2f}, cov={coverage:.2f}, "
            f"stealth={stealth:.2f}, goal={goal_bonus:.2f})"
        )
        
        return trajectory_reward
    
    def _compute_efficiency(self, stats: Dict[str, Any]) -> float:
        """
        Compute efficiency metric (0-1)
        
        Efficiency = 1 - (steps_taken / max_steps)
        Bonus for achieving goal quickly
        """
        steps = stats.get('total_steps', 0)
        max_steps = stats.get('max_steps', 100)
        
        if steps == 0:
            return 0.0
        
        # Base efficiency
        efficiency = 1.0 - min(steps / max_steps, 1.0)
        
        # Bonus for goal achievement
        if stats.get('goal_achieved', False):
            efficiency = min(efficiency * 1.5, 1.0)
        
        return efficiency
    
    def _compute_coverage(self, stats: Dict[str, Any]) -> float:
        """
        Compute coverage metric (0-1)
        
        Coverage = hosts_owned / total_hosts
        """
        owned = stats.get('hosts_owned', 0)
        total = stats.get('total_hosts', 1)
        
        return min(owned / total, 1.0)
    
    def _compute_stealth(self, trajectory: List[Dict[str, Any]]) -> float:
        """
        Compute stealth metric (0-1)
        
        Stealth = 1 - avg(noise_levels)
        """
        if not trajectory:
            return 0.5
        
        noise_levels = []
        for step in trajectory:
            action = step.get('action', {})
            noise = action.get('noise_level', 0.5)
            noise_levels.append(noise)
        
        avg_noise = np.mean(noise_levels)
        stealth = 1.0 - avg_noise
        
        return stealth
    
    def _compute_goal_bonus(self, stats: Dict[str, Any]) -> float:
        """
        Compute goal achievement bonus (0-1)
        
        Full bonus for achieving all goals
        """
        goal_progress = stats.get('goal_progress', 0.0)
        return goal_progress


if __name__ == "__main__":
    # Test trajectory reward model
    logger.info("Testing TrajectoryRewardModel...")
    
    model = TrajectoryRewardModel()
    
    # Mock trajectory
    trajectory = [
        {'action': {'noise_level': 0.3}},
        {'action': {'noise_level': 0.5}},
        {'action': {'noise_level': 0.4}},
    ]
    
    # Mock episode stats
    stats = {
        'total_steps': 30,
        'max_steps': 100,
        'hosts_owned': 3,
        'total_hosts': 5,
        'goal_achieved': True,
        'goal_progress': 1.0
    }
    
    # Compute trajectory reward
    reward = model.compute_trajectory_reward(trajectory, stats)
    print(f"Trajectory reward: {reward:.3f}")
    
    logger.info("Test completed!")
