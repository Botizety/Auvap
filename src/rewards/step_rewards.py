"""
Step Reward Calculator

Implements DynPen-style step rewards:
reward = max(0, result - cost)

Where:
- result: Value gained from action (host compromise, credential discovery, etc.)
- cost: Resource cost of action (time, noise, resources)

This encourages efficient exploitation while penalizing expensive failures.
"""

from typing import Dict, Any
import numpy as np
from loguru import logger


class StepRewardCalculator:
    """
    Calculate step-level rewards based on action results
    
    Reward components:
    - Host compromise: +10 (base) + host_value
    - Credential discovery: +5
    - Service discovery: +2
    - Failed action: -cost
    - Invalid action: -5 (penalty)
    - Detection risk: -noise_level
    """
    
    def __init__(
        self,
        host_compromise_reward: float = 10.0,
        credential_reward: float = 5.0,
        discovery_reward: float = 2.0,
        invalid_action_penalty: float = -5.0,
        cost_multiplier: float = 1.0
    ):
        """
        Initialize step reward calculator
        
        Args:
            host_compromise_reward: Base reward for compromising a host
            credential_reward: Reward for discovering credentials
            discovery_reward: Reward for discovering new services/hosts
            invalid_action_penalty: Penalty for invalid actions
            cost_multiplier: Multiplier for action costs
        """
        self.host_compromise_reward = host_compromise_reward
        self.credential_reward = credential_reward
        self.discovery_reward = discovery_reward
        self.invalid_action_penalty = invalid_action_penalty
        self.cost_multiplier = cost_multiplier
        
        logger.info("StepRewardCalculator initialized")
    
    def calculate_reward(
        self,
        action_result: Dict[str, Any],
        action_cost: float,
        action_valid: bool = True
    ) -> float:
        """
        Calculate step reward based on action result
        
        Args:
            action_result: Dictionary with action outcomes
            action_cost: Cost of the action
            action_valid: Whether action was valid
        
        Returns:
            Step reward (can be negative)
        """
        if not action_valid:
            return self.invalid_action_penalty
        
        # Start with negative cost
        reward = -action_cost * self.cost_multiplier
        
        # Add positive outcomes
        if action_result.get('host_compromised', False):
            host_value = action_result.get('host_value', 0)
            reward += self.host_compromise_reward + host_value
            logger.debug(f"Host compromised: +{self.host_compromise_reward + host_value}")
        
        if action_result.get('credential_discovered', False):
            reward += self.credential_reward
            logger.debug(f"Credential discovered: +{self.credential_reward}")
        
        if action_result.get('services_discovered', 0) > 0:
            count = action_result.get('services_discovered', 0)
            reward += self.discovery_reward * count
            logger.debug(f"Services discovered: +{self.discovery_reward * count}")
        
        if action_result.get('hosts_discovered', 0) > 0:
            count = action_result.get('hosts_discovered', 0)
            reward += self.discovery_reward * count
            logger.debug(f"Hosts discovered: +{self.discovery_reward * count}")
        
        # Apply clipping (DynPen-style: no negative reward for exploration)
        # Comment this out if you want negative rewards for failed expensive actions
        # reward = max(0, reward)
        
        return reward
    
    def calculate_batch_rewards(
        self,
        results: list[Dict[str, Any]],
        costs: list[float],
        valid_flags: list[bool]
    ) -> np.ndarray:
        """
        Calculate rewards for a batch of actions
        
        Args:
            results: List of action results
            costs: List of action costs
            valid_flags: List of validity flags
        
        Returns:
            Array of rewards
        """
        rewards = np.zeros(len(results), dtype=np.float32)
        
        for i, (result, cost, valid) in enumerate(zip(results, costs, valid_flags)):
            rewards[i] = self.calculate_reward(result, cost, valid)
        
        return rewards


if __name__ == "__main__":
    # Test step reward calculator
    logger.info("Testing StepRewardCalculator...")
    
    calc = StepRewardCalculator()
    
    # Test case 1: Successful host compromise
    result1 = {
        'host_compromised': True,
        'host_value': 50,
        'credential_discovered': True
    }
    reward1 = calc.calculate_reward(result1, action_cost=2.0)
    print(f"Test 1 - Host compromise: {reward1:.2f} (expected: ~63.0)")
    
    # Test case 2: Failed action
    result2 = {
        'host_compromised': False
    }
    reward2 = calc.calculate_reward(result2, action_cost=3.0)
    print(f"Test 2 - Failed action: {reward2:.2f} (expected: -3.0)")
    
    # Test case 3: Discovery
    result3 = {
        'services_discovered': 3,
        'hosts_discovered': 1
    }
    reward3 = calc.calculate_reward(result3, action_cost=0.5)
    print(f"Test 3 - Discovery: {reward3:.2f} (expected: ~7.5)")
    
    # Test case 4: Invalid action
    result4 = {}
    reward4 = calc.calculate_reward(result4, action_cost=1.0, action_valid=False)
    print(f"Test 4 - Invalid action: {reward4:.2f} (expected: -5.0)")
    
    logger.info("Test completed!")
