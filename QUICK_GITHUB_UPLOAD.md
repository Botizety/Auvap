# 🚀 Quick GitHub Upload - Copy & Paste Commands

## Step 1: Initialize Git (Run Once)

```powershell
# Navigate to project
cd "c:\Users\kitti\OneDrive\เอกสาร\Cyber AUVAP"

# Initialize git
git init

# Configure git (replace with your info)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## Step 2: Add Files

```powershell
# Add all files (respects .gitignore)
git add .

# Check what will be committed (IMPORTANT!)
git status

# ⚠️ Make sure .env is NOT in the list!
# If you see .env, run:
# git rm --cached .env
```

---

## Step 3: Create First Commit

```powershell
git commit -m "Initial commit: AUVAP Framework

- Hierarchical RL with Manager-Worker architecture
- CyberBattleSim integration with real CBS API
- Neo4j knowledge graph for action masking
- Dual-signal reward system
- Verified and documented for 2025"
```

---

## Step 4: Create GitHub Repository

1. Go to: https://github.com/new
2. Repository name: `AUVAP` or `AUVAP-Framework`
3. Description: "Automated Vulnerability Assessment and Penetration Testing with Hierarchical RL"
4. Choose: ✅ Public or ⚠️ Private
5. **DO NOT** check "Initialize with README" (we already have files)
6. Click "Create repository"

---

## Step 5: Connect to GitHub

```powershell
# Replace YOUR_USERNAME with your GitHub username!
git remote add origin https://github.com/YOUR_USERNAME/AUVAP.git

# Verify
git remote -v
```

---

## Step 6: Push to GitHub

```powershell
# Rename branch to main
git branch -M main

# Push code
git push -u origin main
```

**Authentication:**
- Username: Your GitHub username
- Password: Use **Personal Access Token** (get it from GitHub → Settings → Developer settings → Personal access tokens)

---

## Step 7: Verify

Go to: https://github.com/YOUR_USERNAME/AUVAP

✅ Check:
- README.md displays
- Source code visible
- .gitignore present
- ❌ .env is NOT visible (good!)
- ❌ .venv/ is NOT visible (good!)

---

## 🎉 Done! Your Code is on GitHub!

---

## Future Updates (After Initial Upload)

```powershell
# Make changes to your code
# ... edit files ...

# Stage changes
git add .

# Commit with message
git commit -m "Description of what you changed"

# Push to GitHub
git push
```

---

## ⚠️ SECURITY CHECKLIST

Before pushing:
- [ ] `.env` file is in `.gitignore` ✅
- [ ] `.env` is NOT in `git status` output
- [ ] No passwords/secrets in code
- [ ] No personal information you don't want public

---

## 🆘 Quick Fixes

### "fatal: not a git repository"
```powershell
git init
```

### "failed to push"
```powershell
git pull --rebase origin main
git push
```

### ".env appeared on GitHub"
```powershell
git rm --cached .env
git commit -m "Remove sensitive file"
git push
# ⚠️ CHANGE YOUR NEO4J PASSWORD IMMEDIATELY!
```

---

## 📚 Files Ready for GitHub

✅ Your repository includes:
- `README.md` - Project documentation
- `requirements.txt` - Dependencies
- `.gitignore` - Ignore rules (updated)
- `.env.example` - Template for users
- `LICENSE` - MIT License
- `GITHUB_UPLOAD_GUIDE.md` - Detailed guide
- All source code in `src/`
- All scripts in `scripts/`
- All tests in `tests/`
- All documentation (NEO4J_DATA_SOURCE.md, etc.)

❌ These will NOT be uploaded (in .gitignore):
- `.env` - Your passwords
- `.venv/` - Virtual environment
- `__pycache__/` - Python cache
- `*.log` - Log files
- `checkpoints/` - Training checkpoints

---

## 📞 Need Help?

Read the detailed guide: `GITHUB_UPLOAD_GUIDE.md`

Or check GitHub's documentation: https://docs.github.com/en/get-started
