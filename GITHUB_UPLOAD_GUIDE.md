# 🚀 GitHub Upload Guide for AUVAP Project

## Complete Step-by-Step Instructions

This guide will help you upload your AUVAP project to GitHub safely and professionally.

---

## ⚠️ IMPORTANT: Before You Start

### 1. **Check for Sensitive Information**

**NEVER commit these files:**
- ✅ Already in `.gitignore`:
  - `.env` (contains Neo4j password)
  - `.venv/` (virtual environment)
  - `__pycache__/` (Python cache)
  - `*.log` (logs may contain sensitive data)

**Double-check these don't exist:**
```powershell
# Check for .env file
Get-Content .env 2>$null

# If it shows your password, make sure .gitignore includes it!
```

### 2. **Create `.env.example`** (Template for Users)

Create this file so others know what environment variables they need:

```bash
# .env.example (safe to commit)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

---

## 📋 Pre-Upload Checklist

- [ ] `.gitignore` is configured (already done ✅)
- [ ] `.env` is NOT committed (check with `git status` after adding files)
- [ ] `README.md` is complete and informative
- [ ] All code is tested and working
- [ ] Remove any personal information (paths, usernames, emails you don't want public)

---

## 🛠️ Step-by-Step Upload Process

### Step 1: Initialize Git Repository

```powershell
# Navigate to your project directory
cd "c:\Users\kitti\OneDrive\เอกสาร\Cyber AUVAP"

# Initialize git repository
git init

# Check git version
git --version
```

**Expected Output:**
```
Initialized empty Git repository in C:/Users/kitti/OneDrive/เอกสาร/Cyber AUVAP/.git/
```

---

### Step 2: Configure Git (First Time Only)

```powershell
# Set your name (will appear on commits)
git config --global user.name "Your Name"

# Set your email (use your GitHub email)
git config --global user.email "your.email@example.com"

# Check configuration
git config --list
```

---

### Step 3: Create `.env.example` (Safe Template)

```powershell
# Create template file
@"
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
"@ | Out-File -FilePath .env.example -Encoding UTF8
```

---

### Step 4: Add Files to Git

```powershell
# Add all files (respects .gitignore)
git add .

# Check what will be committed
git status
```

**Important: Review the output!**
- ✅ Should include: `.py` files, `README.md`, `requirements.txt`, etc.
- ❌ Should NOT include: `.env`, `.venv/`, `__pycache__/`, `*.log`

**If you see `.env` in the list:**
```powershell
# Remove it from staging
git rm --cached .env

# Make sure .gitignore includes .env
echo ".env" >> .gitignore
git add .gitignore
```

---

### Step 5: Create Initial Commit

```powershell
# Commit your files with a message
git commit -m "Initial commit: AUVAP Framework implementation

- Hierarchical RL with Manager-Worker architecture
- CyberBattleSim integration with real CBS API
- Neo4j knowledge graph for action masking
- Dual-signal reward system
- Comprehensive verification and documentation
- Ready for 2025 deployment"
```

**Expected Output:**
```
[main (root-commit) abc1234] Initial commit: AUVAP Framework implementation
 XX files changed, YYYY insertions(+)
 create mode 100644 README.md
 create mode 100644 requirements.txt
 ...
```

---

### Step 6: Create GitHub Repository

#### Option A: Using GitHub Website (Recommended for Beginners)

1. **Go to GitHub:** https://github.com
2. **Sign in** to your account
3. **Click the `+` icon** (top right) → **"New repository"**
4. **Fill in details:**
   - **Repository name:** `AUVAP` or `AUVAP-Framework`
   - **Description:** "Automated Vulnerability Assessment and Penetration Testing with Hierarchical RL"
   - **Visibility:** 
     - ✅ **Public** (if you want to share/publish research)
     - ⚠️ **Private** (if you want to keep it confidential initially)
   - **Initialize repository:** ❌ **Do NOT check any boxes** (we already have files)
5. **Click "Create repository"**

#### Option B: Using GitHub CLI (Advanced)

```powershell
# Install GitHub CLI first: https://cli.github.com/
# Then authenticate
gh auth login

