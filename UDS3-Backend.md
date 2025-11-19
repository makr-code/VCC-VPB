# UDS3 Backend Integration

**Version:** 0.5.0  
**Target:** Developers & Architects  
**Status:** Implemented

---

## Overview / Übersicht

**Deutsch:**  
VPB nutzt UDS3 (Unified Data Services 3) Polyglot Persistence für verteilte Datenhaltung über drei spezialisierte Datenbanksysteme mit SAGA Pattern für Transaktionskonsistenz.

**English:**  
VPB uses UDS3 (Unified Data Services 3) Polyglot Persistence for distributed data storage across three specialized database systems with SAGA pattern for transaction consistency.

---

## Architecture / Architektur

### Polyglot Persistence Strategy

VPB verteilt Daten über drei Backend-Systeme, jedes optimiert für spezifische Anwendungsfälle:

```
┌──────────────────────────────────────────────────────┐
│              VPB Application Layer                    │
│         (vpb_app.py / FastAPI Server)                │
└────────────────┬─────────────────────────────────────┘
                 │
         ┌───────┴────────┐
         │ Polyglot Mgr   │  (SAGA Coordinator)
         │ core/          │
         └───────┬────────┘
                 │
    ┌────────────┼────────────┐
    ↓            ↓            ↓
┌──────────┐ ┌─────────┐ ┌──────────┐
│PostgreSQL│ │ Neo4j   │ │ChromaDB  │
│Relational│ │ Graph   │ │ Vector   │
└──────────┘ └─────────┘ └──────────┘
```

---

## Backend Systems / Backend-Systeme

### 1. PostgreSQL (Relational Master)

**Purpose / Zweck:**  
Primäre Datenhaltung für strukturierte Prozessdaten

**Stores / Speichert:**
- Process metadata (name, description, status)
- Element properties
- Connection data
- User data
- Audit logs

**Tables / Tabellen:**
```sql
-- Main tables
processes (id, key, name, description, authority, legal_basis, status, created_at, updated_at)
process_elements (id, process_id, element_type, properties, position)
process_connections (id, process_id, source_id, target_id, connection_type)

-- Reference tables
roles (id, key, name, level, permissions)
org_units (id, key, name, parent_id, type)
systems (id, key, name, type, criticality)
controls (id, key, name, type, objective, evidence)
legal_refs (id, citation, type, uri)
info_objects (id, key, name, classification, pii, retention)
```

**Connection String:**
```
postgresql://localhost:5432/uds3
```

**Features:**
- ACID transactions
- Structured queries
- Foreign key constraints
- Full-text search (later)

---

### 2. Neo4j (Graph Database)

**Purpose / Zweck:**  
Prozess-Graphen und Beziehungsanalyse

**Stores / Speichert:**
- Process flow graphs
- Element relationships
- Organizational hierarchy
- Role assignments
- System dependencies

**Node Types / Knotentypen:**
```cypher
(:PROCESS {id, key, name, version, status})
(:STEP {id, key, title, description, order})
(:ROLE {id, key, name, level})
(:ORG_UNIT {id, key, name, type})
(:SYSTEM {id, key, name, type, criticality})
(:CONTROL {id, key, name, type})
(:LEGAL_REF {id, citation, type, uri})
(:INFO {id, key, name, classification, pii})
```

**Relationship Types / Beziehungstypen:**
```cypher
(:PROCESS)-[:HAS_STEP]->(:STEP)
(:STEP)-[:NEXT]->(:STEP)
(:STEP)-[:PERFORMED_BY]->(:ROLE)
(:ROLE)-[:BELONGS_TO]->(:ORG_UNIT)
(:STEP)-[:USES_SYSTEM]->(:SYSTEM)
(:CONTROL)-[:CONTROLS]->(:STEP|:PROCESS)
(:STEP|:PROCESS)-[:CITES]->(:LEGAL_REF)
(:STEP)-[:PRODUCES|CONSUMES]->(:INFO)
(:STEP)-[:ESCALATES_TO]->(:ROLE|:ORG_UNIT)
```

