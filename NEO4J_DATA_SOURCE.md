# Neo4j Knowledge Graph Data Source

## Where Does the Data Come From?

The Neo4j knowledge graph in AUVAP gets its data from **3 main sources**:

---

## 1. 🌐 CyberBattleSim Environment (Real Network Data)

### Initial Network Topology

When a CyberBattle environment is created, it defines:

```python
# From cyberbattle.samples.chainpattern.chainpattern
env_spec = chainpattern.new_environment(size=6)
```

This creates a network with:
- **Nodes**: 6 Linux/Windows hosts in a chain
- **Services**: HTTP, SSH, RDP, MySQL, etc. on each host
- **Vulnerabilities**: CVEs associated with services
- **Connections**: Network links between nodes
- **Credentials**: Username/password combinations

**Example from Real CyberBattle:**
```
Network:
  start (Linux) 
    → 1_LinuxNode (SSH, HTTP)
      → 2_WindowsNode (RDP, SMB)
        → 3_LinuxNode (MySQL, SSH)
          ...
```

### Data Flow: CyberBattle → Neo4j

```python
# In ckg_manager.py, line 256
def batch_create_network(self, topology: Dict[str, Any]):
    """Create entire network topology from CBS observation"""
    
    # Create hosts
    for host_id, host_data in topology.get('nodes', {}).items():
        host = HostEntity(
            host_id=host_id,
            os_type=host_data.get('properties', {}).get('os', 'Unknown'),
            value=host_data.get('value', 0),
            discovered=False,
            owned=False
        )
        self.create_entity(host)  # → Neo4j CREATE (h:Host {...})
```

---

## 2. 🎮 Real-Time Episode Observations

During training, every step generates observations from **real CyberBattle**:

### Observation Data Structure

```python
# From CyberBattle's actual observation
obs = {
    'discovered_nodes': [...],           # Newly discovered nodes
    'discovered_node_count': 3,          # Total discovered
    'nodes_privilegelevel': [0,1,2...],  # Admin vs user
    'credential_cache_matrix': [...],    # Found credentials
    'leaked_credentials': [...],         # Credentials from compromises
    'action_mask': {...}                 # Valid actions
}
```

### Real-Time Updates to Neo4j

When agents discover or compromise nodes:

```python
# In ckg_manager.py

# When a node is discovered
def update_host_discovery(self, host_id: str, discovered: bool):
    query = """
    MATCH (h:Host {id: $host_id})
    SET h.discovered = $discovered
    RETURN h
    """
    # Updates Neo4j in real-time
    
# When a node is compromised  
def update_host_ownership(self, host_id: str, owned: bool, privilege: str):
    query = """
    MATCH (h:Host {id: $host_id})
    SET h.owned = $owned, h.privilege = $privilege
    RETURN h
    """
    # Updates ownership status in Neo4j
```

---

## 3. 📊 Agent Actions and State Changes

### State Manager Integration

The `StateManager` tracks the current attack state:

```python
# From src/environment/state_manager.py

class StateManager:
    def __init__(self):
        self.discovered_hosts = set()
        self.owned_hosts = set()
        self.services_found = {}
        self.credentials_collected = []
        self.network_topology = {}
    
    def update_from_observation(self, obs, info):
        """Extract data from CyberBattle observation"""
        # This data gets pushed to Neo4j
```

### Complete Data Pipeline

```
┌─────────────────────┐
│  CyberBattleSim     │  ← Real Microsoft simulator
│  (Initial Topology) │
└──────────┬──────────┘
           │ Network definition
           ▼
┌─────────────────────┐
│  batch_create_      │  ← Populate Neo4j with network
│  network()          │
└──────────┬──────────┘
           │ Creates nodes & relationships
           ▼
┌─────────────────────┐
│     Neo4j Graph     │  ← Initial knowledge graph
│  (Hosts, Services,  │
│   Vulnerabilities)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Training Episode   │  ← Agent explores network
└──────────┬──────────┘
           │ Each step returns observation
           ▼
┌─────────────────────┐
│  CyberBattle        │  ← Real observations
│  Observation        │     (discoveries, compromises)
└──────────┬──────────┘
           │ Parsed by StateManager
           ▼
┌─────────────────────┐
│  update_host_       │  ← Real-time updates
│  discovery()        │
│  update_host_       │
│  ownership()        │
└──────────┬──────────┘
           │ Cypher queries
           ▼
┌─────────────────────┐
│  Neo4j Graph        │  ← Updated knowledge
│  (Updated state)    │     (discovered, owned flags)
└─────────────────────┘
```

