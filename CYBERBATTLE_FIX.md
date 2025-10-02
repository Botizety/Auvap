# CyberBattle Import Fix Guide

## Problem
The CyberBattleSim package installs as `cyberbattle` (not `cyberbattlesim`) and has a different module structure than expected.

## Package Structure
```
cyberbattle/
├── _env/
│   └── cyberbattle_env.py    # Contains CyberBattleEnv
├── samples/
│   ├── chainpattern/         # Chain network topology
│   ├── toyctf/              # Toy CTF scenario
│   └── simple/              # Simple network
├── simulation/
│   ├── model.py             # Network model
│   ├── actions.py           # Action definitions
│   └── generate_network.py  # Network generation utilities
└── agents/                  # Sample agents

```

## Correct Imports

### Old (Incorrect):
```python
import cyberbattlesim.simulation.model as model
import cyberbattlesim.simulation.generate as generate
from cyberbattlesim import gymenvs
```

### New (Correct):
```python
import cyberbattle.simulation.model as model
from cyberbattle._env.cyberbattle_env import CyberBattleEnv
from cyberbattle.samples.chainpattern import chainpattern
```

## Creating Environments

### Chain Network (Even numbers only):
```python
from cyberbattle.samples.chainpattern import chainpattern
from cyberbattle._env.cyberbattle_env import CyberBattleEnv

# Create chain environment with 6 nodes (must be even)
env_spec = chainpattern.new_environment(size=6)
env = CyberBattleEnv(
    env_spec,
    maximum_total_credentials=10,
    maximum_node_count=10
)

# Reset returns (observation, info) tuple
obs, info = env.reset()
```

### ToyC TF Network:
```python
from cyberbattle.samples.toyctf import toyctf
from cyberbattle._env.cyberbattle_env import CyberBattleEnv

env_spec = toyctf.new_environment()
env = CyberBattleEnv(env_spec, maximum_total_credentials=10, maximum_node_count=22)
```

## API Changes

### Reset:
```python
# Old: obs = env.reset()
# New: obs, info = env.reset()  # Returns tuple
```

### Step:
```python
# Returns: (obs, reward, terminated, truncated, info)
obs, reward, terminated, truncated, info = env.step(action)
```

## Files That Need Updates

1. `src/environment/cbs_wrapper.py` - Main wrapper
2. `scripts/train_auvap.py` - Training script
3. `tests/test_setup.py` - Verification script

## Quick Test

```python
from cyberbattle.samples.chainpattern import chainpattern
from cyberbattle._env.cyberbattle_env import CyberBattleEnv

# Create and test
env = CyberBattleEnv(
    chainpattern.new_environment(6),
    maximum_total_credentials=10,
    maximum_node_count=10
)

obs, info = env.reset()
print("✓ CyberBattle working!")
print(f"Observation keys: {list(obs.keys())[:5]}")
print(f"Action space: {env.action_space}")
```

## Temporary Solution

For now, you can use the mock environment in `train_auvap.py`:
```bash
python scripts/train_auvap.py --episodes 10
```

This runs without CyberBattleSim to test the AUVAP framework logic.

## Full Fix Coming

I'll update all files to work with the actual CyberBattle API in the next update.
