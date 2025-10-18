"""
UDS3 Polyglot Persistence Manager
==================================

Orchestrator für multi-backend Persistence mit SAGA Pattern für
distributed transactions über PostgreSQL, Neo4j, ChromaDB.

Autor: UDS3 Development Team
Datum: 18. Oktober 2025
"""

import logging
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class BackendConfig:
    """Konfiguration für einzelnes Backend"""
    enabled: bool = True
    connection_string: str = ""
    timeout: int = 30
    retry_count: int = 3
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UDS3Config:
    """Gesamtkonfiguration für UDS3 Polyglot Manager"""
    
    # PostgreSQL (Relational DB)
    postgresql: BackendConfig = field(default_factory=lambda: BackendConfig(
        enabled=True,
        connection_string="postgresql://localhost:5432/uds3",
        options={"pool_size": 10}
    ))
    
    # Neo4j (Graph DB)
    neo4j: BackendConfig = field(default_factory=lambda: BackendConfig(
        enabled=True,
        connection_string="bolt://localhost:7687",
        options={"max_connection_lifetime": 3600}
    ))
    
    # ChromaDB (Vector DB)
    chromadb: BackendConfig = field(default_factory=lambda: BackendConfig(
        enabled=True,
        connection_string="http://localhost:8000",
        options={"collection_name": "vpb_processes"}
    ))
    
    # Embedding Model (v1.0.1: Changed to available multilingual model)
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # SAGA Settings
    enable_saga: bool = True
    saga_timeout: int = 60
    
    # Performance
    enable_caching: bool = False
    batch_size: int = 100


# ============================================================================
# SAGA Pattern - Transaction State
# ============================================================================

class TransactionState(Enum):
    """SAGA Transaction States"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMMITTED = "committed"
    COMPENSATING = "compensating"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class SagaStep:
    """Einzelner Schritt in SAGA Transaction"""
    backend_name: str
    operation: str  # 'save', 'update', 'delete'
    execute: Callable  # Forward function
    compensate: Callable  # Rollback function
    executed: bool = False
    compensated: bool = False
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class SagaTransaction:
    """SAGA Transaction Coordinator"""
    transaction_id: str
    operation: str
    domain: str
    process_id: str
    state: TransactionState = TransactionState.PENDING
    steps: List[SagaStep] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def add_step(self, step: SagaStep):
        """Füge SAGA Step hinzu"""
        self.steps.append(step)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary"""
        return {
            "transaction_id": self.transaction_id,
            "operation": self.operation,
            "domain": self.domain,
            "process_id": self.process_id,
            "state": self.state.value,
            "steps": [
                {
                    "backend": s.backend_name,
                    "operation": s.operation,
                    "executed": s.executed,
                    "compensated": s.compensated,
                    "error": s.error
                }
                for s in self.steps
            ],
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }


# ============================================================================
# Real Backend Adapters - Production Implementation
# ============================================================================

try:
    import psycopg2
    from psycopg2 import pool, extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 not available - PostgreSQL adapter will be disabled")


