# AUVAP Installation Guide

Complete step-by-step installation guide for the AUVAP framework.

## Prerequisites

- **Operating System:** Windows 10/11, Linux (Ubuntu 20.04+), or macOS
- **Python:** 3.8 or higher
- **Memory:** At least 8GB RAM (16GB recommended for training)
- **Storage:** 5GB free space
- **Optional:** NVIDIA GPU with CUDA support for faster training

## Installation Steps

### 1. Install Python and Git

#### Windows
```powershell
# Install Python from python.org or use Chocolatey
choco install python git

# Verify installation
python --version
git --version
```

#### Linux/macOS
```bash
# Most systems have Python pre-installed
python3 --version

# Install if needed
sudo apt-get install python3 python3-pip git  # Ubuntu/Debian
brew install python git  # macOS
```

### 2. Clone or Navigate to Project

```powershell
cd "c:\Users\kitti\OneDrive\เอกสาร\Cyber AUVAP"
```

### 3. Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows CMD:
.\venv\Scripts\activate.bat

# Linux/macOS:
source venv/bin/activate
```

**Note:** If you get a PowerShell execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 4. Install Python Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

This will install:
- CyberBattleSim (Microsoft's simulation environment)
- Stable-Baselines3 (RL library)
- PyTorch (deep learning framework)
- Neo4j driver (graph database)
- Other utilities (numpy, pandas, loguru, etc.)

**Installation may take 10-15 minutes depending on your connection.**

### 5. Install Neo4j Database

Neo4j is required for the Cybersecurity Knowledge Graph (CKG).

#### Option A: Docker (Recommended)

```powershell
# Install Docker Desktop from docker.com
# Then run Neo4j container:

docker run -d `
  --name auvap-neo4j `
  -p 7474:7474 -p 7687:7687 `
  -e NEO4J_AUTH=neo4j/auvap_password `
  -v ${PWD}/neo4j-data:/data `
  neo4j:5.12
```

Access Neo4j Browser at: http://localhost:7474
- Username: `neo4j`
- Password: `auvap_password`

#### Option B: Neo4j Desktop

1. Download from: https://neo4j.com/download/
2. Install and create a new database
3. Set password to `auvap_password` (or update .env)
4. Start the database

#### Option C: Skip Neo4j (Testing Only)

For quick testing without CKG features:
```powershell
# Run without --use-neo4j flag
python scripts/train_auvap.py --episodes 5
```

### 6. Configure Environment

```powershell
# Copy environment template
copy .env.example .env

# Edit .env with your settings
notepad .env
```

**Minimum .env configuration:**
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=auvap_password
LOG_LEVEL=INFO
```

### 7. Verify Installation

```powershell
python tests/test_setup.py
```

Expected output:
```
=== Checking AUVAP Modules ===
✓ src.environment.cbs_wrapper
✓ src.environment.state_manager
...
=== Checking Dependencies ===
✓ numpy installed
✓ pytorch installed
...
=== Checking Neo4j ===
✓ Neo4j connected at bolt://localhost:7687
...
🎉 All checks passed! You're ready to train AUVAP.
```

## Troubleshooting

### Common Issues

#### 1. CyberBattleSim Installation Fails

**Error:** `Could not install cyberbattlesim`

**Solution:**
```powershell
# Install from GitHub directly
pip install git+https://github.com/microsoft/CyberBattleSim.git
```

#### 2. PyTorch CUDA Issues

**Error:** `CUDA not available`

**Solution:**
- For CPU-only: This is fine, training will be slower
- For GPU: Install CUDA toolkit from nvidia.com
- Or reinstall PyTorch with CUDA:
```powershell
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

#### 3. Neo4j Connection Failed

**Error:** `Could not connect to Neo4j`

**Solutions:**
- Check Docker container is running: `docker ps`
- Verify port 7687 is not blocked
- Check firewall settings
- Try alternative URI: `bolt://127.0.0.1:7687`

#### 4. Module Import Errors

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```powershell
# Make sure you're in the project root
cd "c:\Users\kitti\OneDrive\เอกสาร\Cyber AUVAP"

# And virtual environment is activated
.\venv\Scripts\Activate.ps1
```

#### 5. Permission Errors (Windows)

**Error:** `Access is denied`

**Solution:**
```powershell
# Run PowerShell as Administrator
# Or adjust execution policy
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Dependency Conflicts

If you encounter dependency conflicts:

```powershell
# Create fresh environment
deactivate
rm -r venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install in specific order
pip install numpy
pip install torch
pip install stable-baselines3
pip install -r requirements.txt
```

## Quick Start After Installation

### 1. Test with Mock Environment (No CBS needed)

```powershell
python scripts/train_auvap.py --episodes 5
```

### 2. Test with CyberBattleSim

```powershell
python scripts/train_auvap.py --env CyberBattleChain-v0 --episodes 10
```

### 3. Full Training with CKG

```powershell
# Start Neo4j first
docker start auvap-neo4j

# Train with all features
python scripts/train_auvap.py `
  --env CyberBattleChain-v0 `
  --episodes 1000 `
  --use-neo4j `
  --log-frequency 50
```

## Performance Optimization

### For Faster Training

1. **Use GPU:** Install CUDA-enabled PyTorch
2. **Adjust batch sizes:** Edit `configs/chain_topology.yaml`
3. **Parallel environments:** Use vectorized environments
4. **Reduce logging:** Set `LOG_LEVEL=WARNING` in .env

### For Development

```powershell
# Install development dependencies
pip install pytest pytest-cov black flake8 ipython jupyter

# Run tests
pytest tests/

# Format code
black src/

# Start Jupyter for analysis
jupyter notebook notebooks/
```

## Updating

To update AUVAP to the latest version:

```powershell
# Pull latest changes (if using git)
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Verify
python tests/test_setup.py
```

## Uninstallation

To completely remove AUVAP:

```powershell
# Stop and remove Neo4j container
docker stop auvap-neo4j
docker rm auvap-neo4j

# Remove virtual environment
deactivate
rm -r venv

# Remove project files (optional)
cd ..
rm -r "Cyber AUVAP"
```

## Additional Resources

- **CyberBattleSim Documentation:** https://github.com/microsoft/CyberBattleSim
- **Stable-Baselines3 Docs:** https://stable-baselines3.readthedocs.io/
- **Neo4j Documentation:** https://neo4j.com/docs/
- **PyTorch Tutorials:** https://pytorch.org/tutorials/

## Getting Help

If you encounter issues not covered here:

1. Check the error messages carefully
2. Run `python tests/test_setup.py` for diagnostics
3. Review logs in `logs/training.log`
4. Check Neo4j browser at http://localhost:7474
5. Verify Python version: `python --version` (should be 3.8+)

## Next Steps

Once installation is complete:

1. Read `README.md` for framework overview
2. Explore `configs/chain_topology.yaml` for configuration options
3. Run training: `python scripts/train_auvap.py`
4. Check results in `logs/` and `checkpoints/`

---

**Congratulations! You're ready to use AUVAP.** 🎉
