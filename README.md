# AUVAP Framework

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![Neo4j](https://img.shields.io/badge/Neo4j-5.x-brightgreen.svg)
![CyberBattleSim](https://img.shields.io/badge/CyberBattleSim-Microsoft-blueviolet.svg)
![Status](https://img.shields.io/badge/Status-Real%20Environment%20Verified-success.svg)

> **AUVAP** (*Automated Vulnerability Assessment and Penetration Testing*) is a production-ready research framework that combines hierarchical reinforcement learning with a Neo4j knowledge graph on top of Microsoft CyberBattleSim.

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Highlights](#highlights)
4. [Getting Started](#getting-started)
5. [Neo4j & Environment Setup](#neo4j--environment-setup)
6. [Usage](#usage)
7. [Documentation Map](#documentation-map)
8. [Repository Layout](#repository-layout)
9. [Tech Stack](#tech-stack)
10. [Citation](#citation)
11. [License](#license)
12. [Support](#support)

## Overview

AUVAP delivers a full autonomous penetration-testing pipeline:

- **Manager-Worker Hierarchical RL** for task decomposition
- **Cybersecurity Knowledge Graph (CKG)** in Neo4j for action masking, feature enrichment and explainability
- **Dual-Signal Reward System** that blends instantaneous rewards with preference-based trajectory scoring
- **Microsoft CyberBattleSim Integration** using the *real* environment APIs (no mocks)
- **2025-ready Implementation** with Python 3.13, Gymnasium, Stable-Baselines3 2.7, and the latest Neo4j driver

## System Architecture

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

## Highlights

- ✅ **Real CyberBattleSim integration** — verified with automated scripts (`scripts/verify_real.py`, `scripts/simple_proof.py`).
- ✅ **Neo4j-backed intelligence** — action masks, strategic features, explainability, and persistence.
- ✅ **Hierarchical RL agents** — Manager selects sub-goals, Worker executes valid actions only.
- ✅ **Dual reward signals** — step-level DynPen rewards plus trajectory preference learning.
- ✅ **Thorough documentation** — verification guides, data provenance, schema analysis, GitHub publishing instructions.

## Getting Started

### Prerequisites

- Python 3.13 (other 3.11+ versions may work, but 3.13 is what we ship)
- Git, Docker (for Neo4j), and PowerShell (commands below use PowerShell syntax)

### Clone & Environment

```powershell
git clone https://github.com/Botizety/Auvap.git
cd Auvap

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
```

### Smoke Test

```powershell
python tests/test_setup.py
```

This confirms the real CyberBattleSim package is installed and usable.

## Neo4j & Environment Setup

1. **Launch Neo4j 5.x (Docker example):**

   ```powershell
   docker run -d --name neo4j-auvap ^
     -p 7474:7474 -p 7687:7687 ^
     -e NEO4J_AUTH=neo4j/auvap_password ^
     neo4j:5.12
   ```

2. **Create a `.env` file (never commit it):**

   ```text
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=auvap_password
   ```

3. **(Optional) Load the default chain topology into Neo4j:**

   ```powershell
   python scripts/demo_neo4j_data.py --populate
   ```

   This script demonstrates data ingestion and can connect to a running Neo4j instance.

## Usage

| Goal | Command | Notes |
|------|---------|-------|
| Verify real CyberBattleSim integration | `python scripts/verify_real.py` | Runs six assertions proving we are using Microsoft’s environment. |
| Quick visual sanity check | `python scripts/simple_proof.py` | Prints the real network topology (node IDs, vulnerabilities). |
| Inspect Neo4j data pipeline | `python scripts/demo_neo4j_data.py` | Extracts topology, simulates discoveries, optionally pushes to Neo4j. |
| Train hierarchical agents | `python scripts/train_auvap.py --config configs/chain_topology.yaml --episodes 100` | Adjust `--episodes`, `--env`, or config file as needed. |
| Run the unit smoke test | `python tests/test_setup.py` | Verifies the CyberBattleSim API contract. |

### Customising Training

- Edit `configs/chain_topology.yaml` to change environment size, reward weights, or logging.
- Pass `--env toyctf` to `train_auvap.py` to use the ToyCTF CyberBattleSim scenario.
- Use `--use-neo4j` to enable knowledge-graph masking and feature extraction during training.

### Knowledge Graph Operations

Key APIs live in `src/knowledge_graph/ckg_manager.py` and leverage the schema defined in `src/knowledge_graph/ckg_schema.py`. Action masking, feature extraction, and explainability helpers are available via `src/knowledge_graph/action_masking.py` and `feature_extractor.py`.

## Documentation Map

| File | Purpose |
|------|---------|
| `HOW_TO_VERIFY_REAL.md` | Step-by-step proof that the project uses real CyberBattleSim. |
| `NEO4J_DATA_SOURCE.md` | Deep dive into every data source feeding Neo4j. |
| `NEO4J_DUTIES.md` | Explains how the knowledge graph powers masking, features, and explainability. |
| `SCHEMA_2025_ANALYSIS.md` | Validates the Neo4j schema against 2025 industry standards (MITRE ATT&CK, CVE, UCO). |
| `VERSION_STATUS_2025.md` | Confirms all dependencies are current as of October 2025. |
| `QUICKSTART.md` | Punchy TL;DR for setup and training. |
| `GITHUB_UPLOAD_GUIDE.md` & `QUICK_GITHUB_UPLOAD.md` | How this repository was published (handy if you fork). |

## Repository Layout

```
├── configs/                # Training configuration files
├── scripts/                # Training, verification, and demo scripts
├── src/
│   ├── agents/             # Manager & Worker RL agents
│   ├── environment/        # CyberBattleSim wrappers and state tracking
│   ├── explainability/     # Path extraction & reporting helpers
│   ├── knowledge_graph/    # Neo4j schema, manager, action masking, features
│   └── rewards/            # Step and trajectory reward implementations
├── tests/                  # Smoke tests for CyberBattleSim integration
├── requirements.txt        # Python dependencies
├── .env.example            # Example Neo4j credentials (safe to share)
└── *.md                    # Documentation (see table above)
```

## Tech Stack

- **Reinforcement Learning:** Gymnasium 0.29, Stable-Baselines3 2.7, PyTorch 2.x
- **Cyber Range:** Microsoft CyberBattleSim (chain and toyctf scenarios)
- **Knowledge Graph:** Neo4j 5.x (Bolt driver 6.0.2)
- **Explainability:** Graph-based path tracing + human-readable reports
- **Tooling:** Python 3.13, Docker, PowerShell, pytest, tqdm, loguru

## Citation

```bibtex
@software{auvap2025,
  author  = {Botizety},
  title   = {AUVAP: Automated Vulnerability Assessment and Penetration Testing Framework},
  year    = {2025},
  url     = {https://github.com/Botizety/Auvap},
  version = {1.0.0}
}
```

## License

Distributed under the [MIT License](LICENSE).

## Support

Open a [GitHub issue](https://github.com/Botizety/Auvap/issues) for bug reports or feature requests, or reach out via the contact details listed in the project documentation.
