"""
Reward Machines for Phase Progression

Implements finite state machines that track penetration testing phases
and provide bonus rewards for phase transitions:

reconnaissance → initial_access → lateral_movement → privilege_escalation → goal

This encodes high-level progress signals that help the agent understand
the overall penetration testing workflow.
"""

from enum import Enum
from typing import Dict, Any, Optional
from loguru import logger


class PenetrationPhase(Enum):
    """Phases of penetration testing"""
    RECONNAISSANCE = "reconnaissance"
    INITIAL_ACCESS = "initial_access"
    LATERAL_MOVEMENT = "lateral_movement"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    GOAL_ACHIEVED = "goal_achieved"


class RewardMachine:
    """
    Reward machine for tracking penetration testing progress
    
    Provides bonus rewards for:
    - Phase transitions (moving forward in the kill chain)
    - Achieving milestones within phases
    - Completing the overall objective
    """
    
    def __init__(
        self,
        phase_transition_reward: float = 5.0,
        milestone_reward: float = 2.0,
        goal_achievement_reward: float = 20.0
    ):
        """
        Initialize reward machine
        
        Args:
            phase_transition_reward: Reward for advancing to next phase
            milestone_reward: Reward for milestones within phase
            goal_achievement_reward: Reward for achieving final goal
        """
        self.phase_transition_reward = phase_transition_reward
        self.milestone_reward = milestone_reward
        self.goal_achievement_reward = goal_achievement_reward
        
        # Current phase
        self.current_phase = PenetrationPhase.RECONNAISSANCE
        
        # Phase history
        self.phase_history = [PenetrationPhase.RECONNAISSANCE]
        
        # Milestones achieved
        self.milestones: Dict[PenetrationPhase, list[str]] = {
            phase: [] for phase in PenetrationPhase
        }
        
        logger.info("RewardMachine initialized")
    
    def reset(self):
        """Reset reward machine for new episode"""
        self.current_phase = PenetrationPhase.RECONNAISSANCE
        self.phase_history = [PenetrationPhase.RECONNAISSANCE]
        self.milestones = {phase: [] for phase in PenetrationPhase}
    
    def update(self, state_manager) -> float:
        """
        Update reward machine based on current state
        
        Args:
            state_manager: StateManager with episode state
        
        Returns:
            Bonus reward for phase transitions/milestones
        """
        # Determine current phase from state
        new_phase_str = state_manager.get_penetration_phase()
        
        # Map to enum
        phase_map = {
            'reconnaissance': PenetrationPhase.RECONNAISSANCE,
            'initial_access': PenetrationPhase.INITIAL_ACCESS,
            'lateral_movement': PenetrationPhase.LATERAL_MOVEMENT,
            'privilege_escalation': PenetrationPhase.PRIVILEGE_ESCALATION,
            'goal_achieved': PenetrationPhase.GOAL_ACHIEVED
        }
        
        new_phase = phase_map.get(new_phase_str, PenetrationPhase.RECONNAISSANCE)
        
        bonus_reward = 0.0
        
        # Check for phase transition
        if new_phase != self.current_phase:
            # Check if this is forward progress
            phase_order = list(PenetrationPhase)
            current_idx = phase_order.index(self.current_phase)
            new_idx = phase_order.index(new_phase)
            
            if new_idx > current_idx:
                # Forward progress!
                bonus_reward += self.phase_transition_reward
                logger.info(
                    f"Phase transition: {self.current_phase.value} → {new_phase.value} "
                    f"(+{self.phase_transition_reward})"
                )
                
                self.current_phase = new_phase
                self.phase_history.append(new_phase)
        
        # Check for milestones within current phase
        milestone_bonus = self._check_milestones(state_manager)
        bonus_reward += milestone_bonus
        
        # Check for goal achievement
        if new_phase == PenetrationPhase.GOAL_ACHIEVED:
            if 'goal_achieved' not in self.milestones[PenetrationPhase.GOAL_ACHIEVED]:
                bonus_reward += self.goal_achievement_reward
                self.milestones[PenetrationPhase.GOAL_ACHIEVED].append('goal_achieved')
                logger.info(f"GOAL ACHIEVED! (+{self.goal_achievement_reward})")
        
        return bonus_reward
    
    def _check_milestones(self, state_manager) -> float:
        """
        Check for milestones achieved in current phase
        
        Args:
            state_manager: State manager
        
        Returns:
            Milestone bonus reward
        """
        bonus = 0.0
        phase = self.current_phase
        
        if phase == PenetrationPhase.RECONNAISSANCE:
            # Milestone: First host discovered
            if len(state_manager.get_discovered_hosts()) >= 1:
                if 'first_discovery' not in self.milestones[phase]:
                    self.milestones[phase].append('first_discovery')
                    bonus += self.milestone_reward
                    logger.debug("Milestone: First host discovered")
        
        elif phase == PenetrationPhase.INITIAL_ACCESS:
            # Milestone: First host compromised
            if len(state_manager.get_owned_hosts()) >= 1:
                if 'first_compromise' not in self.milestones[phase]:
                    self.milestones[phase].append('first_compromise')
                    bonus += self.milestone_reward
                    logger.debug("Milestone: First host compromised")
        
        elif phase == PenetrationPhase.LATERAL_MOVEMENT:
            # Milestone: Multiple hosts compromised
            owned = len(state_manager.get_owned_hosts())
            if owned >= 2 and 'multi_compromise' not in self.milestones[phase]:
                self.milestones[phase].append('multi_compromise')
                bonus += self.milestone_reward
                logger.debug("Milestone: Multiple hosts compromised")
        
        elif phase == PenetrationPhase.PRIVILEGE_ESCALATION:
            # Milestone: Admin privilege obtained
            for host_id in state_manager.get_owned_hosts():
                if state_manager.get_privilege(host_id) == 'admin':
                    if 'admin_privilege' not in self.milestones[phase]:
                        self.milestones[phase].append('admin_privilege')
                        bonus += self.milestone_reward
                        logger.debug("Milestone: Admin privilege obtained")
                        break
        
        return bonus
    
    def get_phase_progress(self) -> float:
        """
        Get progress through phases (0-1)
        
        Returns:
            Progress ratio
        """
        phase_order = list(PenetrationPhase)
        current_idx = phase_order.index(self.current_phase)
        return current_idx / (len(phase_order) - 1)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reward machine statistics"""
        return {
            'current_phase': self.current_phase.value,
            'phase_history': [p.value for p in self.phase_history],
            'phase_progress': self.get_phase_progress(),
            'milestones_achieved': sum(len(m) for m in self.milestones.values())
        }


if __name__ == "__main__":
    # Test reward machine
    from ..environment.state_manager import StateManager
    
    logger.info("Testing RewardMachine...")
    
    # Create reward machine
    rm = RewardMachine()
    
    # Create mock state
    state = StateManager()
    
    # Initial state (reconnaissance)
    print(f"\n=== Initial Phase ===")
    print(f"Phase: {rm.current_phase.value}")
    bonus = rm.update(state)
    print(f"Bonus reward: {bonus}")
    
    # Discover a host
    print(f"\n=== Discover Host ===")
    state.add_host("web-01")
    state.mark_discovered("web-01")
    bonus = rm.update(state)
    print(f"Phase: {rm.current_phase.value}, Bonus: {bonus}")
    
    # Compromise a host (initial access)
    print(f"\n=== Compromise Host ===")
    state.mark_owned("web-01", privilege="user")
    bonus = rm.update(state)
    print(f"Phase: {rm.current_phase.value}, Bonus: {bonus}")
    
    # Compromise another host (lateral movement)
    print(f"\n=== Lateral Movement ===")
    state.add_host("db-01")
    state.mark_discovered("db-01")
    state.mark_owned("db-01", privilege="admin")
    bonus = rm.update(state)
    print(f"Phase: {rm.current_phase.value}, Bonus: {bonus}")
    
    # Get statistics
    print(f"\n=== Statistics ===")
    stats = rm.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    logger.info("Test completed!")