**Temporal Model (UDS3 Canon):**
```cypher
-- Date nodes for temporal tracking
(:Year {y})
(:Month {y, m})
(:Day {y, m, d})
(:Date {iso, year, month, day})

-- Temporal relationships
(:STEP)-[:OCCURS_ON]->(:Date)
(:STEP)-[:SCHEDULED_FOR]->(:Date)
(:CONTROL)-[:EFFECTIVE_FROM]->(:Date)
(:CONTROL)-[:EFFECTIVE_UNTIL]->(:Date)

-- Constraints
CREATE CONSTRAINT date_iso_unique FOR (d:Date) REQUIRE d.iso IS UNIQUE;
CREATE INDEX month_y_m FOR (m:Month) ON (m.y, m.m);
CREATE INDEX day_y_m_d FOR (d:Day) ON (d.y, d.m, d.d);
```

**Connection String:**
```
bolt://localhost:7687
```

**Use Cases:**
- Process path finding
- Impact analysis (what depends on this?)
- Organizational structure queries
- Compliance chain verification

---

### 3. ChromaDB (Vector Database)

**Purpose / Zweck:**  
Semantische Suche und KI-Features

**Stores / Speichert:**
- Text embeddings of process descriptions
- Step descriptions (vector representations)
- Document embeddings
- Similarity search indexes

**Collections:**
```python
vpb_processes:
  - document_id: process UUID
  - embeddings: 384-dim vectors
  - metadata: {
      process_key: str,
      step_key: str,
      version: str,
      role_keys: List[str],
      text: str (original)
    }
```

**Embedding Model:**
```
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```
- Multilingual support (DE/EN)
- 384 dimensions
- Optimized for semantic similarity

**Connection String:**
```
http://localhost:8000
```

**Use Cases:**
- Semantic process search
- "Find similar processes"
- AI-powered suggestions
- Natural language queries

---

## SAGA Pattern for Distributed Transactions

### Overview

**Problem:**  
Wie stellen wir Konsistenz über drei Datenbanken sicher?

**Solution:**  
SAGA Pattern mit Compensation Logic

### Transaction States

```python
class TransactionState(Enum):
    PENDING = "pending"           # Initial state
    IN_PROGRESS = "in_progress"   # Executing steps
    COMMITTED = "committed"       # All steps successful
    COMPENSATING = "compensating" # Rolling back
    ROLLED_BACK = "rolled_back"   # Rollback complete
    FAILED = "failed"             # Unrecoverable error
```

### SAGA Flow

**Successful Transaction:**
```
1. BEGIN SAGA
2. PostgreSQL: Save process → ✅
3. Neo4j: Create graph → ✅
4. ChromaDB: Store embeddings → ✅
5. COMMIT SAGA → ✅ All committed
```

**Failed Transaction with Rollback:**
```
1. BEGIN SAGA
2. PostgreSQL: Save process → ✅
3. Neo4j: Create graph → ✅
4. ChromaDB: Store embeddings → ❌ FAILS
5. COMPENSATE:
   - ChromaDB: (already failed, skip)
   - Neo4j: DELETE graph → ✅
   - PostgreSQL: DELETE process → ✅
6. ROLLBACK SAGA → All changes reverted
```

### Implementation

**File:** `core/polyglot_manager.py`

**Key Classes:**
```python
class UDS3PolyglotManager:
    """Main orchestrator for polyglot operations"""
    
    def begin_transaction(self, operation: str) -> str:
        """Start SAGA transaction, returns transaction_id"""
        
    def save_process(self, process_data: dict, transaction_id: str):
        """Save to all backends in SAGA"""
        
    def commit_transaction(self, transaction_id: str):
        """Commit all steps"""
        
    def rollback_transaction(self, transaction_id: str):
        """Compensate all executed steps"""
```

**SAGA Step Structure:**
```python
@dataclass
class SagaStep:
    backend_name: str       # "postgresql" | "neo4j" | "chromadb"
    operation: str          # "save" | "update" | "delete"
    execute: Callable       # Forward function
    compensate: Callable    # Rollback function
    executed: bool = False
    compensated: bool = False
    result: Optional[Any] = None
    error: Optional[str] = None
```

---

## Configuration / Konfiguration

### UDS3Config

**File:** `core/polyglot_manager.py`

