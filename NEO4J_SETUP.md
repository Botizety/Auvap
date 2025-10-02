# Neo4j Setup Guide for AUVAP

## The Issue

The error `The system cannot find the file specified` means Docker Desktop is not running on your Windows machine.

## Solution Options

### Option 1: Start Docker Desktop (Recommended for Full Features)

1. **Start Docker Desktop:**
   - Press `Windows key`
   - Search for "Docker Desktop"
   - Click to launch it
   - Wait for Docker to fully start (icon in system tray will stop animating)

2. **Verify Docker is Running:**
   ```powershell
   docker version
   # Should show Client and Server versions
   ```

3. **Run Neo4j Container:**
   ```powershell
   docker run -d `
     --name auvap-neo4j `
     -p 7474:7474 -p 7687:7687 `
     -e NEO4J_AUTH=neo4j/auvap_password `
     -v ${PWD}/neo4j-data:/data `
     neo4j:5.12
   ```

4. **Verify Neo4j is Running:**
   ```powershell
   docker ps
   # Should show auvap-neo4j container
   ```

5. **Access Neo4j Browser:**
   - Open: http://localhost:7474
   - Username: `neo4j`
   - Password: `auvap_password`

### Option 2: Install Docker Desktop (If Not Installed)

1. Download from: https://www.docker.com/products/docker-desktop/
2. Run installer
3. Restart computer if prompted
4. Follow Option 1 above

### Option 3: Use Neo4j Desktop (Alternative to Docker)

If you prefer not to use Docker:

1. **Download Neo4j Desktop:**
   - https://neo4j.com/download-center/#desktop
   - Free download, requires registration

2. **Install and Setup:**
   - Install Neo4j Desktop
   - Create a new database
   - Set password to `auvap_password`
   - Start the database

3. **Update Your .env File:**
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=auvap_password
   ```

4. **Test Connection:**
   ```powershell
   python tests/test_setup.py
   ```

### Option 4: Skip Neo4j (Testing Only)

**Good news:** Your AUVAP framework works perfectly without Neo4j for testing!

The Knowledge Graph features will be disabled, but you can still:
- ✅ Train Manager and Worker agents
- ✅ Test hierarchical coordination
- ✅ Use reward systems
- ✅ Run all episodes successfully

**Just run:**
```powershell
python scripts/train_auvap.py --episodes 10
# Notice: No --use-neo4j flag = runs without Neo4j
```

You already tested this successfully! 🎉

## What Each Option Gives You

| Feature | Without Neo4j | With Neo4j |
|---------|--------------|------------|
| Basic training | ✅ | ✅ |
| Manager-Worker agents | ✅ | ✅ |
| Reward systems | ✅ | ✅ |
| State tracking | ✅ | ✅ |
| **Action masking** | ❌ | ✅ |
| **CKG features** | ❌ | ✅ |
| **Explainability paths** | ❌ | ✅ |
| **Network topology storage** | ❌ | ✅ |

## Recommended Path for Your Situation

Since you're just getting started, I recommend:

### For Now: Test Without Neo4j ✅

You've already proven this works:

```powershell
# This is working perfectly!
python scripts/train_auvap.py --episodes 10
```

### When Ready: Add Neo4j

When you want to explore the full Knowledge Graph features:

1. **Start Docker Desktop** (easiest option)
2. **Run the Neo4j container** (see Option 1 above)
3. **Train with CKG enabled:**
   ```powershell
   python scripts/train_auvap.py --use-neo4j --episodes 100
   ```

## Quick Commands Reference

### Check Docker Status
```powershell
# Is Docker running?
docker version

# See running containers
docker ps

# See all containers (including stopped)
docker ps -a
```

### Start/Stop Neo4j Container
```powershell
# Start existing container
docker start auvap-neo4j

# Stop container
docker stop auvap-neo4j

# Remove container (to recreate)
docker rm auvap-neo4j

# View logs
docker logs auvap-neo4j
```

### AUVAP Training Commands
```powershell
# Without Neo4j (works now!)
python scripts/train_auvap.py --episodes 10

# With Neo4j (when ready)
python scripts/train_auvap.py --use-neo4j --episodes 100

# With CyberBattleSim environment
python scripts/train_auvap.py --env CyberBattleChain-v0 --episodes 50

# Full features
python scripts/train_auvap.py `
  --env CyberBattleChain-v0 `
  --use-neo4j `
  --episodes 1000 `
  --log-frequency 50
```

## Troubleshooting Docker

### Docker Desktop Won't Start

1. **Check Windows Services:**
   - Press `Windows + R`
   - Type: `services.msc`
   - Find "Docker Desktop Service"
   - Right-click → Start

2. **Check WSL2:**
   ```powershell
   wsl --status
   # Docker Desktop requires WSL2
   ```

3. **Reinstall Docker Desktop** if needed

### Port Already in Use

If you get "port already allocated" error:

```powershell
# Check what's using the port
netstat -ano | findstr "7687"

# Or use different ports
docker run -d `
  --name auvap-neo4j `
  -p 8474:7474 -p 8687:7687 `
  -e NEO4J_AUTH=neo4j/auvap_password `
  neo4j:5.12

# Update .env to use new ports:
# NEO4J_URI=bolt://localhost:8687
```

## Testing Your Setup

After setting up Neo4j (whichever option), test it:

```powershell
# 1. Verify installation
python tests/test_setup.py

# 2. Quick training test
python scripts/train_auvap.py --use-neo4j --episodes 5

# 3. Check Neo4j browser
# Open: http://localhost:7474
# Run query: MATCH (n) RETURN count(n)
```

## Summary

**Right now, you can:**
```powershell
# This works perfectly! ✅
python scripts/train_auvap.py --episodes 10
```

**When you want Neo4j features:**
1. Start Docker Desktop
2. Run the Neo4j container command from Option 1
3. Add `--use-neo4j` flag to training command

**No rush!** The framework is fully functional without Neo4j for learning and testing the hierarchical RL components.

---

Need help with any of these options? Just ask! 🚀