# Create repository
gh repo create AUVAP --public --source=. --remote=origin --push
```

---

### Step 7: Connect Local Repository to GitHub

After creating the repository on GitHub, you'll see commands. Use these:

```powershell
# Add GitHub as remote repository
git remote add origin https://github.com/YOUR_USERNAME/AUVAP.git

# Verify remote is added
git remote -v
```

**Replace `YOUR_USERNAME`** with your GitHub username!

**Expected Output:**
```
origin  https://github.com/YOUR_USERNAME/AUVAP.git (fetch)
origin  https://github.com/YOUR_USERNAME/AUVAP.git (push)
```

---

### Step 8: Push Code to GitHub

```powershell
# Rename branch to 'main' (GitHub default)
git branch -M main

# Push code to GitHub
git push -u origin main
```

**First time:** Git will ask for credentials:
- **Username:** Your GitHub username
- **Password:** Use **Personal Access Token** (NOT your account password)

**How to create Personal Access Token:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (full control)
4. Copy the token (save it somewhere safe!)
5. Use this token as your password when pushing

**Expected Output:**
```
Enumerating objects: XX, done.
Counting objects: 100% (XX/XX), done.
Delta compression using up to 8 threads
Compressing objects: 100% (XX/XX), done.
Writing objects: 100% (XX/XX), XXX KiB | XXX MiB/s, done.
Total XX (delta X), reused 0 (delta 0), pack-reused 0
To https://github.com/YOUR_USERNAME/AUVAP.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

### Step 9: Verify Upload

1. **Go to your GitHub repository:** https://github.com/YOUR_USERNAME/AUVAP
2. **Check that files are there:**
   - ✅ `README.md` displays on homepage
   - ✅ All source code files visible
   - ✅ `.gitignore` is present
   - ❌ `.env` is NOT visible (good!)
   - ❌ `.venv/` is NOT visible (good!)

---

## 📝 After Upload: Enhance Your Repository

### 1. **Add Topics/Tags**

On GitHub repository page:
- Click ⚙️ (settings icon) next to "About"
- Add topics: `reinforcement-learning`, `cybersecurity`, `penetration-testing`, `neo4j`, `hierarchical-rl`, `python`

### 2. **Add License**

```powershell
# Add MIT License (common for research)
@"
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"@ | Out-File -FilePath LICENSE -Encoding UTF8

git add LICENSE
git commit -m "Add MIT License"
git push
```

### 3. **Add GitHub Repository Description**

On your repository page:
- Click ⚙️ next to "About"
- Add description: "AUVAP: Automated Vulnerability Assessment and Penetration Testing with Hierarchical RL and Knowledge Graphs"
- Add website (if you have one)

### 4. **Create Releases** (When Ready)

```powershell
# Tag your current version
git tag -a v1.0.0 -m "AUVAP v1.0.0 - Initial Release"
git push origin v1.0.0
```

Then on GitHub:
- Go to "Releases" → "Draft a new release"
- Select tag `v1.0.0`
- Title: "AUVAP v1.0.0 - Initial Release"
- Description: List features, installation instructions, etc.

---

## 🔄 Future Updates: How to Push Changes

### Making Changes

```powershell
# 1. Make your code changes
# ... edit files ...

# 2. Check what changed
git status
git diff

# 3. Stage changes
git add .
# OR add specific files
git add src/agents/manager.py

# 4. Commit with descriptive message
git commit -m "Add new feature: Graph-based reward shaping"

# 5. Push to GitHub
git push
```

### Branching Workflow (Recommended for Larger Projects)

```powershell
# Create feature branch
git checkout -b feature/new-reward-system

# Make changes, commit
git add .
git commit -m "Implement graph-based reward shaping"

# Push branch to GitHub
git push -u origin feature/new-reward-system

# On GitHub: Create Pull Request to merge into main
# After merge on GitHub, update local:
git checkout main
git pull
git branch -d feature/new-reward-system  # Delete local branch
```

---

## 🛡️ Security Best Practices

### What to NEVER Commit

1. **Passwords/API Keys** (`.env` file)
2. **Personal Information** (real IP addresses, usernames)
3. **Large Binary Files** (models > 100MB - use Git LFS)
4. **Virtual Environments** (`.venv/`)
5. **Temporary Files** (`*.log`, `__pycache__/`)

### If You Accidentally Committed Secrets