class PostgreSQLAdapter:
    """PostgreSQL Adapter für Relational Data mit Connection Pooling"""
    
    def __init__(self, config: BackendConfig):
        self.config = config
        self.connection_pool = None
        self.connected = False
        
        if not PSYCOPG2_AVAILABLE:
            logger.error("PostgreSQL Adapter: psycopg2 not installed")
            return
            
        logger.info("PostgreSQL Adapter initialized (production mode)")
    
    def connect(self):
        """Verbinde mit PostgreSQL und erstelle Connection Pool"""
        if not self.config.enabled or not PSYCOPG2_AVAILABLE:
            return False
            
        try:
            pool_size = self.config.options.get('pool_size', 10)
            
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                1, pool_size,
                self.config.connection_string
            )
            
            # Test connection
            conn = self.connection_pool.getconn()
            conn.cursor().execute("SELECT 1")
            self.connection_pool.putconn(conn)
            
            self.connected = True
            logger.info(f"PostgreSQL connected to {self.config.connection_string}")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Schließe alle Connections im Pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            self.connected = False
            logger.info("PostgreSQL disconnected")
    
    def _get_connection(self):
        """Hole Connection aus Pool"""
        if not self.connected:
            self.connect()
        if self.connection_pool:
            return self.connection_pool.getconn()
        return None
    
    def _release_connection(self, conn):
        """Gib Connection zurück an Pool"""
        if self.connection_pool and conn:
            self.connection_pool.putconn(conn)
    
    def save_process(self, process_data: Dict[str, Any]) -> str:
        """Speichere Process in PostgreSQL"""
        process_id = process_data.get('process_id', str(uuid.uuid4()))
        conn = None
        
        try:
            conn = self._get_connection()
            if not conn:
                raise Exception("No database connection available")
            
            cursor = conn.cursor()
            
            # CREATE TABLE IF NOT EXISTS (idempotent)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uds3_processes (
                    process_id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(512),
                    description TEXT,
                    process_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    deleted_at TIMESTAMP NULL
                )
            """)
            
            # INSERT Process
            cursor.execute("""
                INSERT INTO uds3_processes 
                (process_id, name, description, process_data)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (process_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    process_data = EXCLUDED.process_data,
                    updated_at = NOW()
            """, (
                process_id,
                process_data.get('name', 'Unnamed Process'),
                process_data.get('description', ''),
                json.dumps(process_data)
            ))
            
            conn.commit()
            logger.info(f"PostgreSQL: Saved process {process_id}")
            return process_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"PostgreSQL save failed: {e}")
            raise
        finally:
            if conn:
                self._release_connection(conn)
    
    def get_process(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Lade Process aus PostgreSQL"""
        conn = None
        try:
            conn = self._get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
            cursor.execute("""
                SELECT process_id, name, description, process_data, 
                       created_at, updated_at
                FROM uds3_processes 
                WHERE process_id = %s AND deleted_at IS NULL
            """, (process_id,))
            
            row = cursor.fetchone()
            if row:
                logger.info(f"PostgreSQL: Loaded process {process_id}")
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"PostgreSQL get failed: {e}")
            return None
        finally:
            if conn:
                self._release_connection(conn)
    
    def update_process(self, process_id: str, updates: Dict[str, Any]) -> bool:
        """Update Process in PostgreSQL"""
        conn = None
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE uds3_processes 
                SET name = %s,
                    description = %s,
                    process_data = %s,
                    updated_at = NOW()
                WHERE process_id = %s AND deleted_at IS NULL
            """, (
                updates.get('name'),
                updates.get('description'),
                json.dumps(updates),
                process_id
            ))
            
            conn.commit()
            logger.info(f"PostgreSQL: Updated process {process_id}")
            return cursor.rowcount > 0
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"PostgreSQL update failed: {e}")
            return False
        finally:
            if conn:
                self._release_connection(conn)
    
    def delete_process(self, process_id: str, soft_delete: bool = True) -> bool:
        """Lösche Process aus PostgreSQL"""
        conn = None
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            if soft_delete:
                cursor.execute("""
                    UPDATE uds3_processes 
                    SET deleted_at = NOW()
                    WHERE process_id = %s AND deleted_at IS NULL
                """, (process_id,))
            else:
                cursor.execute("""
                    DELETE FROM uds3_processes 
                    WHERE process_id = %s
                """, (process_id,))
            
            conn.commit()
            logger.info(f"PostgreSQL: Deleted process {process_id} (soft={soft_delete})")
            return cursor.rowcount > 0
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"PostgreSQL delete failed: {e}")
            return False
        finally:
            if conn:
                self._release_connection(conn)


try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j driver not available - Neo4j adapter will be disabled")


class Neo4jAdapter:
    """Neo4j Adapter für Graph Data mit Session Management"""
    
    def __init__(self, config: BackendConfig):
        self.config = config
        self.driver: Optional[Driver] = None
        self.connected = False
        
        if not NEO4J_AVAILABLE:
            logger.error("Neo4j Adapter: neo4j driver not installed")
            return
            
        logger.info("Neo4j Adapter initialized (production mode)")
    
    def connect(self):
        """Verbinde mit Neo4j Database"""
        if not self.config.enabled or not NEO4J_AVAILABLE:
            return False
            
        try:
            # Parse connection string: bolt://user:pass@localhost:7687
            conn_str = self.config.connection_string
            auth = None
            
            # Extract credentials if present
            if '@' in conn_str:
                prefix, host = conn_str.split('@')
                if ':' in prefix:
                    parts = prefix.split('://')
                    if len(parts) == 2:
                        protocol, creds = parts
                        user, password = creds.split(':')
                        auth = (user, password)
                        conn_str = f"{protocol}://{host}"
            
            max_lifetime = self.config.options.get('max_connection_lifetime', 3600)
            
            self.driver = GraphDatabase.driver(
                conn_str,
                auth=auth,
                max_connection_lifetime=max_lifetime
            )
            
            # Test connection
            self.driver.verify_connectivity()
            
            self.connected = True
            logger.info(f"Neo4j connected to {conn_str}")
            return True
            
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Schließe Neo4j Driver"""
        if self.driver:
            self.driver.close()
            self.connected = False
            logger.info("Neo4j disconnected")
    
    def save_process_graph(self, process_data: Dict[str, Any]) -> bool:
        """Erstelle Process Graph in Neo4j"""
        if not self.connected:
            self.connect()
        
        if not self.driver:
            return False
        
        process_id = process_data.get('process_id')
        
        try:
            with self.driver.session() as session:
                # Create Process Node
                session.run("""
                    MERGE (p:Process {process_id: $process_id})
                    SET p.name = $name,
                        p.description = $description,
                        p.updated_at = datetime()
                """, {
                    'process_id': process_id,
                    'name': process_data.get('name', 'Unnamed Process'),
                    'description': process_data.get('description', '')
                })
                
                # Create Element Nodes and Relationships
                elements = process_data.get('elements', [])
                for element in elements:
                    element_id = element.get('id')
                    element_type = element.get('type', 'Unknown')
                    
                    session.run("""
                        MATCH (p:Process {process_id: $process_id})
                        MERGE (e:Element {element_id: $element_id})
                        SET e.type = $type,
                            e.name = $name,
                            e.properties = $properties
                        MERGE (p)-[:HAS_ELEMENT]->(e)
                    """, {
                        'process_id': process_id,
                        'element_id': element_id,
                        'type': element_type,
                        'name': element.get('name', ''),
                        'properties': json.dumps(element)
                    })
                
                # Create Relationships between Elements
                connections = process_data.get('connections', [])
                for conn in connections:
                    session.run("""
                        MATCH (from:Element {element_id: $from_id})
                        MATCH (to:Element {element_id: $to_id})
                        MERGE (from)-[r:CONNECTED_TO]->(to)
                        SET r.type = $conn_type
                    """, {
                        'from_id': conn.get('from'),
                        'to_id': conn.get('to'),
                        'conn_type': conn.get('type', 'default')
                    })
            
            logger.info(f"Neo4j: Created process graph for {process_id}")
            return True
            
        except Exception as e:
            logger.error(f"Neo4j save failed: {e}")
            return False
    
    def get_process_graph(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Lade Process Graph aus Neo4j"""
        if not self.connected or not self.driver:
            return None
        
        try:
            with self.driver.session() as session:
                # Get Process and all connected Elements
                result = session.run("""
                    MATCH (p:Process {process_id: $process_id})
                    OPTIONAL MATCH (p)-[:HAS_ELEMENT]->(e:Element)
                    OPTIONAL MATCH (e)-[r:CONNECTED_TO]->(to:Element)
                    RETURN p, collect(DISTINCT e) as elements, 
                           collect({from: e.element_id, to: to.element_id, type: type(r)}) as connections
                """, {'process_id': process_id})
                
                record = result.single()
                if record:
                    return {
                        'process': dict(record['p']),
                        'elements': [dict(e) for e in record['elements']],
                        'connections': record['connections']
                    }
                return None
                
        except Exception as e:
            logger.error(f"Neo4j get failed: {e}")
            return None
    
    def delete_process_graph(self, process_id: str) -> bool:
        """Lösche Process Graph aus Neo4j"""
        if not self.connected or not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (p:Process {process_id: $process_id})
                    OPTIONAL MATCH (p)-[:HAS_ELEMENT]->(e:Element)
                    DETACH DELETE p, e
                """, {'process_id': process_id})
            
            logger.info(f"Neo4j: Deleted process graph {process_id}")
            return True
            
        except Exception as e:
            logger.error(f"Neo4j delete failed: {e}")
            return False


