# VPB Process Designer - Entwickler-Dokumentation

**Version:** 1.0.0 "UDS3 Complete"  
**Last Updated:** 2025-10-18

---

## 📋 Inhaltsverzeichnis

1. [Entwicklungsumgebung einrichten](#entwicklungsumgebung-einrichten)
2. [Projektstruktur](#projektstruktur)
3. [UDS3 API Development](#uds3-api-development)
4. [Tests ausführen](#tests-ausführen)
5. [Code-Qualität](#code-qualität)
6. [Debugging](#debugging)
7. [Build und Deployment](#build-und-deployment)
8. [Contributing](#contributing)

---

## 🛠️ Entwicklungsumgebung einrichten

### Voraussetzungen

- **Python 3.10+** (Python 3.13 empfohlen)
- **Git** (2.x)
- **Visual Studio Code** (empfohlen) oder PyCharm
- **PostgreSQL** (optional, für UDS3 Backend)
- **Neo4j Desktop** (optional, für UDS3 Backend)
- **Ghostscript** (optional, für PDF/PNG Export)

### Lokales Setup

**1. Repository klonen:**
```powershell
git clone https://github.com/makr-code/VCC-VPB.git
cd VCC-VPB
```

**2. Virtuelle Umgebung erstellen:**
```powershell
# Python venv erstellen
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (CMD)
.\venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

**3. Abhängigkeiten installieren:**
```powershell
# Core Dependencies
pip install -r requirements.txt

# Development Dependencies (optional)
pip install pytest pytest-cov flake8 black mypy

# Verify Installation
python -c "import fastapi, pydantic, uvicorn; print('FastAPI Ready')"
```

**4. Umgebungsvariablen konfigurieren (optional):**
```powershell
# PostgreSQL (für Production)
$env:UDS3_POSTGRES_HOST = "localhost"
$env:UDS3_POSTGRES_PORT = "5432"
$env:UDS3_POSTGRES_USER = "vpb_user"
$env:UDS3_POSTGRES_PASSWORD = "your_password"
$env:UDS3_POSTGRES_DB = "vpb_processes"

# Neo4j (für Production)
$env:UDS3_NEO4J_URI = "bolt://localhost:7687"
$env:UDS3_NEO4J_USER = "neo4j"
$env:UDS3_NEO4J_PASSWORD = "your_password"

# ChromaDB (für Production)
$env:UDS3_CHROMADB_PATH = "./data/chromadb"
$env:UDS3_CHROMADB_COLLECTION = "vpb_processes"

# Mock Mode (Standard für Development)
$env:UDS3_USE_MOCK = "true"
```

**5. Applikation starten:**
```powershell
# Option 1: VPB Designer GUI
python vpb_app.py

# Option 2: UDS3 API Server (Development)
uvicorn api.uds3_vpb_fastapi:app --reload

# Option 3: Mit Prozess-Datei
python vpb_app.py processes\showcase_sps_elements_complete.vpb.json
```

---

## 📁 Projektstruktur

```
VPB/
├── api/                       # UDS3 FastAPI Backend (NEW v1.0.0)
│   ├── __init__.py
│   └── uds3_vpb_fastapi.py   # 696 lines - REST API (11 endpoints)
│
├── core/                      # Core Logic (NEW v1.0.0)
│   ├── __init__.py
│   ├── message_bus.py
│   └── polyglot_manager.py   # 1041 lines - SAGA Pattern + Backend Adapters
│
├── controller/                # MVC Controller
│   ├── __init__.py
│   └── app_controller.py
│
├── migration/                 # Migration Tools (NEW v1.0.0)
│   ├── __init__.py
│   ├── migration_tool.py     # SQLite → UDS3 Migration
│   ├── validation.py         # Real-time UDS3 Validation
│   └── auto_fix.py           # 587 lines - 5 Fix Strategies
│
├── vpb/                       # VPB Designer Core
│   ├── models/
│   │   ├── element.py        # Element definitions (COUNTER, CONDITION, etc.)
│   │   ├── process.py        # Process model
│   │   └── connection.py     # Connection model
│   │
│   ├── ui/
│   │   ├── canvas.py         # Main canvas rendering
│   │   ├── properties_panel.py  # Element properties UI
│   │   └── migration_dialog.py  # 575 lines - Migration GUI (NEW v1.0.0)
│   │
│   ├── views/
│   │   ├── menu_bar.py       # Menu structure (enhanced v1.0.0)
│   │   └── toolbar.py        # Toolbar actions
│   │
│   └── services/
│       ├── validation_service.py  # Process validation
│       ├── export_service.py      # PDF/PNG/SVG export
│       └── palette_service.py     # Element palette management
│
├── tests/                     # Test Suite
│   ├── test_*_element.py     # SPS Element tests (40 tests)
│   ├── test_*_validation.py  # Validation tests
│   ├── test_uds3_fastapi.py  # 658 lines - API tests (20 tests, NEW v1.0.0)
│   ├── test_auto_fix.py      # 390 lines - Auto-fix tests (8 tests, NEW v1.0.0)
│   ├── test_migration_performance.py  # 750 lines - Performance tests (NEW v1.0.0)
│   └── test_migration_quick.py        # 120 lines - Quick baseline (NEW v1.0.0)
│
├── docs/                      # Dokumentation
│   ├── ELEMENTS_*.md         # SPS Element Documentation (10,000+ lines)
│   ├── VPB_v0.3.0_RELEASE_NOTES.md
│   ├── PHASE_2_COMPLETION_SUMMARY.md    # 548 lines (NEW v1.0.0)
│   ├── PERFORMANCE_BENCHMARK_REPORT.md  # 277 lines (NEW v1.0.0)
│   ├── VPB_API_DOCUMENTATION.md
│   ├── VPB_ROADMAP.md
│   └── ...
│
├── processes/                 # Example Process Files
│   ├── showcase_sps_elements_complete.vpb.json  # Full SPS showcase
│   └── ...
│
├── palettes/                  # Element Palette Definitions
│   ├── default_palette.json
│   └── README.md
│
├── data/                      # Data Storage
│   ├── vpb.db                # SQLite Database (legacy)
│   └── chromadb/             # ChromaDB Vector Store (UDS3)
│
├── logs/                      # Application Logs
├── temp/                      # Temporary Files
│
├── vpb_app.py                # Main Application Entry Point
├── vpb_config.py             # Configuration Management
├── vpb_schema.py             # VPB-JSON Schema
├── vpb_sqlite_db.py          # SQLite Database Management
│
├── requirements.txt          # Python Dependencies
├── pytest.ini                # Pytest Configuration
├── README.md                 # Project Overview
├── CHANGELOG.md              # Complete Change History
├── ROADMAP.md                # Project Roadmap
├── DEVELOPMENT.md            # This File
└── LICENSE                   # MIT License
```

---

## 🌐 UDS3 API Development

### API Server starten

**Development Mode (mit Auto-Reload):**
```powershell
uvicorn api.uds3_vpb_fastapi:app --reload --host 127.0.0.1 --port 8000
```

**Production Mode:**
```powershell
# Mit Gunicorn (Production WSGI Server)
pip install gunicorn

gunicorn api.uds3_vpb_fastapi:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

**Docker:**
```powershell
# Build Docker Image
docker build -t vpb-api:1.0.0 .

# Run Container
docker run -d -p 8000:8000 \
  -e UDS3_USE_MOCK=true \
  --name vpb-api \
  vpb-api:1.0.0
```

---

### API Endpoints Übersicht

**OpenAPI Dokumentation:**
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

**Process CRUD:**
```
POST   /api/uds3/vpb/processes        Create process (SAGA)
GET    /api/uds3/vpb/processes        List processes (filters)
GET    /api/uds3/vpb/processes/{id}   Get process
PUT    /api/uds3/vpb/processes/{id}   Update process (SAGA)
DELETE /api/uds3/vpb/processes/{id}   Delete process (SAGA)
```

**Search & Health:**
```
GET    /api/uds3/vpb/search            Semantic search (ChromaDB)
GET    /api/uds3/vpb/health            Backend health check
```

**SAGA Transactions:**
```
GET    /api/uds3/saga/transactions     List transactions
GET    /api/uds3/saga/transactions/{id}  Transaction status
```

---

### API Testing mit curl

**Health Check:**
```powershell
curl http://localhost:8000/api/uds3/vpb/health
```

**Create Process:**
```powershell
curl -X POST http://localhost:8000/api/uds3/vpb/processes `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Test Process",
    "description": "API Test",
    "domain": "test",
    "elements": [],
    "connections": []
  }'
```

**List Processes:**
```powershell
curl "http://localhost:8000/api/uds3/vpb/processes?limit=10"
```

**Get Process:**
```powershell
curl http://localhost:8000/api/uds3/vpb/processes/{process_id}
```

**Update Process:**
```powershell
curl -X PUT http://localhost:8000/api/uds3/vpb/processes/{process_id} `
  -H "Content-Type: application/json" `
  -d '{"description": "Updated via API"}'
```

**Delete Process (Soft):**
```powershell
curl -X DELETE http://localhost:8000/api/uds3/vpb/processes/{process_id}
```

**Delete Process (Hard):**
```powershell
curl -X DELETE "http://localhost:8000/api/uds3/vpb/processes/{process_id}?hard_delete=true"
```

**Semantic Search:**
```powershell
curl "http://localhost:8000/api/uds3/vpb/search?query=genehmigung&limit=5"
```

**List SAGA Transactions:**
```powershell
curl "http://localhost:8000/api/uds3/saga/transactions?state=COMMITTED"
```

---

### SAGA Pattern Development

**SAGA Transaction Flow:**

```python
# 1. Define SAGA Steps
from core.polyglot_manager import SagaStep, create_uds3_manager

async def create_process_saga(process_data: Dict):
    manager = create_uds3_manager(use_mock=True)
    
    # Step 1: PostgreSQL (Relational Data)
    step1 = SagaStep(
        name="save_to_postgres",
        backend="postgres",
        execute=lambda: manager.postgres.save_process(process_data),
        compensate=lambda id: manager.postgres.delete_process(id)
    )
    
    # Step 2: Neo4j (Graph Relationships)
    step2 = SagaStep(
        name="save_to_neo4j",
        backend="neo4j",
        execute=lambda: manager.neo4j.save_process_graph(process_data),
        compensate=lambda id: manager.neo4j.delete_process_graph(id)
    )
    
    # Step 3: ChromaDB (Vector Embeddings)
    step3 = SagaStep(
        name="save_to_chromadb",
        backend="chromadb",
        execute=lambda: manager.chromadb.add_process_embedding(process_data, embedding),
        compensate=lambda id: manager.chromadb.delete_embedding(id)
    )
    
    # 2. Execute SAGA
    transaction_id = str(uuid.uuid4())
    success = await manager._execute_saga_transaction([step1, step2, step3], transaction_id)
    
    # 3. Check Transaction State
    transaction = manager.transactions[transaction_id]
    print(f"State: {transaction.state}")  # COMMITTED or ROLLED_BACK
    
    return transaction_id, success

# Run SAGA
import asyncio
transaction_id, success = asyncio.run(create_process_saga({...}))
```

**Rollback on Failure:**
```python
# If Step 3 fails:
# 1. Compensate Step 2 (delete from Neo4j)
# 2. Compensate Step 1 (delete from PostgreSQL)
# Result: TransactionState.ROLLED_BACK

# Check Rollback
transaction = manager.transactions[transaction_id]
if transaction.state == TransactionState.ROLLED_BACK:
    print(f"Rollback reason: {transaction.error}")
    for step in transaction.steps:
        if not step.success:
            print(f"Failed step: {step.name} - {step.error}")
```

---

### Pydantic Models

**Request Models:**
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ProcessCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    domain: str = Field(default="default", max_length=100)
    elements: List[Dict] = Field(default_factory=list)
    connections: List[Dict] = Field(default_factory=list)

class ProcessUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    elements: Optional[List[Dict]] = None
    connections: Optional[List[Dict]] = None
```

**Response Models:**
```python
class ProcessResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    domain: str
    elements: List[Dict]
    connections: List[Dict]
    created_at: str
    updated_at: Optional[str]
    transaction_id: Optional[str]  # SAGA transaction ID

class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    backends: Dict[str, str]  # {"postgres": "connected", "neo4j": "disconnected", ...}
    timestamp: str
```

---
```bash
# Image bauen
docker build -t vcc-vpb .

# Container starten
docker run -p 8000:8000 vcc-vpb
```

## 🤝 Beitragen

### Workflow

1. **Branch erstellen:**
   ```bash
   git checkout -b feature/neue-funktion
   ```

2. **Änderungen committen:**
   ```bash
   git add .
   git commit -m "feat: Neue Funktion hinzugefügt"
   ```

3. **Push und Pull Request:**
   ```bash
   git push origin feature/neue-funktion
   # Dann Pull Request auf GitHub erstellen
   ```

### Commit-Konventionen

- `feat:` - Neue Features
- `fix:` - Bug-Fixes
- `docs:` - Dokumentations-Änderungen
- `refactor:` - Code-Refactoring
- `test:` - Test-Änderungen
- `chore:` - Wartungsaufgaben

---

*Letzte Aktualisierung: 16.10.2025*