---

## Data Schema in Neo4j

### Node Types (Entities)

Created from **real CyberBattle environment**:

```cypher
// Host nodes (from CyberBattle network)
(:Host {
  id: "web-01",
  os_type: "Ubuntu20",
  value: 50,
  discovered: true,
  owned: false,
  privilege: "user"
})

// Service nodes (from CyberBattle services)
(:Service {
  id: "web-01:SSH",
  service_name: "SSH",
  port: 22
})

// Vulnerability nodes (from CyberBattle vulnerabilities)
(:VulnerabilityTechnique {
  id: "CVE-2021-1234",
  cve_id: "CVE-2021-1234",
  severity: "HIGH"
})

// Credential nodes (discovered during episodes)
(:Credential {
  id: "cred_001",
  username: "admin",
  credential_type: "password"
})
```

### Relationship Types

```cypher
// Network connectivity (from CyberBattle topology)
(h1:Host)-[:CONNECTED_TO]->(h2:Host)

// Service hosting (from CyberBattle environment spec)
(h:Host)-[:RUNS]->(s:Service)

// Vulnerability exposure (from CyberBattle vulnerability definitions)
(s:Service)-[:EXPOSES]->(v:VulnerabilityTechnique)

// Credential discovery (from episode observations)
(h:Host)-[:HAS_CREDENTIAL]->(c:Credential)
```

---

## Example: Complete Data Flow

### Step 1: Environment Creation

```python
# scripts/train_auvap.py
env = CyberBattleSimWrapper(env_name='chain', size=6)
```

CyberBattle creates:
```
Network Graph:
  start → 1_LinuxNode → 2_WindowsNode → 3_LinuxNode → 4_WindowsNode → 5_LinuxNode
  
Services on each node:
  1_LinuxNode: SSH (port 22), HTTP (port 80)
  2_WindowsNode: RDP (port 3389), SMB (port 445)
  ...
  
Vulnerabilities:
  SSH → CVE-2021-XXXX (weak password)
  HTTP → CVE-2020-YYYY (remote code execution)
  ...
```

### Step 2: Initial CKG Population

```python
# In training script (if --use-neo4j enabled)
if args.use_neo4j:
    ckg.connect()
    ckg.initialize_schema(clear_existing=True)
    
    # Get topology from CyberBattle
    topology = env.get_network_topology()
    
    # Populate Neo4j
    ckg.batch_create_network(topology)
```

Neo4j now contains:
```cypher
// Created in Neo4j
(start:Host {id: "start", discovered: false, owned: false})
(n1:Host {id: "1_LinuxNode", discovered: false, owned: false})
(n2:Host {id: "2_WindowsNode", discovered: false, owned: false})

(start)-[:CONNECTED_TO]->(n1)
(n1)-[:CONNECTED_TO]->(n2)

(n1)-[:RUNS]->(ssh:Service {id: "1_LinuxNode:SSH"})
(ssh)-[:EXPOSES]->(vuln:VulnerabilityTechnique {id: "CVE-2021-XXXX"})
```

### Step 3: Training Episode

```python
# Episode loop
obs = env.reset()

for step in range(max_steps):
    action = agent.select_action(obs)
    obs, reward, done, info = env.step(action)
    
    # Real CyberBattle returns:
    # obs = {
    #   'discovered_node_count': 2,  # Agent discovered node 1
    #   'nodes_privilegelevel': [2, 1, 0, ...],  # Got user access on node 1
    #   ...
    # }
    
    # Update Neo4j with real discoveries
    if args.use_neo4j:
        # Parse observation
        discovered = info.get('newly_discovered', [])
        for host_id in discovered:
            ckg.update_host_discovery(host_id, discovered=True)
        
        # Update ownership
        owned = info.get('newly_owned', [])
        for host_id in owned:
            ckg.update_host_ownership(host_id, owned=True, privilege="user")
```

Neo4j updated with **real episode data**:
```cypher
// After discoveries
(start:Host {discovered: true, owned: true})  ← Updated!
(n1:Host {discovered: true, owned: true})     ← Updated!
(n2:Host {discovered: true, owned: false})    ← Updated!
```