```powershell
# Remove file from Git history (BEFORE pushing)
git rm --cached .env
git commit -m "Remove sensitive file"

# If already pushed to GitHub, you need to:
# 1. Change all passwords/secrets immediately!
# 2. Use git-filter-branch or BFG Repo-Cleaner to remove from history
# 3. Force push (WARNING: destructive!)
```

**Better:** Just create a new repository and start fresh if secrets were exposed!

---

## 📚 Documentation Files to Include

Make sure these are in your repo:

- [x] `README.md` - Main documentation ✅
- [x] `requirements.txt` - Dependencies ✅
- [x] `.gitignore` - Ignore rules ✅
- [ ] `LICENSE` - Open source license (add above)
- [x] `.env.example` - Environment template
- [x] `QUICKSTART.md` - Quick start guide ✅
- [x] `NEO4J_DATA_SOURCE.md` - Data documentation ✅
- [x] `VERSION_STATUS_2025.md` - Version info ✅
- [x] `HOW_TO_VERIFY_REAL.md` - Verification guide ✅

---

## 🎯 Quick Command Reference

```powershell
# Check status
git status

# See what changed
git diff

# Add files
git add .

# Commit
git commit -m "Your message"

# Push to GitHub
git push

# Pull latest from GitHub
git pull

# Create new branch
git checkout -b branch-name

# Switch branches
git checkout main

# See commit history
git log --oneline

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard all local changes
git reset --hard HEAD
```

---

## 🆘 Troubleshooting

### Problem: "fatal: not a git repository"
**Solution:** Run `git init` first

### Problem: "failed to push some refs"
**Solution:** 
```powershell
git pull --rebase origin main
git push
```

### Problem: ".env file is visible on GitHub"
**Solution:**
```powershell
git rm --cached .env
git commit -m "Remove .env from tracking"
git push
# Change your Neo4j password!
```

### Problem: "Large file error"
**Solution:** Use Git LFS for files > 100MB:
```powershell
git lfs install
git lfs track "*.zip"
git add .gitattributes
git commit -m "Track large files with LFS"
```

### Problem: "Authentication failed"
**Solution:** Use Personal Access Token, not password
- GitHub → Settings → Developer settings → Personal access tokens

---

## 🌟 Making Your Repo Stand Out

### 1. Add Badges to README

```markdown
![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Neo4j](https://img.shields.io/badge/neo4j-5.x-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
```

### 2. Add Screenshots/Diagrams

- Training curves
- Neo4j graph visualizations
- Architecture diagrams

### 3. Add GitHub Actions (CI/CD)

Create `.github/workflows/test.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: pip install -r requirements.txt
      - run: pytest tests/
```

---

## 📞 Support & Community

After uploading:
- **Enable Issues** on GitHub for bug reports
- **Enable Discussions** for Q&A
- **Add CONTRIBUTING.md** if you want collaborators
- **Add CODE_OF_CONDUCT.md** for community guidelines

---

## ✅ Final Checklist

Before making repository public:

- [ ] All sensitive data removed (`.env` not committed)
- [ ] README.md is clear and complete
- [ ] Requirements.txt includes all dependencies
- [ ] .gitignore properly configured
- [ ] Code is tested and working
- [ ] Documentation files included
- [ ] License added
- [ ] .env.example created
- [ ] Repository description added
- [ ] Topics/tags added
- [ ] Personal information removed

---

## 🎓 For Research/Academic Use

If publishing this with a paper:

1. **Add DOI** (Digital Object Identifier) via Zenodo:
   - Connect GitHub to Zenodo
   - Create release → automatic DOI generation
   
2. **Update Citation** in README:
```bibtex
@software{auvap2025,
  author = {Your Name},
  title = {AUVAP: Automated Vulnerability Assessment Framework},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/YOUR_USERNAME/AUVAP},
  doi = {10.5281/zenodo.XXXXXXX}
}
```

3. **Link to Paper** (when published):
```markdown
## 📄 Research Paper

This code accompanies the paper:
**"AUVAP: Automated Vulnerability Assessment and Penetration Testing"**
Published in: [Conference/Journal Name]
[Link to paper]
```

---

**Good luck with your upload! 🚀**

If you encounter any issues, check the Troubleshooting section or open a GitHub Issue for help.
