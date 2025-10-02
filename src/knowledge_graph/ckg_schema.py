"""
Cybersecurity Knowledge Graph Schema

Defines the 6-entity CKG schema for AUVAP:
1. Host - Network nodes (servers, workstations, etc.)
2. Service - Running services (HTTP, SSH, SMB, etc.)
3. SoftwareStack - Software/OS/libraries with versions
4. VulnerabilityTechnique - CVEs and exploit techniques
5. Ability - Actions/tools the agent can use
6. Credential - Authentication credentials

Relationships encode preconditions, effects, and dependencies.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class EntityType(Enum):
    """Types of entities in the CKG"""
    HOST = "Host"
    SERVICE = "Service"
    SOFTWARE_STACK = "SoftwareStack"
    VULNERABILITY_TECHNIQUE = "VulnerabilityTechnique"
    ABILITY = "Ability"
    CREDENTIAL = "Credential"


class RelationType(Enum):
    """Types of relationships in the CKG"""
    # Host relationships
    RUNS = "RUNS"  # Host -> Service
    HAS_STACK = "HAS_STACK"  # Host -> SoftwareStack
    CONNECTED_TO = "CONNECTED_TO"  # Host -> Host
    OWNED = "OWNED"  # Agent -> Host (ownership)
    
    # Service relationships
    EXPOSES = "EXPOSES"  # Service -> VulnerabilityTechnique
    REQUIRES_STACK = "REQUIRES_STACK"  # Service -> SoftwareStack
    
    # Vulnerability relationships
    AFFECTS = "AFFECTS"  # VulnerabilityTechnique -> SoftwareStack
    EXPLOITED_BY = "EXPLOITED_BY"  # VulnerabilityTechnique -> Ability
    
    # Ability relationships
    TARGETS = "TARGETS"  # Ability -> Service
    REQUIRES_CREDENTIAL = "REQUIRES_CREDENTIAL"  # Ability -> Credential
    GRANTS_CREDENTIAL = "GRANTS_CREDENTIAL"  # Ability -> Credential
    
    # Credential relationships
    VALID_FOR = "VALID_FOR"  # Credential -> Host
    GRANTS_ACCESS = "GRANTS_ACCESS"  # Credential -> Service


@dataclass
class Entity:
    """Base entity in the CKG"""
    entity_type: EntityType
    entity_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_cypher_create(self) -> str:
        """Generate Cypher CREATE statement"""
        props = ", ".join([f"{k}: ${k}" for k in self.properties.keys()])
        return f"CREATE (n:{self.entity_type.value} {{id: $id, {props}}})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': self.entity_type.value,
            'id': self.entity_id,
            **self.properties
        }


@dataclass
class Relationship:
    """Relationship between entities in the CKG"""
    rel_type: RelationType
    source_id: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_cypher_create(self, source_label: str, target_label: str) -> str:
        """Generate Cypher CREATE relationship statement"""
        props = ""
        if self.properties:
            prop_str = ", ".join([f"{k}: ${k}" for k in self.properties.keys()])
            props = f" {{{prop_str}}}"
        
        return (
            f"MATCH (a:{source_label} {{id: $source_id}}), "
            f"(b:{target_label} {{id: $target_id}}) "
            f"CREATE (a)-[r:{self.rel_type.value}{props}]->(b)"
        )


@dataclass
class HostEntity(Entity):
    """Host entity - represents a network node"""
    def __init__(self, host_id: str, os_type: str = "Unknown", 
                 value: int = 0, discovered: bool = False, 
                 owned: bool = False, privilege: str = "none"):
        super().__init__(
            entity_type=EntityType.HOST,
            entity_id=host_id,
            properties={
                'os_type': os_type,
                'value': value,
                'discovered': discovered,
                'owned': owned,
                'privilege': privilege
            }
        )


@dataclass
class ServiceEntity(Entity):
    """Service entity - represents a running service"""
    def __init__(self, service_id: str, service_name: str, 
                 port: Optional[int] = None, version: Optional[str] = None):
        super().__init__(
            entity_type=EntityType.SERVICE,
            entity_id=service_id,
            properties={
                'name': service_name,
                'port': port,
                'version': version
            }
        )


@dataclass
class SoftwareStackEntity(Entity):
    """Software Stack entity - represents software/OS/library"""
    def __init__(self, stack_id: str, name: str, version: str, 
                 cpe: Optional[str] = None):
        super().__init__(
            entity_type=EntityType.SOFTWARE_STACK,
            entity_id=stack_id,
            properties={
                'name': name,
                'version': version,
                'cpe': cpe
            }
        )


@dataclass
class VulnerabilityEntity(Entity):
    """Vulnerability entity - represents CVE or exploit technique"""
    def __init__(self, vuln_id: str, cve_id: Optional[str] = None,
                 cvss_score: float = 0.0, exploit_type: str = "unknown",
                 requires_auth: bool = False):
        super().__init__(
            entity_type=EntityType.VULNERABILITY_TECHNIQUE,
            entity_id=vuln_id,
            properties={
                'cve_id': cve_id,
                'cvss_score': cvss_score,
                'exploit_type': exploit_type,
                'requires_auth': requires_auth
            }
        )


@dataclass
class AbilityEntity(Entity):
    """Ability entity - represents an action/tool the agent can use"""
    def __init__(self, ability_id: str, action_type: str, tool_name: str,
                 cost: float = 1.0, noise_level: float = 0.5,
                 success_rate: float = 0.8, requires_cred: bool = False):
        super().__init__(
            entity_type=EntityType.ABILITY,
            entity_id=ability_id,
            properties={
                'action_type': action_type,  # local, remote, connect
                'tool_name': tool_name,  # nmap, metasploit, etc.
                'cost': cost,
                'noise_level': noise_level,
                'success_rate': success_rate,
                'requires_cred': requires_cred
            }
        )


@dataclass
class CredentialEntity(Entity):
    """Credential entity - represents authentication credential"""
    def __init__(self, cred_id: str, cred_type: str, username: Optional[str] = None,
                 scope: Optional[List[str]] = None):
        super().__init__(
            entity_type=EntityType.CREDENTIAL,
            entity_id=cred_id,
            properties={
                'type': cred_type,  # password, hash, token, key
                'username': username,
                'scope': scope or []
            }
        )


class CKGSchema:
    """
    Defines the complete Cybersecurity Knowledge Graph schema
    
    Provides:
    - Entity and relationship definitions
    - Cypher queries for schema creation
    - Constraint and index definitions
    - Schema validation
    """
    
    @staticmethod
    def get_schema_creation_queries() -> List[str]:
        """Get Cypher queries to create the CKG schema"""
        queries = []
        
        # Create constraints (unique IDs)
        for entity_type in EntityType:
            queries.append(
                f"CREATE CONSTRAINT IF NOT EXISTS "
                f"FOR (n:{entity_type.value}) "
                f"REQUIRE n.id IS UNIQUE"
            )
        
        # Create indexes for common queries
        queries.extend([
            # Host indexes
            "CREATE INDEX IF NOT EXISTS FOR (h:Host) ON (h.owned)",
            "CREATE INDEX IF NOT EXISTS FOR (h:Host) ON (h.discovered)",
            
            # Service indexes
            "CREATE INDEX IF NOT EXISTS FOR (s:Service) ON (s.name)",
            
            # Vulnerability indexes
            "CREATE INDEX IF NOT EXISTS FOR (v:VulnerabilityTechnique) ON (v.cve_id)",
            "CREATE INDEX IF NOT EXISTS FOR (v:VulnerabilityTechnique) ON (v.cvss_score)",
            
            # Ability indexes
            "CREATE INDEX IF NOT EXISTS FOR (a:Ability) ON (a.action_type)",
            "CREATE INDEX IF NOT EXISTS FOR (a:Ability) ON (a.requires_cred)",
        ])
        
        return queries
    
    @staticmethod
    def get_all_entity_types() -> List[EntityType]:
        """Get list of all entity types"""
        return list(EntityType)
    
    @staticmethod
    def get_all_relationship_types() -> List[RelationType]:
        """Get list of all relationship types"""
        return list(RelationType)
    
    @staticmethod
    def validate_entity(entity: Entity) -> bool:
        """Validate entity has required properties"""
        if not entity.entity_id:
            return False
        if not entity.entity_type:
            return False
        return True
    
    @staticmethod
    def validate_relationship(rel: Relationship) -> bool:
        """Validate relationship has required properties"""
        if not rel.source_id or not rel.target_id:
            return False
        if not rel.rel_type:
            return False
        return True


# Example CKG structure for reference
EXAMPLE_CKG = """
# Example Knowledge Graph Structure

