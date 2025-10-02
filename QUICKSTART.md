# AUVAP Quick Start Guide

Get started with AUVAP in 5 minutes!

## ✅ VERIFY IT'S REAL (Not Mock!)

**First, prove AUVAP uses REAL Microsoft CyberBattleSim:**

```powershell
.venv\Scripts\python.exe scripts\verify_real.py
```

This confirms you have a **real cybersecurity research tool**, not a mockup!

See `HOW_TO_VERIFY_REAL.md` for detailed explanation.

---

## TL;DR - Quick Setup

```powershell
# 1. Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Verify REAL CyberBattle (not mock!)
.venv\Scripts\python.exe scripts\verify_real.py

# 3. Test installation
python tests\test_setup.py

# 4. Run training with REAL CyberBattle
.venv\Scripts\python.exe scripts\train_auvap.py --env chain --episodes 10

# 5. (Optional) With Neo4j knowledge graph
docker run -d --name auvap-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/auvap_password neo4j:5.12
.venv\Scripts\python.exe scripts\train_auvap.py --env chain --use-neo4j --episodes 10
```

## What is AUVAP?

AUVAP (**Automated Vulnerability Assessment and Penetration Testing**) is a hierarchical reinforcement learning framework that learns to hack networks intelligently.

### Key Features

- **🎯 Hierarchical RL:** Manager-Worker architecture for strategic and tactical decisions
- **🧠 Knowledge Graph:** Neo4j-based CKG for action masking and explainability
- **🎁 Dual Rewards:** Step rewards + trajectory rewards for better learning
- **📊 Explainable:** Generates human-readable reports of attack paths
- **🔬 Research-Ready:** Built on CyberBattleSim, ready for experimentation

## Architecture

```
┌─────────────┐
│   Manager   │ ← Selects sub-goals (recon, exploit, escalate, pivot)
└──────┬──────┘
       │ Task + Budget
       ▼
┌─────────────┐
│   Worker    │ ← Executes low-level actions (scan, exploit, connect)
└──────┬──────┘
       │ Actions
       ▼
┌─────────────┐
│ CyberBattle │ ← Simulated network environment
│     Sim     │
└──────┬──────┘
       │ Observations
       ▼
┌─────────────┐
│     CKG     │ ← Knowledge graph for masking & features
│   (Neo4j)   │
└─────────────┘
```

## Training Modes

### Mode 1: Mock Environment (Testing Only)

Test the framework structure without real CyberBattle:

```powershell
.venv\Scripts\python.exe scripts\train_auvap.py --env mock --episodes 5
```

**Use when:** Testing code changes, debugging  
**⚠️ WARNING:** This is NOT real - just for framework testing!

### Mode 2: Real CyberBattleSim (Recommended)

Train on **REAL Microsoft CyberBattle** environment:

```powershell
.venv\Scripts\python.exe scripts\train_auvap.py --env chain --episodes 100
```

**Use when:** Actual training, research, realistic results  
**✅ REAL:** Actual vulnerability simulation, state progression, Microsoft's cyber range

### Mode 3: Full AUVAP with Knowledge Graph

Complete system with Neo4j integration:

```powershell
# Start Neo4j
docker start auvap-neo4j

# Train with real CyberBattle + Knowledge Graph
.venv\Scripts\python.exe scripts\train_auvap.py --env chain --use-neo4j --episodes 1000
```

**Use when:** Production training, research papers, explainable AI  
**✅ REAL:** Full autonomous vulnerability assessment platform

## Configuration

Edit `configs/chain_topology.yaml`:

```yaml
environment:
  name: "CyberBattleChain-v0"
  num_hosts: 5
  max_steps_per_episode: 100

manager:
  default_budget: 6
  decision_frequency: 10

training:
  total_episodes: 10000
  save_frequency: 500
```

## Monitoring Training

### Real-time Logs

```powershell
# Watch training progress
Get-Content logs/training.log -Wait
```

### TensorBoard (Coming Soon)

```powershell
tensorboard --logdir logs/tensorboard
```

### Neo4j Browser

Open http://localhost:7474 to visualize the knowledge graph in real-time.

## Output Files

After training:

```
Cyber AUVAP/
├── logs/
│   ├── training.log          # Training logs
│   └── episode_*.json        # Episode data
├── checkpoints/
│   ├── best_model.zip        # Best Manager model
│   └── worker_best.zip       # Best Worker model
└── reports/
    └── episode_reports/      # Generated reports
```

## Example Report

After an episode:

```markdown
# AUVAP Episode Report #42

## Executive Summary
**Status:** ✅ SUCCESS
**Total Steps:** 45
**Hosts Compromised:** 4/5
**Current Phase:** goal_achieved

## Manager Decisions Timeline
1. **reconnaissance** → Target: web-01, Budget: 4
2. **web_exploitation** → Target: web-01, Budget: 6
3. **pivoting** → Target: db-01, Budget: 8

## Network Topology
🔴 OWNED client (admin)
  └─ RDP
🔴 OWNED web-01 (user)
  └─ HTTP
  └─ SSH
🟡 DISCOVERED db-01
  └─ MySQL
```

## Common Commands

```powershell
# VERIFY IT'S REAL (not mock!)
.venv\Scripts\python.exe scripts\verify_real.py

# Test installation
python tests\test_setup.py

# Quick training with REAL CyberBattle
.venv\Scripts\python.exe scripts\train_auvap.py --env chain --episodes 10

# Full training (real CBS + Neo4j)
.venv\Scripts\python.exe scripts\train_auvap.py --env chain --use-neo4j --episodes 1000

# Mock environment (testing only - NOT REAL!)
.venv\Scripts\python.exe scripts\train_auvap.py --env mock --episodes 5

# Custom config
python scripts\train_auvap.py --config configs\custom.yaml

# Evaluate model
python scripts\evaluate.py --model checkpoints\best_model.zip

# Generate report
python scripts\explain_episode.py --episode logs\episode_42.json
```

## Tips & Tricks

### Faster Training

1. Use GPU: Install CUDA PyTorch
2. Reduce logging: `--log-frequency 100`
3. Smaller network: Use `CyberBattleTiny-v0`

### Better Results

1. Longer training: `--episodes 10000`
2. Tune hyperparameters in config file
3. Adjust reward weights
4. Use action masking: `--use-neo4j`

### Debugging

1. Check logs: `logs/training.log`
2. Verify Neo4j: http://localhost:7474
3. Test components individually (see `__main__` blocks in source files)

## Next Steps

1. **Experiment:** Try different hyperparameters
2. **Customize:** Create custom network topologies
3. **Analyze:** Review generated reports
4. **Extend:** Add new sub-goals or actions
5. **Research:** Compare against baseline agents

## Key Metrics

Monitor these during training:

- **Success Rate:** % episodes reaching goal
- **Steps to Goal:** Efficiency metric
- **Invalid Action Rate:** Should decrease over time
- **Manager Success Rates:** Per sub-goal performance

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Import errors | Activate virtual environment |
| Neo4j connection failed | Start Neo4j container |
| CBS not found | `pip install cyberbattlesim` |
| Training too slow | Use smaller network or GPU |
| Out of memory | Reduce batch size in config |

## Resources

- **Full Installation Guide:** See `INSTALL.md`
- **Architecture Details:** See `README.md`
- **API Documentation:** See `docs/` folder
- **Examples:** See `notebooks/` folder

---

**Happy Hacking!** 🎩🔐
