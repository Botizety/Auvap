"""
Simple Training Script for AUVAP

This is a basic training script to demonstrate the AUVAP framework.
For full training, you'll need to:
1. Install all dependencies (see requirements.txt)
2. Setup Neo4j database
3. Configure CyberBattleSim environment

This script provides a template for training the hierarchical agents.
"""

import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
import numpy as np

# Check if packages are available
try:
    import gym
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False
    logger.warning("Dependencies not installed. Install with: pip install -r requirements.txt")

from src.environment.cbs_wrapper import CyberBattleSimWrapper
from src.environment.state_manager import StateManager
from src.knowledge_graph.ckg_manager import CKGManager
from src.knowledge_graph.action_masking import ActionMasker
from src.knowledge_graph.feature_extractor import FeatureExtractor
from src.agents.manager import ManagerAgent, SubGoal
from src.agents.worker import WorkerAgent
from src.rewards.step_rewards import StepRewardCalculator
from src.rewards.reward_machines import RewardMachine


def create_mock_env():
    """Create a mock environment for testing when CBS is not available"""
    class MockEnv(gym.Env):
        def __init__(self):
            self.observation_space = gym.spaces.Box(low=0, high=1, shape=(50,), dtype=np.float32)
            self.action_space = gym.spaces.Discrete(20)
            self.step_count = 0
            
        def reset(self):
            self.step_count = 0
            return np.random.rand(50).astype(np.float32)
        
        def step(self, action):
            self.step_count += 1
            obs = np.random.rand(50).astype(np.float32)
            reward = np.random.uniform(-1, 5)
            done = self.step_count >= 50 or np.random.rand() < 0.1
            info = {
                'host_compromised': np.random.rand() < 0.2,
                'services_discovered': np.random.randint(0, 3)
            }
            return obs, reward, done, info
        
        def render(self, mode='human'):
            pass
    
    return MockEnv()