```python
@dataclass
class UDS3Config:
    # PostgreSQL
    postgresql: BackendConfig = BackendConfig(
        enabled=True,
        connection_string="postgresql://localhost:5432/uds3",
        options={"pool_size": 10}
    )
    
    # Neo4j
    neo4j: BackendConfig = BackendConfig(
        enabled=True,
        connection_string="bolt://localhost:7687",
        options={"max_connection_lifetime": 3600}
    )
    
    # ChromaDB
    chromadb: BackendConfig = BackendConfig(
        enabled=True,
        connection_string="http://localhost:8000",
        options={"collection_name": "vpb_processes"}
    )
    
    # Embedding Model
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # SAGA Settings
    enable_saga: bool = True
    saga_timeout: int = 60
    
    # Performance
    enable_caching: bool = False
    batch_size: int = 100
```

### Environment Variables

```bash
# PostgreSQL
export UDS3_POSTGRES_HOST=localhost
export UDS3_POSTGRES_PORT=5432
export UDS3_POSTGRES_DB=uds3
export UDS3_POSTGRES_USER=vpb_user
export UDS3_POSTGRES_PASSWORD=secret

# Neo4j
export UDS3_NEO4J_URI=bolt://localhost:7687
export UDS3_NEO4J_USER=neo4j
export UDS3_NEO4J_PASSWORD=secret

# ChromaDB
export UDS3_CHROMA_HOST=localhost
export UDS3_CHROMA_PORT=8000
```

---

## API Integration

### REST Endpoints

**File:** `api/uds3_vpb_fastapi.py`

**Process CRUD with UDS3:**
```python
@app.post("/api/uds3/vpb/processes")
async def create_process(process: ProcessCreate):
    """Create process in all UDS3 backends (SAGA)"""
    
    manager = get_uds3_manager()
    tx_id = manager.begin_transaction("create_process")
    
    try:
        result = manager.save_process(process.dict(), tx_id)
        manager.commit_transaction(tx_id)
        return {"success": True, "process_id": result["id"]}
    except Exception as e:
        manager.rollback_transaction(tx_id)
        raise HTTPException(status_code=500, detail=str(e))
```

**Search with ChromaDB:**
```python
@app.post("/api/uds3/vpb/search")
async def semantic_search(query: str, top_k: int = 5):
    """Semantic search using ChromaDB embeddings"""
    
    manager = get_uds3_manager()
    results = manager.search_similar(query, top_k)
    return {"results": results}
```

**Graph Query with Neo4j:**
```python
@app.get("/api/uds3/vpb/processes/{process_id}/graph")
async def get_process_graph(process_id: str):
    """Get process graph from Neo4j"""
    
    manager = get_uds3_manager()
    graph = manager.get_process_graph(process_id)
    return {"graph": graph}
```

---

## Data Flow / Datenfluss

### Creating a Process

```
User Action (vpb_app.py)
    ↓
DocumentController
    ↓
DocumentService
    ↓
UDS3PolyglotManager.save_process()
    ↓
SAGA Transaction Begin
    ↓
┌─────────────────┬──────────────────┬─────────────────┐
│   PostgreSQL    │      Neo4j       │    ChromaDB     │
├─────────────────┼──────────────────┼─────────────────┤
│ INSERT process  │ CREATE (:PROCESS)│ Store embedding │
│ INSERT elements │ CREATE (:STEP)   │ + metadata      │
│ INSERT conns    │ CREATE rels      │                 │
└─────────────────┴──────────────────┴─────────────────┘
    ↓ All succeed
SAGA Commit → Process created ✅

    OR

    ↓ One fails
SAGA Rollback → All compensated ❌
```

### Querying Data

**Relational Query (PostgreSQL):**
```sql
SELECT * FROM processes WHERE authority = 'Bauamt XYZ';
```

**Graph Query (Neo4j):**
```cypher
MATCH (p:PROCESS)-[:HAS_STEP]->(s:STEP)-[:PERFORMED_BY]->(r:ROLE)
WHERE p.id = $process_id
RETURN s, r;
```

**Semantic Search (ChromaDB):**
```python
results = collection.query(
    query_texts=["Baugenehmigungsverfahren"],
    n_results=5,
    where={"version": "1.0"}
)
```

---

## System Integration: Covina

### Overview