# Hosts
(client:Host {id: 'client', os: 'Windows10', owned: true})
(web:Host {id: 'web-01', os: 'Ubuntu20', discovered: true})
(db:Host {id: 'db-01', os: 'Ubuntu20', discovered: false})

# Services  
(http:Service {id: 'web-01:http', name: 'apache', port: 80, version: '2.4.41'})
(mysql:Service {id: 'db-01:mysql', name: 'mysql', port: 3306, version: '8.0'})

# Software Stacks
(apache_stack:SoftwareStack {id: 'apache-2.4.41', name: 'Apache', version: '2.4.41'})
(mysql_stack:SoftwareStack {id: 'mysql-8.0', name: 'MySQL', version: '8.0'})

# Vulnerabilities
(cve1:VulnerabilityTechnique {id: 'CVE-2021-1234', cvss: 7.5, type: 'RCE'})
(cve2:VulnerabilityTechnique {id: 'CVE-2021-5678', cvss: 9.8, type: 'SQLi'})

# Abilities
(scan:Ability {id: 'nmap_scan', type: 'remote', tool: 'nmap', cost: 0.5, noise: 0.3})
(exploit:Ability {id: 'exploit_http', type: 'remote', tool: 'metasploit', cost: 2.0, noise: 0.8})

# Credentials
(admin_cred:Credential {id: 'admin_pass', type: 'password', username: 'admin'})

