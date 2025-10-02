"""
Cybersecurity Knowledge Graph Manager

Manages Neo4j connection and graph operations:
- Initialize database connection
- Create/update/query entities and relationships
- Populate graph from CyberBattleSim observations
- Real-time updates during episode execution
- Provide graph queries for action masking and feature extraction
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError

from .ckg_schema import (
    Entity, Relationship, CKGSchema,
    HostEntity, ServiceEntity, SoftwareStackEntity,
    VulnerabilityEntity, AbilityEntity, CredentialEntity,
    RelationType, EntityType
)


class CKGManager:
    """
    Manages the Cybersecurity Knowledge Graph in Neo4j
    
    Responsibilities:
    - Database connection management
    - Schema initialization
    - Entity and relationship CRUD operations
    - Batch updates from CBS observations
    - Query execution for action masking and features
    """
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j"
    ):
        """
        Initialize CKG Manager
        
        Args:
            uri: Neo4j connection URI (default: from env NEO4J_URI)
            username: Neo4j username (default: from env NEO4J_USER)
            password: Neo4j password (default: from env NEO4J_PASSWORD)
            database: Database name (default: 'neo4j')
        """
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = username or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'password')
        self.database = database
        
        self.driver: Optional[Driver] = None
        self.connected = False
        
        logger.info(f"CKGManager initialized for {self.uri}")
    
    def connect(self) -> bool:
        """
        Establish connection to Neo4j database
        
        Returns:
            True if connection successful
        """
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            
            # Verify connection
            self.driver.verify_connectivity()
            self.connected = True
            
            logger.info("Successfully connected to Neo4j")
            return True
            
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.connected = False
            return False
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            self.connected = False
            logger.info("Neo4j connection closed")
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        write: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            write: If True, use write transaction
        
        Returns:
            List of result records as dictionaries
        """
        if not self.connected or not self.driver:
            logger.error("Not connected to Neo4j")
            return []
        
        parameters = parameters or {}
        
        def _execute(tx):
            result = tx.run(query, parameters)
            return [dict(record) for record in result]
        
        try:
            with self.driver.session(database=self.database) as session:
                if write:
                    return session.execute_write(_execute)
                else:
                    return session.execute_read(_execute)
        
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Query: {query}, Parameters: {parameters}")
            return []
    
    def initialize_schema(self, clear_existing: bool = False):
        """
        Initialize the CKG schema in Neo4j
        
        Args:
            clear_existing: If True, clear all existing data first
        """
        if not self.connected:
            logger.error("Cannot initialize schema: not connected")
            return
        
        logger.info("Initializing CKG schema...")
        
        # Clear existing data if requested
        if clear_existing:
            logger.warning("Clearing all existing data...")
            self.execute_query("MATCH (n) DETACH DELETE n", write=True)
        
        # Create schema (constraints and indexes)
        schema = CKGSchema()
        for query in schema.get_schema_creation_queries():
            self.execute_query(query, write=True)
        
        logger.info("CKG schema initialized successfully")
    
    def create_entity(self, entity: Entity) -> bool:
        """
        Create an entity in the graph
        
        Args:
            entity: Entity object to create
        
        Returns:
            True if successful
        """
        # MERGE to avoid duplicates
        query = f"""
        MERGE (n:{entity.entity_type.value} {{id: $id}})
        SET n += $properties
        RETURN n
        """
        
        params = {
            'id': entity.entity_id,
            'properties': entity.properties
        }
        
        result = self.execute_query(query, params, write=True)
        
        if result:
            logger.debug(f"Created/updated entity: {entity.entity_type.value}:{entity.entity_id}")
            return True
        return False
    
    def create_relationship(
        self,
        rel: Relationship,
        source_type: EntityType,
        target_type: EntityType
    ) -> bool:
        """
        Create a relationship between entities
        
        Args:
            rel: Relationship object
            source_type: Type of source entity
            target_type: Type of target entity
        
        Returns:
            True if successful
        """
        query = f"""
        MATCH (a:{source_type.value} {{id: $source_id}})
        MATCH (b:{target_type.value} {{id: $target_id}})
        MERGE (a)-[r:{rel.rel_type.value}]->(b)
        SET r += $properties
        RETURN r
        """
        
        params = {
            'source_id': rel.source_id,
            'target_id': rel.target_id,
            'properties': rel.properties
        }
        
        result = self.execute_query(query, params, write=True)
        
        if result:
            logger.debug(f"Created relationship: {rel.source_id}-[{rel.rel_type.value}]->{rel.target_id}")
            return True
        return False
    
    def update_host_ownership(self, host_id: str, owned: bool, privilege: str = "user"):
        """Update host ownership status"""
        query = """
        MATCH (h:Host {id: $host_id})
        SET h.owned = $owned, h.privilege = $privilege
        RETURN h
        """
        
        self.execute_query(query, {
            'host_id': host_id,
            'owned': owned,
            'privilege': privilege
        }, write=True)
        
        logger.info(f"Updated host {host_id}: owned={owned}, privilege={privilege}")
    
    def update_host_discovery(self, host_id: str, discovered: bool):
        """Update host discovery status"""
        query = """
        MATCH (h:Host {id: $host_id})
        SET h.discovered = $discovered
        RETURN h
        """
        
        self.execute_query(query, {
            'host_id': host_id,
            'discovered': discovered
        }, write=True)
    
    def batch_create_network(self, topology: Dict[str, Any]):
        """
        Create entire network topology from CBS observation
        
        Args:
            topology: Network topology dictionary from CBS wrapper
        """
        logger.info("Creating network topology in CKG...")
        
        # Create hosts
        for host_id, host_data in topology.get('nodes', {}).items():
            host = HostEntity(
                host_id=host_id,
                os_type=host_data.get('properties', {}).get('os', 'Unknown'),
                value=host_data.get('value', 0),
                discovered=False,
                owned=False
            )
            self.create_entity(host)
            
            # Create services for this host
            for svc_name, svc_data in host_data.get('services', {}).items():
                service_id = f"{host_id}:{svc_name}"
                service = ServiceEntity(
                    service_id=service_id,
                    service_name=svc_name
                )
                self.create_entity(service)
                
                # Create RUNS relationship
                runs_rel = Relationship(
                    rel_type=RelationType.RUNS,
                    source_id=host_id,
                    target_id=service_id
                )
                self.create_relationship(runs_rel, EntityType.HOST, EntityType.SERVICE)
                
                # Create vulnerabilities
                for vuln_id in svc_data.get('vulnerabilities', []):
                    vuln = VulnerabilityEntity(
                        vuln_id=vuln_id,
                        cve_id=vuln_id
                    )
                    self.create_entity(vuln)
                    
                    # Create EXPOSES relationship
                    exposes_rel = Relationship(
                        rel_type=RelationType.EXPOSES,
                        source_id=service_id,
                        target_id=vuln_id
                    )
                    self.create_relationship(exposes_rel, EntityType.SERVICE, EntityType.VULNERABILITY_TECHNIQUE)
        
        # Create connectivity relationships
        for edge in topology.get('edges', []):
            conn_rel = Relationship(
                rel_type=RelationType.CONNECTED_TO,
                source_id=edge['source'],
                target_id=edge['target']
            )
            self.create_relationship(conn_rel, EntityType.HOST, EntityType.HOST)
        
        logger.info(f"Created {len(topology.get('nodes', {}))} hosts and {len(topology.get('edges', []))} connections")
    
    def get_all_hosts(self) -> List[Dict[str, Any]]:
        """Get all hosts from graph"""
        query = "MATCH (h:Host) RETURN h"
        results = self.execute_query(query)
        return [r['h'] for r in results]
    
    def get_owned_hosts(self) -> List[str]:
        """Get list of owned host IDs"""
        query = "MATCH (h:Host {owned: true}) RETURN h.id as id"
        results = self.execute_query(query)
        return [r['id'] for r in results]
    
    def get_discovered_hosts(self) -> List[str]:
        """Get list of discovered host IDs"""
        query = "MATCH (h:Host {discovered: true}) RETURN h.id as id"
        results = self.execute_query(query)
        return [r['id'] for r in results]
    
    def get_reachable_hosts(self, source_id: str) -> List[str]:
        """Get hosts reachable from source"""
        query = """
        MATCH (source:Host {id: $source_id})-[:CONNECTED_TO]->(target:Host)
        RETURN target.id as id
        """
        results = self.execute_query(query, {'source_id': source_id})
        return [r['id'] for r in results]
    
    def get_host_services(self, host_id: str) -> List[Dict[str, Any]]:
        """Get services running on a host"""
        query = """
        MATCH (h:Host {id: $host_id})-[:RUNS]->(s:Service)
        RETURN s
        """
        results = self.execute_query(query, {'host_id': host_id})
        return [r['s'] for r in results]
    
    def get_service_vulnerabilities(self, service_id: str) -> List[Dict[str, Any]]:
        """Get vulnerabilities exposed by a service"""
        query = """
        MATCH (s:Service {id: $service_id})-[:EXPOSES]->(v:VulnerabilityTechnique)
        RETURN v
        """
        results = self.execute_query(query, {'service_id': service_id})
        return [r['v'] for r in results]
    
    def clear_all(self):
        """Clear all data from graph (use with caution!)"""
        logger.warning("Clearing all graph data...")
        self.execute_query("MATCH (n) DETACH DELETE n", write=True)
        logger.info("All graph data cleared")
    
    def get_graph_stats(self) -> Dict[str, int]:
        """Get statistics about the graph"""
        stats = {}
        
        # Count nodes by type
        for entity_type in EntityType:
            query = f"MATCH (n:{entity_type.value}) RETURN count(n) as count"
            result = self.execute_query(query)
            stats[entity_type.value] = result[0]['count'] if result else 0
        
        # Count relationships
        query = "MATCH ()-[r]->() RETURN count(r) as count"
        result = self.execute_query(query)
        stats['total_relationships'] = result[0]['count'] if result else 0
        
        return stats
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


if __name__ == "__main__":
    # Test CKG Manager
    logger.info("Testing CKGManager...")
    
    # Create manager
    ckg = CKGManager()
    
    if ckg.connect():
        # Initialize schema
        ckg.initialize_schema(clear_existing=True)
        
        # Create some test entities
        host1 = HostEntity("web-01", os_type="Ubuntu20", value=50)
        host2 = HostEntity("db-01", os_type="Ubuntu20", value=100)
        
        ckg.create_entity(host1)
        ckg.create_entity(host2)
        
        # Create connection
        conn_rel = Relationship(
            rel_type=RelationType.CONNECTED_TO,
            source_id="web-01",
            target_id="db-01"
        )
        ckg.create_relationship(conn_rel, EntityType.HOST, EntityType.HOST)
        
        # Query
        print("\n=== All Hosts ===")
        hosts = ckg.get_all_hosts()
        for host in hosts:
            print(host)
        
        print("\n=== Graph Stats ===")
        stats = ckg.get_graph_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        ckg.close()
        logger.info("Test completed!")
    else:
        logger.error("Could not connect to Neo4j. Make sure Neo4j is running.")
        logger.info("Start Neo4j: docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.12")