**Covina** ist das übergeordnete System für Prozess- und Organisationsmodellierung.

**Integration Point:**  
VPB → UDS3 → Covina

### Unified Process Schema (UPS)

**Mapping VPB → UPS:**

```
VPB Process Element → UPS Entities:
- Process → Process(id, key, title, version, domain)
- Step → Step(id, process_id, order, key, title)
- SPS Elements → Controls, States, Conditions
- Connections → NEXT relationships
- Roles → Role(id, key, name, level)
```

### Covina Integration Features

**1. Process Import to Covina:**
```
VPB Export (JSON/XML) → Covina Ingestion API
POST /ingestion/processes
```

**2. Gap Detection:**
- Missing roles
- Missing controls
- Dead-end steps
- Cyclic processes
- Temporal inconsistencies

**3. Organizational Mapping:**
- Org units
- Role hierarchy
- System landscape
- Control framework

**See:** `strategieVBP-Covina.md` for detailed strategy

---

## System Integration: VERITAS

### Overview

**VERITAS** ist das Compliance und Governance System.

### Integration Points

**Protected Modules:**
```python
# vpb_compliance_engine.py
module_licenced_organization = "VERITAS_TECH_GMBH"

# vpb_api_server.py
# VERITAS Protected Module
```

**Features:**
- Compliance checking
- Audit logging
- License management
- Protected operations

---

## Performance Considerations

### Optimization Strategies

**1. Batch Operations:**
```python
# Instead of individual saves
for element in elements:
    manager.save_element(element)  # ❌ Slow

# Use batch
manager.save_elements_batch(elements)  # ✅ Fast
```

**2. Caching (Future):**
```python
config.enable_caching = True
# Cache frequently accessed processes
```

**3. Async Operations:**
```python
# Non-critical writes can be async
await manager.save_process_async(process_data)
```

**4. Connection Pooling:**
- PostgreSQL: Pool size 10
- Neo4j: Connection lifetime 3600s
- ChromaDB: HTTP keepalive

---

## Monitoring & Observability

### Transaction Tracking

**SAGA Transactions API:**
```
GET /api/uds3/saga/transactions
GET /api/uds3/saga/transactions/{transaction_id}
```

**Response:**
```json
{
  "transaction_id": "uuid",
  "state": "COMMITTED",
  "operation": "create_process",
  "started_at": "2025-11-19T12:00:00",
  "completed_at": "2025-11-19T12:00:02",
  "steps": [
    {"backend": "postgresql", "status": "executed"},
    {"backend": "neo4j", "status": "executed"},
    {"backend": "chromadb", "status": "executed"}
  ]
}
```

### Health Check

```
GET /api/uds3/vpb/health
```

**Response:**
```json
{
  "status": "healthy",
  "backends": {
    "postgresql": {"status": "connected", "latency_ms": 5},
    "neo4j": {"status": "connected", "latency_ms": 8},
    "chromadb": {"status": "connected", "latency_ms": 12}
  }
}
```

---

## Deployment

### Development Mode

**Mock Backends (No DB required):**
```python
config = UDS3Config()
config.postgresql.enabled = False  # Use mock
config.neo4j.enabled = False       # Use mock
config.chromadb.enabled = False    # Use mock

manager = UDS3PolyglotManager(config, mode="mock")
```

### Production Mode

**Requirements:**
- PostgreSQL 14+
- Neo4j 5.0+
- ChromaDB 0.4+

**Docker Compose:**
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: uds3
      POSTGRES_USER: vpb_user
      POSTGRES_PASSWORD: secret
    ports:
      - "5432:5432"
  
  neo4j:
    image: neo4j:5.0
    environment:
      NEO4J_AUTH: neo4j/secret
    ports:
      - "7687:7687"
      - "7474:7474"
  
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
```

**Start:**
```bash
docker-compose up -d
python vpb_app.py  # Or start API server
```

---

## Related Documentation

- **[[Architecture]]** - Overall system architecture
- **[[API-Reference]]** - REST API endpoints
- **[[Development-Guide]]** - Setup development environment
- **[[System-Integration]]** - Covina, Veritas, Themis, Clara

---

[[Home]] | [[Architecture]] | [[API-Reference]]