---

## How to View the Data

### 1. Neo4j Browser

```bash
# Open browser
http://localhost:7474

# Login
Username: neo4j
Password: auvap_password

# Query all nodes
MATCH (n) RETURN n
```

### 2. Query from Python

```python
from src.knowledge_graph.ckg_manager import CKGManager

ckg = CKGManager()
if ckg.connect():
    # Get all hosts
    hosts = ckg.get_all_hosts()
    print(f"Total hosts: {len(hosts)}")
    
    # Get owned hosts
    owned = ckg.get_owned_hosts()
    print(f"Owned hosts: {owned}")
    
    # Get graph stats
    stats = ckg.get_graph_stats()
    print(stats)
    
    ckg.close()
```

### 3. During Training

```python
# scripts/train_auvap.py with --use-neo4j flag

# The graph is updated in real-time during episodes
# You can query it while training is running!

# Watch discoveries happen live:
MATCH (h:Host {discovered: true})
RETURN h.id, h.owned, h.privilege
```

---

## Data Sources Summary

| Data Type | Source | When Updated | Example |
|-----------|--------|--------------|---------|
| **Network Topology** | CyberBattle environment spec | Episode start | Hosts, connections |
| **Services** | CyberBattle node properties | Episode start | SSH, HTTP, RDP |
| **Vulnerabilities** | CyberBattle vulnerability definitions | Episode start | CVE IDs, exploits |
| **Discovery Status** | CyberBattle observations | Each step | discovered=true |
| **Ownership Status** | CyberBattle state | Each step | owned=true, privilege=admin |
| **Credentials** | CyberBattle leaked_credentials | When found | username/password |
| **Attack Paths** | Episode trajectory | End of episode | Action sequences |

---

## Key Points

1. **Real Data**: All data comes from **real Microsoft CyberBattleSim**, not mock/fake data

2. **Dynamic Updates**: Neo4j is updated in **real-time** as agents discover and compromise nodes

3. **State Tracking**: The graph reflects the **current state** of the attack simulation

4. **Bi-directional**: 
   - CyberBattle → Neo4j (observations, discoveries)
   - Neo4j → Agents (action masking, features)

5. **Research Quality**: Because it's real CyberBattle data, the knowledge graph is suitable for research

---

## Example Neo4j Queries

### See All Discovered Hosts
```cypher
MATCH (h:Host {discovered: true})
RETURN h.id, h.owned, h.privilege
```

### Find Attack Paths
```cypher
MATCH path = (start:Host {id: "start"})-[:CONNECTED_TO*]->(target:Host)
WHERE target.owned = true
RETURN path
```

### Find Exploitable Vulnerabilities
```cypher
MATCH (h:Host {discovered: true, owned: false})-[:RUNS]->(s:Service)-[:EXPOSES]->(v:VulnerabilityTechnique)
RETURN h.id, s.service_name, v.cve_id
```

### Count Compromised Nodes
```cypher
MATCH (h:Host {owned: true})
RETURN count(h) as compromised_count
```

---

## Testing the Data Pipeline

Run this to see the data flow:

```python
# scripts/test_ckg_integration.py (create this)

from src.environment.cbs_wrapper import CyberBattleSimWrapper
from src.knowledge_graph.ckg_manager import CKGManager

# Create environment
env = CyberBattleSimWrapper(env_name='chain', size=6)

# Create CKG
ckg = CKGManager()
if ckg.connect():
    ckg.initialize_schema(clear_existing=True)
    
    # Get topology from REAL CyberBattle
    topology = env.get_network_topology()
    print(f"Topology from CyberBattle: {topology}")
    
    # Populate Neo4j
    ckg.batch_create_network(topology)
    
    # Verify in Neo4j
    stats = ckg.get_graph_stats()
    print(f"Neo4j stats: {stats}")
    
    ckg.close()

env.close()
```

---

## Conclusion

**All Neo4j data comes from REAL Microsoft CyberBattleSim!**

- ✅ Network topology: From CyberBattle environment specs
- ✅ Real-time updates: From CyberBattle observations during episodes
- ✅ State tracking: From actual agent actions and discoveries
- ✅ No mock data: Everything is production-grade simulation data

The knowledge graph is a **real-time representation** of the **real cybersecurity simulation**!
