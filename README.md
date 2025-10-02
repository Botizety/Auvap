# AUVAP Framework
**Automated Vulnerability Assessment and Penetration Testing with Hierarchical Reinforcement Learning**

## Overview

AUVAP implements a novel approach to automated penetration testing using:
- **Manager-Worker Hierarchical RL**: Decomposing complex penetration testing into sub-goals
- **Cybersecurity Knowledge Graph (CKG)**: Neo4j-based graph for action masking and explainability
- **Dual-Signal Reward System**: Combining step rewards with trajectory-level preference learning
- **CyberBattleSim Integration**: Built on Microsoft's enterprise network simulation

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Manager Agent                        │
│  (Selects sub-goals, assigns targets/budgets)          │
└────────────────┬────────────────────────────────────────┘
                 │ Sub-goal + Budget
                 ▼
┌─────────────────────────────────────────────────────────┐
│                    Worker Agent                         │
│  (Executes low-level actions: scan, probe, exploit)    │
└────────────────┬────────────────────────────────────────┘
                 │ Actions + Results
                 ▼
┌─────────────────────────────────────────────────────────┐
│              CyberBattleSim Environment                 │
│  (Simulated enterprise network)                         │
└────────────────┬────────────────────────────────────────┘
                 │ Observations
                 ▼
┌─────────────────────────────────────────────────────────┐
│       Cybersecurity Knowledge Graph (Neo4j)             │
│  Host ↔ Service ↔ SoftwareStack ↔ Vuln ↔ Ability      │
│  - Action masking                                       │
│  - Feature extraction (CVSS, cost, noise)              │
│  - Explanation paths                                    │
└─────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.8+
- Neo4j 5.x (running locally or remote)
- CUDA-compatible GPU (optional, for faster training)

### Setup

1. **Clone and navigate to the project:**
```bash
cd "c:\Users\kitti\OneDrive\เอกสาร\Cyber AUVAP"
```

2. **Create virtual environment:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Setup Neo4j:**
   - Install Neo4j Desktop or use Docker:
   ```bash
   docker run -d --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/auvap_password \
     neo4j:5.12
   ```
   - Create `.env` file:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=auvap_password
   ```

5. **Verify installation:**
```bash
python tests/test_setup.py
```

## Quick Start

### Run a training session:
```bash
python scripts/train_auvap.py --config configs/chain_topology.yaml
```

### Evaluate a trained model:
```bash
python scripts/evaluate.py --model checkpoints/best_model.zip --episodes 100
```

### View explanations:
```bash
python scripts/explain_episode.py --episode logs/episode_42.json
```

## Project Structure

```
AUVAP/
├── src/
│   ├── environment/          # CyberBattleSim wrapper
│   │   ├── cbs_wrapper.py
│   │   └── state_manager.py
│   ├── knowledge_graph/      # Neo4j CKG implementation
│   │   ├── ckg_schema.py
│   │   ├── ckg_manager.py
│   │   └── action_masking.py
│   ├── agents/               # Hierarchical RL agents
│   │   ├── manager.py
│   │   ├── worker.py
│   │   └── hierarchical_env.py
│   ├── rewards/              # Dual-signal reward system
│   │   ├── step_rewards.py
│   │   ├── trajectory_rewards.py
│   │   └── reward_machines.py
│   └── explainability/       # Explanation generation
│       ├── path_extractor.py
│       └── report_generator.py
├── scripts/                  # Training & evaluation
├── configs/                  # Configuration files
├── tests/                    # Unit tests
├── notebooks/                # Jupyter analysis notebooks
└── docs/                     # Additional documentation
```

## Key Components

### 1. Manager Agent
- Selects high-level sub-goals: `reconnaissance`, `web_exploitation`, `privilege_escalation`, `pivoting`
- Assigns targets and action budgets (e.g., "scan web tier, budget: 6 actions")
- Monitors Worker progress and adjusts strategy

### 2. Worker Agent
- Executes CyberBattleSim actions: `local`, `remote`, `connect`
- Guided by CKG features: CVSS scores, cost, noise, credential requirements
- Respects Manager's budget and stop conditions

### 3. Cybersecurity Knowledge Graph
- **6 Entity Types**: Host, Service, SoftwareStack, VulnerabilityTechnique, Ability, Credential
- **Action Masking**: Only valid actions presented to Worker
- **Feature Extraction**: Per-action features (CVSS, cost, noise level)
- **Explainability**: Generates reasoning paths (e.g., "Exploit X chosen because Service Y vulnerable via CVE Z")

### 4. Dual-Signal Rewards
- **Step Reward**: `max(0, result - cost)` (DynPen-style)
- **Trajectory Reward**: Preference-trained `r_θ(τ)` for long-horizon quality
- **Reward Machines**: Encode phase progression bonuses

## Training Details

- **Episodes**: 10,000+ for convergence
- **Manager**: PPO with sub-goal action space (4 goals × target selection)
- **Worker**: PPO/DQN with masked action space
- **Metrics**: Steps-to-goal, success rate, invalid action %, explanation quality

## Evaluation

The framework tracks:
- **Efficiency**: Steps to compromise all targets
- **Success Rate**: % episodes reaching goal
- **Validity**: % actions that are CKG-valid
- **Explainability**: Human-readable reasoning paths

## Research Paper Reference

This implementation is based on the AUVAP research paper:
- Manager-Worker hierarchical decomposition
- CKG-based action masking and feature extraction
- Dual-signal reward system with preference learning
- Explanation path generation for interpretability

## Citation

```bibtex
@article{auvap2024,
  title={AUVAP: Automated Vulnerability Assessment and Penetration Testing Framework with Hierarchical RL},
  author={Your Name},
  journal={Conference/Journal},
  year={2024}
}
```

## License

MIT License - See LICENSE file for details

## Contact

For questions or issues, please open a GitHub issue or contact the author.