# Relationships
(client)-[:CONNECTED_TO]->(web)
(web)-[:CONNECTED_TO]->(db)
(web)-[:RUNS]->(http)
(db)-[:RUNS]->(mysql)
(http)-[:REQUIRES_STACK]->(apache_stack)
(apache_stack)-[:AFFECTED_BY]->(cve1)
(cve1)-[:EXPLOITED_BY]->(exploit)
(exploit)-[:TARGETS]->(http)
(exploit)-[:GRANTS_CREDENTIAL]->(admin_cred)
(admin_cred)-[:VALID_FOR]->(web)
"""


if __name__ == "__main__":
    # Test schema
    print("=== CKG Schema ===\n")
    
    # Create example entities
    host = HostEntity("web-01", os_type="Ubuntu20", value=50)
    service = ServiceEntity("web-01:http", "apache", port=80, version="2.4.41")
    vuln = VulnerabilityEntity("CVE-2021-1234", cvss_score=7.5)
    ability = AbilityEntity("nmap_scan", "remote", "nmap", cost=0.5, noise_level=0.3)
    
    print("Example Host:", host.to_dict())
    print("Example Service:", service.to_dict())
    print("Example Vulnerability:", vuln.to_dict())
    print("Example Ability:", ability.to_dict())
    
    # Print schema creation queries
    print("\n=== Schema Creation Queries ===")
    schema = CKGSchema()
    for i, query in enumerate(schema.get_schema_creation_queries(), 1):
        print(f"{i}. {query}")
    
    print("\n=== Example CKG Structure ===")
    print(EXAMPLE_CKG)
