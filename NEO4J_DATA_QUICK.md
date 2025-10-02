# Quick Answer: Where Does Neo4j Data Come From?

## Short Answer

The Neo4j knowledge graph gets **ALL its data from REAL Microsoft CyberBattleSim**:

1. **Initial network topology** - From CyberBattle environment creation
2. **Real-time observations** - From episode interactions  
3. **State changes** - From agent discoveries and compromises

**NO MOCK DATA - Everything is real cybersecurity simulation data!**

---

## Visual Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│ MICROSOFT CYBERBATTLESIM                                     │
│ (Real cyber attack simulator)                                │
│                                                              │
│ Creates network:                                             │
│   • start → 1_LinuxNode → 2_WindowsNode → 3_LinuxNode...   │
│   • Services: SSH, HTTP, RDP, MySQL on each node           │
│   • Vulnerabilities: CVE-2021-XXXX, CVE-2020-YYYY...       │
│   • Connections: Who connects to whom                       │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │ extract_topology()
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ AUVAP WRAPPER                                                │
│ (src/environment/cbs_wrapper.py)                            │
│                                                              │
│ Extracts:                                                    │
│   • Network structure                                        │
│   • Host properties                                          │
│   • Service information                                      │
│   • Vulnerability mappings                                   │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │ batch_create_network(topology)
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ NEO4J KNOWLEDGE GRAPH                                        │
│ (Cypher database)                                            │
│                                                              │
│ Creates:                                                     │
│   • (h:Host {id: "1_LinuxNode", discovered: false})         │
│   • (s:Service {id: "1_LinuxNode:SSH"})                     │
│   • (v:VulnerabilityTechnique {cve: "CVE-2021-XXXX"})      │
│   • (h)-[:RUNS]->(s)                                         │
│   • (s)-[:EXPOSES]->(v)                                      │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │ During episodes...
                   │
┌──────────────────▼───────────────────────────────────────────┐
│ REAL-TIME UPDATES                                            │
│                                                              │
│ Agent discovers node:                                        │
│   CyberBattle obs → SET h.discovered = true                 │
│                                                              │
│ Agent compromises node:                                      │
│   CyberBattle obs → SET h.owned = true, h.privilege = admin │
│                                                              │
│ Agent finds credentials:                                     │
│   CyberBattle obs → CREATE (:Credential) relationship       │
└──────────────────────────────────────────────────────────────┘
```

---

## See It In Action

### 1. Run the demonstration:
```powershell
.venv\Scripts\python.exe scripts\demo_neo4j_data.py
```

Shows:
- ✅ Real CyberBattle network with 8 nodes
- ✅ Network topology extraction
- ✅ Real-time observations
- ✅ Neo4j connection test

### 2. Read the full explanation:
See `NEO4J_DATA_SOURCE.md` for complete details with:
- Data schema
- Code examples
- Query examples
- Complete pipeline explanation

---

## Key Code Locations

### Where Data is Created
```python
# src/knowledge_graph/ckg_manager.py, line 256
def batch_create_network(self, topology: Dict[str, Any]):
    """Create entire network topology from CBS observation"""
    for host_id, host_data in topology.get('nodes', {}).items():
        # Creates (:Host) nodes from REAL CyberBattle
```

### Where Data is Updated
```python
# src/knowledge_graph/ckg_manager.py, line 237
def update_host_ownership(self, host_id: str, owned: bool, privilege: str):
    """Update host ownership status"""
    # Updates Neo4j with REAL discoveries from episodes
```

### Where Topology Comes From
```python
# src/environment/cbs_wrapper.py, line 80
env_spec = chainpattern.new_environment(size=6)  # ← REAL CyberBattle
env = CyberBattleEnv(env_spec, ...)              # ← Microsoft's simulator
```

---

## Example: Training Session Data Flow

```powershell
# Start training with Neo4j
.venv\Scripts\python.exe scripts\train_auvap.py --env chain --use-neo4j --episodes 10
```

What happens:

**Episode Start:**
```
1. CyberBattle creates 6-node chain network
2. AUVAP extracts topology
3. Neo4j creates 6 Host nodes (all discovered=false, owned=false)
4. Neo4j creates Service nodes for each host
5. Neo4j creates Vulnerability nodes
6. Neo4j creates relationship edges
```

**During Episode (each step):**
```
1. Agent takes action in REAL CyberBattle
2. CyberBattle returns observation
3. Observation parsed: "discovered_node_count: 2"
4. Neo4j updated: SET (n1:Host).discovered = true
5. Observation parsed: "owned_hosts: 1" 
6. Neo4j updated: SET (n1:Host).owned = true
```

**Real-time visualization:**
```cypher
// Query Neo4j during training to see live updates!
MATCH (h:Host)
RETURN h.id, h.discovered, h.owned
ORDER BY h.discovered DESC, h.owned DESC

// Results change as agents discover/compromise nodes!
```

---

## Verify It's Real Data

### Check 1: CyberBattle Package
```powershell
.venv\Scripts\pip show cyberbattle
# Shows: Microsoft's real package
```

### Check 2: Network Nodes
```powershell
.venv\Scripts\python.exe scripts\demo_neo4j_data.py
# Shows: Real node IDs like "1_LinuxNode", "2_WindowsNode"
```

### Check 3: Neo4j Browser
```
1. Open http://localhost:7474
2. Login: neo4j/auvap_password
3. Query: MATCH (n) RETURN n
4. See: Nodes created from REAL CyberBattle topology!
```

---

## Common Questions

**Q: Is the network topology hardcoded?**  
A: No! It's generated by Microsoft's CyberBattleSim dynamically.

**Q: Are the vulnerabilities fake?**  
A: No! They come from CyberBattle's vulnerability definitions (though CVE IDs may be simplified).

**Q: Do updates happen in real-time?**  
A: Yes! Every agent action updates the knowledge graph immediately.

**Q: Can I see the actual data?**  
A: Yes! Run `scripts/demo_neo4j_data.py` or query Neo4j directly.

**Q: What if Neo4j isn't running?**  
A: AUVAP still works! Neo4j is optional (use `--use-neo4j` flag to enable).

---

## Summary Table

| Data Element | Source | When Created | Where Stored |
|--------------|--------|--------------|--------------|
| Network nodes | CyberBattle environment | Episode start | `(:Host)` |
| Services | CyberBattle node properties | Episode start | `(:Service)` |
| Vulnerabilities | CyberBattle definitions | Episode start | `(:VulnerabilityTechnique)` |
| Connections | CyberBattle topology | Episode start | `[:CONNECTED_TO]` |
| Discovery status | Episode observations | Each step | `h.discovered` |
| Ownership status | Episode observations | Each step | `h.owned` |
| Privilege levels | Episode observations | Each step | `h.privilege` |
| Credentials | Episode observations | When found | `(:Credential)` |

**ALL FROM REAL CYBERBATTLE - NO MOCK DATA!**

---

## Files to Read

1. **`NEO4J_DATA_SOURCE.md`** - Complete explanation
2. **`scripts/demo_neo4j_data.py`** - Live demonstration
3. **`src/knowledge_graph/ckg_manager.py`** - Implementation
4. **`src/environment/cbs_wrapper.py`** - Data extraction

---

**Bottom Line:** Neo4j stores a real-time representation of Microsoft's CyberBattleSim state. All data is extracted from the actual simulation, updated live during episodes, and suitable for research!
