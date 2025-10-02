"""
Test Setup Script

Verifies that all components are properly installed and configured.
Run this before training to check your setup.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
import importlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_import(module_name, package_name=None):
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        logger.success(f"✓ {package_name or module_name} installed")
        return True
    except ImportError:
        logger.error(f"✗ {package_name or module_name} NOT installed")
        return False


def check_auvap_modules():
    """Check AUVAP modules"""
    logger.info("\n=== Checking AUVAP Modules ===")
    
    modules = [
        "src.environment.cbs_wrapper",
        "src.environment.state_manager",
        "src.knowledge_graph.ckg_schema",
        "src.knowledge_graph.ckg_manager",
        "src.knowledge_graph.action_masking",
        "src.knowledge_graph.feature_extractor",
        "src.agents.manager",
        "src.agents.worker",
        "src.rewards.step_rewards",
        "src.rewards.reward_machines",
    ]
    
    all_ok = True
    for module in modules:
        try:
            importlib.import_module(module)
            logger.success(f"✓ {module}")
        except Exception as e:
            logger.error(f"✗ {module}: {e}")
            all_ok = False
    
    return all_ok


def check_dependencies():
    """Check required dependencies"""
    logger.info("\n=== Checking Dependencies ===")
    
    dependencies = [
        ("numpy", "numpy"),
        ("gym", "gym"),
        ("torch", "pytorch"),
        ("stable_baselines3", "stable-baselines3"),
        ("neo4j", "neo4j"),
        ("loguru", "loguru"),
        ("yaml", "pyyaml"),
    ]
    
    results = []
    for module, package in dependencies:
        results.append(check_import(module, package))
    
    return all(results)


def check_neo4j():
    """Check Neo4j connection"""
    logger.info("\n=== Checking Neo4j ===")
    
    try:
        from neo4j import GraphDatabase
        import os
        
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        username = os.getenv('NEO4J_USER', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'password')
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        driver.close()
        
        logger.success(f"✓ Neo4j connected at {uri}")
        return True
        
    except Exception as e:
        logger.warning(f"✗ Neo4j not available: {e}")
        logger.info("  To start Neo4j with Docker:")
        logger.info("  docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.12")
        return False


def check_cyberbattlesim():
    """Check CyberBattleSim"""
    logger.info("\n=== Checking CyberBattleSim ===")
    
    try:
        import cyberbattle
        logger.success("✓ CyberBattleSim installed (as 'cyberbattle' package)")
        
        # Try to create environment using CyberBattle's direct API
        try:
            from cyberbattle.samples.chainpattern import chainpattern
            from cyberbattle._env.cyberbattle_env import CyberBattleEnv
            
            # Create a small chain network (must be even number)
            env_spec = chainpattern.new_environment(size=4)
            env = CyberBattleEnv(
                env_spec,
                maximum_total_credentials=10,
                maximum_node_count=10
            )
            
            # Test reset
            obs, info = env.reset()
            logger.success("✓ CyberBattle chain environment working")
            logger.success(f"  Created 4-node chain network")
            logger.success(f"  Observation keys: {list(obs.keys())[:5]}")
            return True
            
        except Exception as e:
            logger.warning(f"✗ Could not create CBS environment: {e}")
            logger.info(f"  Error details: {type(e).__name__}")
            return False
            
    except ImportError as e:
        logger.warning("✗ CyberBattleSim not installed")
        logger.info("  Install with: pip install git+https://github.com/microsoft/CyberBattleSim.git")
        return False


def main():
    """Run all checks"""
    logger.info("=" * 60)
    logger.info("AUVAP Setup Verification")
    logger.info("=" * 60)
    
    results = {
        "AUVAP Modules": check_auvap_modules(),
        "Dependencies": check_dependencies(),
        "Neo4j": check_neo4j(),
        "CyberBattleSim": check_cyberbattlesim(),
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("Summary")
    logger.info("=" * 60)
    
    for component, status in results.items():
        status_str = "✓ OK" if status else "✗ FAILED"
        logger.info(f"{component:.<40} {status_str}")
    
    logger.info("=" * 60)
    
    if all(results.values()):
        logger.success("\n🎉 All checks passed! You're ready to train AUVAP.")
    else:
        logger.warning("\n⚠️  Some components are not available.")
        logger.info("You can still test with mock environment: python scripts/train_auvap.py --episodes 5")
    
    logger.info("\nNext steps:")
    logger.info("1. Configure .env file (copy from .env.example)")
    logger.info("2. Start Neo4j if not running")
    logger.info("3. Run training: python scripts/train_auvap.py")


if __name__ == "__main__":
    main()