def train_auvap(args):
    """
    Main training function for AUVAP
    
    Args:
        args: Command-line arguments
    """
    logger.info("=== AUVAP Training Started ===")
    logger.info(f"Environment: {args.env}")
    logger.info(f"Episodes: {args.episodes}")
    logger.info(f"Neo4j: {args.neo4j_uri}")
    
    # Initialize components
    logger.info("Initializing components...")
    
    # State manager
    state_manager = StateManager()
    
    # CKG manager
    ckg_manager = CKGManager(uri=args.neo4j_uri)
    if args.use_neo4j:
        if ckg_manager.connect():
            ckg_manager.initialize_schema(clear_existing=True)
            logger.info("Neo4j connected and initialized")
        else:
            logger.warning("Could not connect to Neo4j. Continuing without CKG features.")
            args.use_neo4j = False
    else:
        logger.info("Running without Neo4j (use --use-neo4j to enable)")
    
    # Reward calculator
    reward_calc = StepRewardCalculator()
    reward_machine = RewardMachine()
    
    # Manager and Worker agents
    manager = ManagerAgent(max_hosts=10, default_budget=6)
    worker = WorkerAgent(cbs_obs_dim=50, ckg_feature_dim=10, max_actions=20)
    
    logger.info("Components initialized successfully")
    
    # Create environment
    logger.info("Creating environment...")
    try:
        if DEPS_AVAILABLE and args.env != "mock":
            # Use real CyberBattle environment with chain topology (6 nodes)
            env = CyberBattleSimWrapper(env_name='chain', size=6)
            logger.info("Using real CyberBattle chain environment with 6 nodes")
        else:
            logger.warning("Using mock environment (install cyberbattlesim for real training)")
            env = create_mock_env()
    except Exception as e:
        logger.error(f"Could not create CBS environment: {e}")
        logger.info("Using mock environment instead")
        env = create_mock_env()
    
    # Training loop
    logger.info("Starting training loop...")
    
    episode_rewards = []
    episode_lengths = []
    
    for episode in range(args.episodes):
        # Reset
        obs = env.reset()
        state_manager.reset()
        reward_machine.reset()
        manager_steps = 0
        episode_reward = 0
        episode_length = 0
        done = False
        
        logger.info(f"\n=== Episode {episode + 1}/{args.episodes} ===")
        
        while not done and episode_length < args.max_steps:
            # Manager makes decision every N steps
            if episode_length % args.manager_frequency == 0:
                manager_obs = manager.build_observation(state_manager)
                manager_action = np.random.randint(0, manager.get_action_space_size())  # Random for now
                decision = manager.action_to_decision(manager_action, state_manager)
                worker.set_task(decision)
                manager_steps += 1
            
            # Worker takes action
            worker_obs = worker.build_observation(obs)
            worker_action = env.action_space.sample()  # Random for now (would use trained policy)
            
            # Execute in environment
            obs, env_reward, done, info = env.step(worker_action)
            
            # Calculate custom reward
            action_result = {
                'host_compromised': info.get('host_compromised', False),
                'services_discovered': info.get('services_discovered', 0)
            }
            step_reward = reward_calc.calculate_reward(action_result, action_cost=1.0)
            
            # Reward machine bonus
            rm_bonus = reward_machine.update(state_manager)
            total_reward = step_reward + rm_bonus
            
            # Record
            worker.record_action(total_reward, step_reward > 0)
            episode_reward += total_reward
            episode_length += 1
            
            # Check if Worker should stop
            feedback = info
            should_stop, reason = worker.should_stop(feedback)
            
            if should_stop:
                logger.debug(f"Worker stopped: {reason}")
                worker_feedback = worker.get_feedback()
                manager.record_worker_feedback(worker_feedback)
        
        # Episode complete
        episode_rewards.append(episode_reward)
        episode_lengths.append(episode_length)
        
        logger.info(f"Episode {episode + 1} complete:")
        logger.info(f"  Reward: {episode_reward:.2f}")
        logger.info(f"  Length: {episode_length} steps")
        logger.info(f"  Manager decisions: {manager_steps}")
        logger.info(f"  Phase: {reward_machine.current_phase.value}")
        
        # Periodic statistics
        if (episode + 1) % args.log_frequency == 0:
            avg_reward = np.mean(episode_rewards[-args.log_frequency:])
            avg_length = np.mean(episode_lengths[-args.log_frequency:])
            logger.info(f"\n--- Statistics (last {args.log_frequency} episodes) ---")
            logger.info(f"  Average reward: {avg_reward:.2f}")
            logger.info(f"  Average length: {avg_length:.1f}")
            logger.info(f"  Manager stats: {manager.get_statistics()}")
    
    # Training complete
    logger.info("\n=== Training Complete ===")
    logger.info(f"Total episodes: {args.episodes}")
    logger.info(f"Average reward: {np.mean(episode_rewards):.2f}")
    logger.info(f"Average length: {np.mean(episode_lengths):.1f}")
    
    # Cleanup
    if args.use_neo4j:
        ckg_manager.close()
    env.close()
    
    logger.info("Done!")


def main():
    parser = argparse.ArgumentParser(description="Train AUVAP agents")
    
    # Environment
    parser.add_argument("--env", type=str, default="mock",
                        help="Environment name (CyberBattleChain-v0, mock, etc.)")
    
    # Training
    parser.add_argument("--episodes", type=int, default=10,
                        help="Number of training episodes")
    parser.add_argument("--max-steps", type=int, default=100,
                        help="Maximum steps per episode")
    parser.add_argument("--manager-frequency", type=int, default=10,
                        help="Manager decision frequency (steps)")
    
    # Logging
    parser.add_argument("--log-frequency", type=int, default=5,
                        help="Log statistics every N episodes")
    parser.add_argument("--log-dir", type=str, default="logs",
                        help="Directory for logs")
    
    # Neo4j
    parser.add_argument("--use-neo4j", action="store_true",
                        help="Use Neo4j for CKG (requires Neo4j running)")
    parser.add_argument("--neo4j-uri", type=str, default="bolt://localhost:7687",
                        help="Neo4j URI")
    
    args = parser.parse_args()
    
    # Create log directory
    os.makedirs(args.log_dir, exist_ok=True)
    
    # Setup logging
    logger.add(f"{args.log_dir}/training.log", rotation="100 MB")
    
    # Run training
    try:
        train_auvap(args)
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
    except Exception as e:
        logger.exception(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