try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("chromadb not available - ChromaDB adapter will be disabled")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available - Embeddings will be disabled")


class ChromaDBAdapter:
    """ChromaDB Adapter für Vector Embeddings mit BERT"""
    
    def __init__(self, config: BackendConfig):
        self.config = config
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.connected = False
        
        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB Adapter: chromadb not installed")
            return
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("ChromaDB Adapter: sentence-transformers not installed")
            return
            
        logger.info("ChromaDB Adapter initialized (production mode)")
    
    def connect(self):
        """Verbinde mit ChromaDB und lade Embedding Model"""
        if not self.config.enabled or not CHROMADB_AVAILABLE:
            return False
            
        try:
            # Initialize ChromaDB Client
            conn_str = self.config.connection_string
            
            if conn_str.startswith('http'):
                # HTTP Client for remote ChromaDB
                host = conn_str.replace('http://', '').replace('https://', '').split(':')[0]
                port = int(conn_str.split(':')[-1]) if ':' in conn_str.split('//')[-1] else 8000
                
                self.client = chromadb.HttpClient(
                    host=host,
                    port=port,
                    settings=Settings(anonymized_telemetry=False)
                )
            else:
                # Persistent Client for local ChromaDB
                self.client = chromadb.PersistentClient(
                    path=conn_str,
                    settings=Settings(anonymized_telemetry=False)
                )
            
            # Get or Create Collection
            collection_name = self.config.options.get('collection_name', 'vpb_processes')
            
            try:
                self.collection = self.client.get_collection(name=collection_name)
            except:
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "VPB Process Embeddings"}
                )
            
            # Load Embedding Model
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                model_name = self.config.options.get(
                    'embedding_model',
                    'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
                )
                self.embedding_model = SentenceTransformer(model_name)
                logger.info(f"Loaded embedding model: {model_name}")
            
            self.connected = True
            logger.info(f"ChromaDB connected to {conn_str}")
            return True
            
        except Exception as e:
            logger.error(f"ChromaDB connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Schließe ChromaDB Client"""
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.connected = False
        logger.info("ChromaDB disconnected")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generiere Embedding für Text"""
        if not self.embedding_model:
            raise Exception("Embedding model not loaded")
        
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def add(self, process_id: str, embedding_text: str, metadata: Dict) -> bool:
        """
        Füge Embedding hinzu (Standard ChromaDB API)
        
        FIXED v1.0.1: Renamed from add_embedding() to add() to match ChromaDB API
        """
        if not self.connected:
            self.connect()
        
        if not self.collection:
            return False
        
        try:
            # Generate embedding
            embedding = self._generate_embedding(embedding_text)
            
            # Add to collection
            self.collection.add(
                ids=[process_id],
                embeddings=[embedding],
                documents=[embedding_text],
                metadatas=[metadata]
            )
            
            logger.info(f"ChromaDB: Added embedding for {process_id}")
            return True
            
        except Exception as e:
            logger.error(f"ChromaDB add failed: {e}")
            return False
    
    def query(self, query_text: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Suche ähnliche Prozesse via Embedding"""
        if not self.connected or not self.collection:
            return []
        
        try:
            query_embedding = self._generate_embedding(query_text)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            formatted = []
            for i, doc_id in enumerate(results['ids'][0]):
                formatted.append({
                    'id': doc_id,
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })
            
            logger.info(f"ChromaDB: Query returned {len(formatted)} results")
            return formatted
            
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return []
    
    def update(self, process_id: str, embedding_text: str, metadata: Dict) -> bool:
        """Update Embedding"""
        if not self.connected or not self.collection:
            return False
        
        try:
            embedding = self._generate_embedding(embedding_text)
            
            self.collection.update(
                ids=[process_id],
                embeddings=[embedding],
                documents=[embedding_text],
                metadatas=[metadata]
            )
            
            logger.info(f"ChromaDB: Updated embedding for {process_id}")
            return True
            
        except Exception as e:
            logger.error(f"ChromaDB update failed: {e}")
            return False
    
    def delete_embedding(self, process_id: str) -> bool:
        """Lösche Embedding"""
        if not self.connected or not self.collection:
            return False
        
        try:
            self.collection.delete(ids=[process_id])
            logger.info(f"ChromaDB: Deleted embedding for {process_id}")
            return True
            
        except Exception as e:
            logger.error(f"ChromaDB delete failed: {e}")
            return False


# ============================================================================
# UDS3 Polyglot Manager - Main Orchestrator
# ============================================================================

class UDS3PolyglotManager:
    """
    UDS3 Polyglot Persistence Manager mit SAGA Pattern
    
    Koordiniert CRUD-Operationen über mehrere Backends:
    - PostgreSQL: Strukturierte Daten
    - Neo4j: Process Graphs
    - ChromaDB: Vector Embeddings
    
    SAGA Pattern sorgt für Konsistenz bei Fehlern.
    """
    
    def __init__(self, config: Optional[UDS3Config] = None):
        """
        Initialisiere UDS3 Polyglot Manager
        
        Args:
            config: UDS3 Configuration (optional, verwendet Defaults)
        """
        self.config = config or UDS3Config()
        
        # Backend Adapters
        self.postgresql = PostgreSQLAdapter(self.config.postgresql)
        self.neo4j = Neo4jAdapter(self.config.neo4j)
        self.chromadb = ChromaDBAdapter(self.config.chromadb)
        
        # SAGA Transaction Log
        self.transactions: Dict[str, SagaTransaction] = {}
        
        # Verbinde Backends
        self._connect_all()
        
        logger.info("UDS3 Polyglot Manager initialized")
    
    def _connect_all(self):
        """Verbinde alle Backends"""
        self.postgresql.connect()
        self.neo4j.connect()
        self.chromadb.connect()
    
    # ========================================================================
    # CRUD Operations mit SAGA Pattern
    # ========================================================================
    
    def save_process(
        self,
        process_data: Dict[str, Any],
        domain: str = "vpb",
        generate_embeddings: bool = True
    ) -> str:
        """
        Speichere Process in allen Backends (mit SAGA)
        
        Args:
            process_data: Process-Daten (muss process_id, name, description enthalten)
            domain: App-Domain (z.B. 'vpb', 'vpb_migration')
            generate_embeddings: Generiere Embeddings für Semantic Search
        
        Returns:
            process_id: UUID des gespeicherten Prozesses
        
        Raises:
            Exception: Wenn SAGA rollback fehlschlägt
        """
        # Ensure process_id
        process_id = process_data.get('process_id') or str(uuid.uuid4())
        process_data['process_id'] = process_id
        
        if not self.config.enable_saga:
            # Direct execution ohne SAGA
            return self._save_process_direct(process_data, domain, generate_embeddings)
        
        # SAGA Transaction initiieren
        transaction = SagaTransaction(
            transaction_id=str(uuid.uuid4()),
            operation="save_process",
            domain=domain,
            process_id=process_id
        )
        
        try:
            transaction.state = TransactionState.IN_PROGRESS
            self.transactions[transaction.transaction_id] = transaction
            
            # Step 1: PostgreSQL
            step_pg = SagaStep(
                backend_name="postgresql",
                operation="save",
                execute=lambda: self.postgresql.save_process(process_data),
                compensate=lambda: self.postgresql.delete_process(process_id, soft_delete=False)
            )
            transaction.add_step(step_pg)
            
            logger.info(f"SAGA [{transaction.transaction_id}] Step 1: PostgreSQL")
            step_pg.result = step_pg.execute()
            step_pg.executed = True
            
            # Step 2: Neo4j Graph
            step_neo4j = SagaStep(
                backend_name="neo4j",
                operation="save",
                execute=lambda: self.neo4j.save_process_graph(process_data),
                compensate=lambda: self.neo4j.delete_process_graph(process_id)
            )
            transaction.add_step(step_neo4j)
            
            logger.info(f"SAGA [{transaction.transaction_id}] Step 2: Neo4j")
            step_neo4j.result = step_neo4j.execute()
            step_neo4j.executed = True
            
            # Step 3: ChromaDB Embeddings (optional)
            if generate_embeddings:
                embedding_text = self._build_embedding_text(process_data)
                metadata = self._build_embedding_metadata(process_data, domain)
                
                step_chroma = SagaStep(
                    backend_name="chromadb",
                    operation="save",
                    execute=lambda: self.chromadb.add(process_id, embedding_text, metadata),
                    compensate=lambda: self.chromadb.delete_embedding(process_id)
                )
                transaction.add_step(step_chroma)
                
                logger.info(f"SAGA [{transaction.transaction_id}] Step 3: ChromaDB")
                step_chroma.result = step_chroma.execute()
                step_chroma.executed = True
            
            # Alle Steps erfolgreich
            transaction.state = TransactionState.COMMITTED
            transaction.completed_at = datetime.now()
            
            logger.info(f"✅ SAGA [{transaction.transaction_id}] COMMITTED: Process {process_id} saved")
            
            return process_id
        
        except Exception as e:
            # SAGA Compensation (Rollback)
            logger.error(f"❌ SAGA [{transaction.transaction_id}] ERROR: {e}")
            transaction.state = TransactionState.COMPENSATING
            transaction.error = str(e)
            
            success = self._compensate_transaction(transaction)
            
            if success:
                transaction.state = TransactionState.ROLLED_BACK
                transaction.completed_at = datetime.now()
                logger.info(f"♻️  SAGA [{transaction.transaction_id}] ROLLED_BACK successfully")
            else:
                transaction.state = TransactionState.FAILED
                transaction.completed_at = datetime.now()
                logger.error(f"💥 SAGA [{transaction.transaction_id}] FAILED: Rollback incomplete!")
            
            raise Exception(f"SAGA Transaction failed: {e}")
    
    def get_process(
        self,
        process_id: str,
        source: str = "postgresql"
    ) -> Optional[Dict[str, Any]]:
        """
        Lade Process aus Backend
        
        Args:
            process_id: Process ID
            source: Backend source ('postgresql', 'neo4j', 'all')
        
        Returns:
            Process data or None
        """
        if source == "postgresql":
            return self.postgresql.get_process(process_id)
        elif source == "all":
            # Combine data from all backends
            pg_data = self.postgresql.get_process(process_id)
            # TODO: Merge with Neo4j graph data, ChromaDB metadata
            return pg_data
        else:
            return None
    
    def update_process(
        self,
        process_id: str,
        updates: Dict[str, Any],
        domain: str = "vpb"
    ) -> bool:
        """
        Update Process in allen Backends (mit SAGA)
        
        Args:
            process_id: Process ID
            updates: Update-Dictionary
            domain: App-Domain
        
        Returns:
            True if successful
        """
        if not self.config.enable_saga:
            # Direct update
            self.postgresql.update_process(process_id, updates)
            return True
        
        # SAGA Transaction
        transaction = SagaTransaction(
            transaction_id=str(uuid.uuid4()),
            operation="update_process",
            domain=domain,
            process_id=process_id
        )
        
        try:
            transaction.state = TransactionState.IN_PROGRESS
            self.transactions[transaction.transaction_id] = transaction
            
            # Get current state for rollback
            current_state = self.postgresql.get_process(process_id)
            
            # Step 1: PostgreSQL Update
            step_pg = SagaStep(
                backend_name="postgresql",
                operation="update",
                execute=lambda: self.postgresql.update_process(process_id, updates),
                compensate=lambda: self.postgresql.update_process(process_id, current_state) if current_state else False
            )
            transaction.add_step(step_pg)
            
            logger.info(f"SAGA [{transaction.transaction_id}] UPDATE Step 1: PostgreSQL")
            step_pg.result = step_pg.execute()
            step_pg.executed = True
            
            # TODO: Update Neo4j graph if needed
            # TODO: Update ChromaDB embeddings if text changed
            
            transaction.state = TransactionState.COMMITTED
            transaction.completed_at = datetime.now()
            
            logger.info(f"✅ SAGA [{transaction.transaction_id}] UPDATE COMMITTED")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ SAGA [{transaction.transaction_id}] UPDATE ERROR: {e}")
            transaction.state = TransactionState.COMPENSATING
            transaction.error = str(e)
            
            self._compensate_transaction(transaction)
            
            transaction.state = TransactionState.ROLLED_BACK
            transaction.completed_at = datetime.now()
            
            return False
    
    def delete_process(
        self,
        process_id: str,
        domain: str = "vpb",
        soft_delete: bool = True
    ) -> bool:
        """
        Lösche Process aus allen Backends (mit SAGA)
        
        Args:
            process_id: Process ID
            domain: App-Domain
            soft_delete: Soft delete (set deleted_at) vs. hard delete
        
        Returns:
            True if successful
        """
        if not self.config.enable_saga:
            # Direct delete
            self.postgresql.delete_process(process_id, soft_delete)
            self.neo4j.delete_process_graph(process_id)
            self.chromadb.delete_embedding(process_id)
            return True
        
        # SAGA Transaction
        transaction = SagaTransaction(
            transaction_id=str(uuid.uuid4()),
            operation="delete_process",
            domain=domain,
            process_id=process_id
        )
        
        try:
            transaction.state = TransactionState.IN_PROGRESS
            self.transactions[transaction.transaction_id] = transaction
            
            # Backup current state for compensation
            backup_data = self.postgresql.get_process(process_id)
            
            # Step 1: PostgreSQL Delete
            step_pg = SagaStep(
                backend_name="postgresql",
                operation="delete",
                execute=lambda: self.postgresql.delete_process(process_id, soft_delete),
                compensate=lambda: self.postgresql.save_process(backup_data) if backup_data else False
            )
            transaction.add_step(step_pg)
            
            logger.info(f"SAGA [{transaction.transaction_id}] DELETE Step 1: PostgreSQL")
            step_pg.result = step_pg.execute()
            step_pg.executed = True
            
            # Step 2: Neo4j Delete
            step_neo4j = SagaStep(
                backend_name="neo4j",
                operation="delete",
                execute=lambda: self.neo4j.delete_process_graph(process_id),
                compensate=lambda: self.neo4j.save_process_graph(backup_data) if backup_data else False
            )
            transaction.add_step(step_neo4j)
            
            logger.info(f"SAGA [{transaction.transaction_id}] DELETE Step 2: Neo4j")
            step_neo4j.result = step_neo4j.execute()
            step_neo4j.executed = True
            
            # Step 3: ChromaDB Delete
            step_chroma = SagaStep(
                backend_name="chromadb",
                operation="delete",
                execute=lambda: self.chromadb.delete_embedding(process_id),
                compensate=lambda: False  # Cannot restore embeddings without re-generating
            )
            transaction.add_step(step_chroma)
            
            logger.info(f"SAGA [{transaction.transaction_id}] DELETE Step 3: ChromaDB")
            step_chroma.result = step_chroma.execute()
            step_chroma.executed = True
            
            transaction.state = TransactionState.COMMITTED
            transaction.completed_at = datetime.now()
            
            logger.info(f"✅ SAGA [{transaction.transaction_id}] DELETE COMMITTED")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ SAGA [{transaction.transaction_id}] DELETE ERROR: {e}")
            transaction.state = TransactionState.COMPENSATING
            transaction.error = str(e)
            
            self._compensate_transaction(transaction)
            
            transaction.state = TransactionState.ROLLED_BACK
            transaction.completed_at = datetime.now()
            
            return False
    
    # ========================================================================
    # SAGA Compensation (Rollback)
    # ========================================================================
    
    def _compensate_transaction(self, transaction: SagaTransaction) -> bool:
        """
        SAGA Compensation: Rollback aller ausgeführten Steps
        
        Args:
            transaction: SAGA Transaction
        
        Returns:
            True if all compensations successful
        """
        logger.warning(f"♻️  SAGA [{transaction.transaction_id}] Starting compensation...")
        
        all_success = True
        
        # Reverse order compensation
        for step in reversed(transaction.steps):
            if step.executed and not step.compensated:
                try:
                    logger.info(f"   ♻️  Compensating {step.backend_name}...")
                    step.compensate()
                    step.compensated = True
                except Exception as e:
                    logger.error(f"   ❌ Compensation failed for {step.backend_name}: {e}")
                    step.error = f"Compensation failed: {e}"
                    all_success = False
        
        return all_success
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _save_process_direct(
        self,
        process_data: Dict[str, Any],
        domain: str,
        generate_embeddings: bool
    ) -> str:
        """Direct save ohne SAGA (für Performance)"""
        process_id = process_data.get('process_id') or str(uuid.uuid4())
        process_data['process_id'] = process_id
        
        # PostgreSQL
        self.postgresql.save_process(process_data)
        
        # Neo4j
        self.neo4j.save_process_graph(process_data)
        
        # ChromaDB
        if generate_embeddings:
            embedding_text = self._build_embedding_text(process_data)
            metadata = self._build_embedding_metadata(process_data, domain)
            self.chromadb.add(process_id, embedding_text, metadata)
        
        return process_id
    
    def _build_embedding_text(self, process_data: Dict[str, Any]) -> str:
        """Build text for embedding generation"""
        parts = [
            process_data.get('name', ''),
            process_data.get('description', ''),
            process_data.get('authority', ''),
        ]
        
        # Add legal basis if present
        legal_basis = process_data.get('legal_basis', [])
        if isinstance(legal_basis, list):
            parts.extend(legal_basis)
        
        return " ".join([str(p) for p in parts if p])
    
    def _build_embedding_metadata(self, process_data: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Build metadata for embedding"""
        return {
            "process_id": process_data.get('process_id'),
            "name": process_data.get('name'),
            "domain": domain,
            "authority": process_data.get('authority'),
            "created_at": datetime.now().isoformat()
        }
    
    def get_transaction_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Hole SAGA Transaction Status
        
        Args:
            transaction_id: Transaction ID
        
        Returns:
            Transaction status dictionary
        """
        transaction = self.transactions.get(transaction_id)
        if transaction:
            return transaction.to_dict()
        return None
    
    def list_transactions(
        self,
        state: Optional[TransactionState] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Liste alle SAGA Transactions
        
        Args:
            state: Filter by state
            limit: Max anzahl results
        
        Returns:
            List of transaction dictionaries
        """
        transactions = list(self.transactions.values())
        
        if state:
            transactions = [t for t in transactions if t.state == state]
        
        transactions.sort(key=lambda t: t.started_at, reverse=True)
        
        return [t.to_dict() for t in transactions[:limit]]


# ============================================================================
# Factory Function
# ============================================================================

def create_uds3_manager(config: Optional[UDS3Config] = None) -> UDS3PolyglotManager:
    """
    Factory function für UDS3 Polyglot Manager
    
    Args:
        config: Optional configuration
    
    Returns:
        Configured UDS3PolyglotManager instance
    """
    return UDS3PolyglotManager(config)


# ============================================================================
# CLI Interface (für Testing)
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("UDS3 Polyglot Manager - CLI Test")
    print("=" * 80)
    
    # Initialize Manager
    manager = create_uds3_manager()
    
    # Test Process Data
    test_process = {
        "name": "Test Baugenehmigung",
        "description": "Test process for UDS3",
        "authority": "Bauamt Test",
        "legal_basis": ["BauGB §29"],
        "status": "draft"
    }
    
    # Test Save mit SAGA
    print("\n1. Testing SAVE with SAGA...")
    try:
        process_id = manager.save_process(test_process, domain="vpb_test")
        print(f"   ✅ Process saved: {process_id}")
        
        # Get transaction status
        transactions = manager.list_transactions(limit=1)
        if transactions:
            print(f"   📊 Transaction: {transactions[0]['state']}")
            print(f"   📊 Steps: {len(transactions[0]['steps'])}")
    
    except Exception as e:
        print(f"   ❌ Save failed: {e}")
    
    # Test Update
    print("\n2. Testing UPDATE with SAGA...")
    try:
        success = manager.update_process(
            process_id=process_id,
            updates={"status": "active"},
            domain="vpb_test"
        )
        print(f"   ✅ Update: {success}")
    
    except Exception as e:
        print(f"   ❌ Update failed: {e}")
    
    # Test Delete
    print("\n3. Testing DELETE with SAGA...")
    try:
        success = manager.delete_process(
            process_id=process_id,
            domain="vpb_test",
            soft_delete=True
        )
        print(f"   ✅ Delete: {success}")
    
    except Exception as e:
        print(f"   ❌ Delete failed: {e}")
    
    # Transaction Summary
    print("\n4. SAGA Transaction Summary:")
    all_transactions = manager.list_transactions()
    for tx in all_transactions:
        print(f"   {tx['transaction_id'][:8]}... | {tx['operation']:15} | {tx['state']:15} | Steps: {len(tx['steps'])}")
    
    print("\n" + "=" * 80)
    print("Test complete!")
    print("=" * 80)
