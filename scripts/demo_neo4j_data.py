"""
Demonstrate Neo4j Knowledge Graph Data Flow

Shows exactly where Neo4j data comes from:
1. CyberBattle environment topology
2. Real-time episode observations
3. Agent discoveries and actions
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.environment.cbs_wrapper import CyberBattleSimWrapper
from src.knowledge_graph.ckg_manager import CKGManager
from loguru import logger
import os

logger.remove()
logger.add(sys.stderr, level="INFO")

print("\n" + "="*80)
print("NEO4J KNOWLEDGE GRAPH DATA SOURCE DEMONSTRATION")
print("="*80 + "\n")

# Step 1: Create Real CyberBattle Environment
print("[STEP 1] Creating REAL CyberBattle Environment")
print("-" * 80)

env = CyberBattleSimWrapper(env_name='chain', size=6)
print(f"✓ Created 6-node chain network")

# Access internal CyberBattle environment
if hasattr(env.env, 'environment'):
    real_env = env.env.environment
    nodes = real_env.network.nodes
    print(f"✓ Real CyberBattle network has {len(nodes)} nodes")
    print(f"  Node IDs: {list(nodes.keys())}")
    print("\nThis is REAL Microsoft CyberBattle network topology!")
else:
    print("Could not access internal environment")

print()

# Step 2: Extract Topology Data
print("[STEP 2] Extracting Network Topology from CyberBattle")
print("-" * 80)

obs = env.reset()
topology = env.get_network_topology()

print("Topology extracted from REAL CyberBattle:")
print(f"  Discovered hosts: {topology['hosts']}")
print(f"  Owned hosts: {topology['owned_hosts']}")
print(f"  Services: {topology['services']}")
print(f"  Credentials: {topology['credentials']}")
print(f"  Connectivity: {topology['connectivity']}")

print("\nThis data comes from Microsoft's CyberBattleSim environment state!")
print()

# Step 3: Show What Would Be Sent to Neo4j
print("[STEP 3] Data That Would Be Sent to Neo4j")
print("-" * 80)

if hasattr(env.env, 'environment'):
    real_env = env.env.environment
    
    print("\nNodes that would be created in Neo4j:")
    for node_id, node_data in real_env.network.nodes.items():
        print(f"\n  Host Node: {node_id}")
        if hasattr(node_data, 'properties'):
            props = node_data.properties
            print(f"    Properties: {props}")
        if hasattr(node_data, 'services'):
            print(f"    Services: {list(node_data.services.keys())}")
        if hasattr(node_data, 'value'):
            print(f"    Value: {node_data.value}")
    
    print("\nConnections that would be created:")
    edges = real_env.network.edges()
    for source, target in list(edges)[:5]:  # Show first 5
        print(f"  {source} → {target}")

print("\nAll this data comes from REAL CyberBattle, not mock!")
print()

# Step 4: Simulate Episode and Show Real-Time Data
print("[STEP 4] Running Episode - Real-Time Data Updates")
print("-" * 80)

print("\nTaking 10 actions in REAL CyberBattle environment...")
print("Watch how real observations would update Neo4j:\n")

for step in range(10):
    action = env.action_space.sample()
    obs, reward, done, info = env.step(action)
    
    # Get current state from REAL CyberBattle
    net_state = env.network_state
    
    discovered = len(net_state.discovered_hosts)
    owned = len(net_state.owned_hosts)
    services = len(net_state.discovered_services)
    
    print(f"Step {step+1}:")
    print(f"  Discovered hosts: {discovered}")
    print(f"  Owned hosts: {owned}")
    print(f"  Services found: {services}")
    
    if reward != 0:
        print(f"  → Reward received: {reward:.2f} (Real CyberBattle reward!)")
    
    # This is the data that would update Neo4j
    print(f"  → Neo4j would update: discovered={discovered}, owned={owned}")
    print()
    
    if discovered > 0:
        print("  ✓ REAL discovery happened! This would update Neo4j:")
        print(f"    MATCH (h:Host) SET h.discovered = true")
        break

print("\nAll updates come from REAL CyberBattle observations!")
print()

# Step 5: Show Neo4j Connection (if available)
print("[STEP 5] Neo4j Connection Test")
print("-" * 80)

neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')

try:
    ckg = CKGManager(uri=neo4j_uri)
    
    if ckg.connect():
        print(f"✓ Connected to Neo4j at {neo4j_uri}")
        
        # Show current stats
        stats = ckg.get_graph_stats()
        print(f"\nCurrent graph stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n" + "-" * 80)
        print("DEMO: Creating Nodes from Real CyberBattle Data")
        print("-" * 80)
        
        # Example: Create a host node with REAL data
        if hasattr(env.env, 'environment'):
            real_env = env.env.environment
            
            # Get first node from REAL CyberBattle
            node_id = list(real_env.network.nodes.keys())[0]
            node_data = real_env.network.nodes[node_id]
            
            print(f"\nCreating Neo4j node from REAL CyberBattle node: {node_id}")
            
            # This is how real data flows to Neo4j
            from src.knowledge_graph.ckg_schema import HostEntity
            
            host = HostEntity(
                host_id=node_id,
                os_type=getattr(node_data.properties, 'os', 'Unknown') if hasattr(node_data, 'properties') else 'Unknown',
                value=getattr(node_data, 'value', 0) if hasattr(node_data, 'value') else 0,
                discovered=False,
                owned=False
            )
            
            # Create in Neo4j
            success = ckg.create_entity(host)
            
            if success:
                print(f"✓ Created in Neo4j: Host(id={node_id})")
                print(f"  Data source: Microsoft CyberBattleSim node")
                print(f"  Properties: {host.properties}")
            
            # Verify it's there
            hosts = ckg.get_all_hosts()
            print(f"\nTotal hosts in Neo4j: {len(hosts)}")
            
            # Clean up demo data
            print("\nCleaning up demo data...")
            ckg.execute_query(f"MATCH (h:Host {{id: '{node_id}'}}) DELETE h", write=True)
        
        ckg.close()
        print("\n✓ Neo4j connection test complete!")
    else:
        print(f"✗ Could not connect to Neo4j at {neo4j_uri}")
        print("  Start Neo4j: docker start auvap-neo4j")
        print("  Or create: docker run -d --name auvap-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/auvap_password neo4j:5.12")

except Exception as e:
    print(f"✗ Neo4j not available: {e}")
    print("\nThat's OK - Neo4j is optional!")
    print("But when enabled, it receives REAL data from CyberBattle!")

print()

env.close()

# Summary
print("="*80)
print("SUMMARY: Neo4j Data Sources")
print("="*80)
print("""
The Neo4j knowledge graph gets data from THREE real sources:

1. CYBERBATTLE ENVIRONMENT TOPOLOGY
   - Network structure (nodes, connections)
   - Services on each host
   - Vulnerabilities in services
   - Initial network properties
   → Source: Microsoft CyberBattleSim environment spec

2. REAL-TIME EPISODE OBSERVATIONS
   - Discovered nodes
   - Compromised hosts
   - Found credentials
   - Privilege levels
   → Source: CyberBattle observations during training

3. AGENT ACTIONS & STATE CHANGES
   - Attack decisions
   - Exploitation results
   - Network traversal
   - Success/failure outcomes
   → Source: Agent interactions with CyberBattle

ALL DATA IS REAL - NO MOCK DATA!

The knowledge graph is a real-time representation of the
actual Microsoft CyberBattleSim simulation state!
""")
print("="*80 + "\n")

print("✓ Demonstration complete!")
print("\nFor more details, see: NEO4J_DATA_SOURCE.md\n")
