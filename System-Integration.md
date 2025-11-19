# System Integration / Systemintegration

**Version:** 0.5.0  
**Target:** Architects & System Integrators  
**Status:** Active Integration

---

## Overview / Übersicht

VPB ist Teil eines größeren Ökosystems von Systemen für Verwaltungsprozesse, Compliance und Governance.

VPB is part of a larger ecosystem of systems for administrative processes, compliance, and governance.

---

## System Landscape / Systemlandschaft

```
┌──────────────────────────────────────────────────────────┐
│                    VPB Ecosystem                          │
└──────────────────────────────────────────────────────────┘
                           │
      ┌────────────────────┼────────────────────┐
      ↓                    ↓                    ↓
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│   Covina    │    │   VERITAS    │    │  UDS3 Core   │
│  (Process   │    │ (Compliance  │    │  (Polyglot   │
│  Platform)  │    │  & Govern.)  │    │  Persistence)│
└─────────────┘    └──────────────┘    └──────────────┘
      ↓                    ↓                    ↓
┌─────────────────────────────────────────────────────┐
│        Themis          │         Clara               │
│    (Legal Refs)        │    (AI Assistant)           │
└─────────────────────────────────────────────────────┘
```

---

## 1. Covina Integration

### About Covina

**Covina** = **Co**mpliance + Organi**v**ation + **In**telligence + **A**nalysis

**Purpose:**  
Zentrales System für Prozess- und Organisationsmodellierung mit Gap-Detection und Process Mining.

**Status:** Active Integration (v0.5.0)

### Architecture

```
VPB (Process Designer)
    ↓ Export
VPB JSON/XML
    ↓ Ingestion API
Covina UDS3 Backend
    ↓ Transformation
UPS (Unified Process Schema)
    ↓ Storage
PostgreSQL + Neo4j + ChromaDB
    ↓ Analysis
Gap Detection + Process Mining
```

### Integration Points

#### 1. Process Export to Covina

**VPB → Covina:**
```
VPB Process (JSON) → Covina Ingestion API
POST /ingestion/processes
```

**Mapping:**
```python
# VPB Format
{
  "name": "Baugenehmigung",
  "elements": [
    {"type": "COUNTER", "id": "elem1", ...},
    {"type": "CONDITION", "id": "elem2", ...}
  ],
  "connections": [...]
}

# Covina UPS Format
{
  "process": {
    "key": "baugenehmigung_v1",
    "title": "Baugenehmigung"
  },
  "steps": [
    {"key": "step1", "order": 1, ...},
    {"key": "step2", "order": 2, ...}
  ],
  "flows": [
    {"from": "step1", "to": "step2", "type": "sequence"}
  ]
}
```

#### 2. Unified Process Schema (UPS)

**Core Entities / Kern-Entitäten:**

```
Process(id, key, title, version, domain, owner_org, status, created_at)
Step(id, process_id, order, key, title, description, required, duration_est)
Role(id, key, name, level, permissions[])
Unit(id, key, name, parent_id, type)
System(id, key, name, type, criticality)
Control(id, key, name, type, objective, evidence)
LegalRef(id, citation, type, uri)
InfoObject(id, key, name, classification, pii, retention)
```

**Relationships / Beziehungen:**

```cypher
# Neo4j Graph Model
(Process)-[:HAS_STEP]->(Step)
(Step)-[:NEXT {type}]->(Step)
(Step)-[:PERFORMED_BY]->(Role)
(Role)-[:BELONGS_TO]->(Unit)
(Step)-[:USES_SYSTEM]->(System)
(Control)-[:CONTROLS]->(Step|Process)
(Step|Process)-[:CITES]->(LegalRef)
(Step)-[:PRODUCES|CONSUMES]->(InfoObject)
(Step)-[:ESCALATES_TO]->(Role|Unit)
```

#### 3. Gap Detection

**Covina Gap Detection Rules:**

**Missing Elements:**
- Step ohne PERFORMED_BY (no role assigned)
- Step ohne NEXT (dead-end, no terminal marker)
- Required Control fehlt (no control attached)
- LegalRef im Text aber nicht verknüpft

**Structural Issues:**
- Zyklus ohne Loop-Marker
- Unreachable steps
- Multiple entry points

**Data Quality:**
- InfoObject mit PII aber ohne Control
- Step ohne Beschreibung
- Missing required properties

**Temporal Consistency:**
- EFFECTIVE_FROM > EFFECTIVE_UNTIL
- Step scheduled in past
- Conflicting dates

**API Call:**
```
POST /gaps/processes/run
{
  "process_ids": ["uuid1", "uuid2"],
  "rules": ["all"]  # or specific rules
}
```

**Response:**
```json
{
  "gaps": [
    {
      "type": "MISSING_ROLE",
      "severity": "high",
      "step_id": "step1",
      "message": "Step has no PERFORMED_BY relationship"
    },
    {
      "type": "DEAD_END",
      "severity": "medium",
      "step_id": "step5",
      "message": "Step has no NEXT and is not terminal"
    }
  ],
  "summary": {
    "total_gaps": 2,
    "high": 1,
    "medium": 1,
    "low": 0
  }
}
```

#### 4. Process Mining (Phase 2)

**Planned Features:**
- Frequent pattern detection
- Bottleneck analysis
- Conformance checking (Soll vs. Ist)
- SLA monitoring
- RACI matrix generation

### Configuration

**File:** `strategieVBP-Covina.md`

**Environment:**
```bash
export COVINA_API_URL=https://covina.example.com/api/v1
export COVINA_API_KEY=your-api-key
```

**Usage in VPB:**
```python
# Export to Covina
from vpb.export import CovinaExporter

exporter = CovinaExporter(api_url, api_key)
result = exporter.export_process(vpb_process)

if result.success:
    print(f"Exported to Covina: {result.process_id}")
    gaps = exporter.run_gap_detection(result.process_id)
    print(f"Detected gaps: {gaps}")
```

---

## 2. VERITAS Integration

### About VERITAS

**VERITAS** = **Ver**ification + **I**ntegrity + **T**racking + **A**udit + **S**ecurity

**Purpose:**  
Compliance Engine und Governance Framework

**Status:** Protected Modules (v0.5.0)

### Features

**1. Module Protection:**
```python
# vpb_compliance_engine.py
# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_licenced_organization = "VERITAS_TECH_GMBH"
```

**2. Compliance Checking:**
- License validation
- Module integrity checks
- Access control
- Audit logging

**3. Protected Operations:**
- Data export restrictions
- API access control
- Feature gating

### Integration Points

**VPB Protected Modules:**
- `vpb_compliance_engine.py` - Compliance checking
- `vpb_api_server.py` - API protection
- `vpb_data_preparation.py` - Data protection

**Usage:**
```python
from vpb_compliance_engine import ComplianceEngine

engine = ComplianceEngine()
if engine.validate_license():
    # Allow operation
    pass
else:
    # Deny operation
    raise PermissionError("Invalid license")
```

### Audit Trail

**Logged Events:**
- Process creation/modification
- Export operations
- API calls
- User actions

**Format:**
```json
{
  "timestamp": "2025-11-19T12:00:00Z",
  "user": "user@example.com",
  "action": "PROCESS_EXPORT",
  "resource": "process-uuid",
  "result": "SUCCESS",
  "metadata": {...}
}
```

---

## 3. UDS3 Core Integration

### About UDS3

**UDS3** = **U**nified **D**ata **S**ervices **3**

**Purpose:**  
Polyglot Persistence Layer mit SAGA Pattern

**Status:** Core Component (v0.5.0)

### Components

**Backend Systems:**
- PostgreSQL (relational data)
- Neo4j (graph data)
- ChromaDB (vector data)

**Features:**
- SAGA transactions
- Multi-backend consistency
- Automatic rollback
- Health monitoring

**See:** [[UDS3-Backend]] for complete documentation

---

## 4. Themis Integration

### About Themis

**Themis** = Legal Reference and Citation System

**Purpose:**  
Verwaltung rechtlicher Grundlagen und Verweise

**Status:** Planned Integration (Future)

### Planned Features

**1. Legal Reference Database:**
- Laws and regulations
- Court decisions
- Administrative guidelines
- Cross-references

**2. Citation Management:**
- Automatic citation formatting
- Link verification
- Version tracking
- Change notifications

**3. VPB Integration:**
```python
# Link process to legal basis
process.add_legal_reference(
    citation="BauGB §29-38",
    type="law",
    uri="https://themis.example.com/laws/baugb/29-38"
)
```

**4. Compliance Verification:**
- Check if cited laws are current
- Alert on deprecated references
- Suggest updates

### API (Planned)

```
GET  /themis/legal-refs?q=BauGB
POST /themis/legal-refs
GET  /themis/legal-refs/{id}
GET  /themis/legal-refs/{id}/changes
```

---

## 5. Clara Integration

### About Clara

**Clara** = **C**onversational **L**egal **A**ssistant for **R**egulatory **A**nalysis

**Purpose:**  
KI-gestützter Assistent für Prozessanalyse und -optimierung

**Status:** Early Stage (v0.5.0)

### Current Features (v0.5.0)

**1. AI Chat Integration:**
```python
# vpb/ui/chat_panel.py
# AI-powered chat for process assistance
```

**2. Process Generation:**
- Generate processes from text descriptions
- Natural language understanding
- Element suggestions

**3. Ollama Integration:**
```python
from ollama_client import OllamaClient

client = OllamaClient()
response = client.ask(
    "Create a building permit approval process"
)
```

### Planned Features

**1. Intelligent Analysis:**
- Process optimization suggestions
- Bottleneck detection
- Best practice recommendations

**2. Natural Language Queries:**
```
User: "Which processes involve the building authority?"
Clara: "Found 3 processes: Baugenehmigung, Bauvoranfrage, Abbruchgenehmigung"
```

**3. Automated Documentation:**
- Generate process descriptions
- Create user guides
- Export documentation

**4. Regulatory Compliance:**
- Check against legal requirements
- Suggest necessary controls
- Verify completeness

### Configuration

**Environment:**
```bash
export CLARA_MODEL=llama3
export CLARA_API_URL=http://localhost:11434
export CLARA_TEMPERATURE=0.7
```

**Usage:**
```python
from vpb.services.ai_service import AIService

ai = AIService()
suggestion = ai.suggest_next_element(current_process)
print(f"Clara suggests: {suggestion}")
```

---

## Integration Architecture

### Data Flow

```
User Action (VPB)
    ↓
VPB Application Layer
    ↓
┌──────────┬───────────┬──────────┐
│  Covina  │  VERITAS  │  Clara   │
└──────────┴───────────┴──────────┘
    ↓            ↓          ↓
┌────────────────────────────────┐
│        UDS3 Backend            │
│  (PostgreSQL, Neo4j, ChromaDB) │
└────────────────────────────────┘
    ↓            ↓          ↓
┌──────────┬───────────┬──────────┐
│  Themis  │  Audit    │  Storage │
│ (Legal)  │   Logs    │          │
└──────────┴───────────┴──────────┘
```

### Communication Protocols

**1. REST APIs:**
- Covina: REST JSON
- VERITAS: Internal Python
- Themis: REST JSON (planned)
- Clara: Ollama API

**2. Event Bus:**
```python
# Internal event-driven communication
event_bus.publish("process.exported", {
    "process_id": "uuid",
    "target": "covina",
    "status": "success"
})
```

**3. Message Queue (Future):**
- Async operations
- Background processing
- System decoupling

---

## Configuration Management

### Integration Settings

**File:** `vpb_config.py` (or settings.json)

```python
INTEGRATIONS = {
    "covina": {
        "enabled": True,
        "api_url": "https://covina.example.com/api/v1",
        "api_key": env("COVINA_API_KEY"),
        "auto_export": False
    },
    "veritas": {
        "enabled": True,
        "enforce_compliance": True,
        "audit_level": "full"
    },
    "uds3": {
        "enabled": True,
        "backends": ["postgresql", "neo4j", "chromadb"],
        "saga_enabled": True
    },
    "themis": {
        "enabled": False,  # Future
        "api_url": "https://themis.example.com/api"
    },
    "clara": {
        "enabled": True,
        "model": "llama3",
        "api_url": "http://localhost:11434"
    }
}
```

---

## Security Considerations

### Authentication & Authorization

**1. API Keys:**
```bash
# Required for external integrations
export COVINA_API_KEY=secret-key
export THEMIS_API_KEY=secret-key
```

**2. OAuth (Planned):**
- User authentication
- Service-to-service auth
- Token management

**3. RBAC (Role-Based Access Control):**
- Define roles
- Assign permissions
- Enforce access control

### Data Protection

**1. Encryption:**
- Data in transit (TLS/HTTPS)
- Data at rest (DB encryption)
- API payload encryption

**2. PII Handling:**
- Identify PII fields
- Mask sensitive data
- GDPR compliance

**3. Audit Logging:**
- All integrations logged
- VERITAS audit trail
- Compliance reporting

---

## Deployment Scenarios

### Scenario 1: Standalone VPB

```
VPB Desktop App
    ↓
Local SQLite (no UDS3)
```

**Features:**
- Basic process design
- Local storage
- No external integrations

---

### Scenario 2: VPB + UDS3

```
VPB Desktop App
    ↓
UDS3 Backend (PostgreSQL, Neo4j, ChromaDB)
```

**Features:**
- Full persistence
- SAGA transactions
- Semantic search

---

### Scenario 3: Full Ecosystem

```
VPB Desktop App / API Server
    ↓
UDS3 Backend
    ↓
Covina + VERITAS + Clara + Themis
```

**Features:**
- Complete integration
- Gap detection
- AI assistance
- Compliance checking
- Legal references

---

## Monitoring & Health

### Integration Health Checks

**Endpoint:**
```
GET /api/integrations/health
```

**Response:**
```json
{
  "status": "healthy",
  "integrations": {
    "covina": {"status": "connected", "latency_ms": 45},
    "veritas": {"status": "active"},
    "uds3": {"status": "healthy", "backends": {...}},
    "themis": {"status": "disabled"},
    "clara": {"status": "connected", "model": "llama3"}
  }
}
```

---

## Troubleshooting

### Common Issues

**1. Covina Connection Failed:**
```bash
# Check API URL and key
curl -H "Authorization: Bearer $COVINA_API_KEY" \
     https://covina.example.com/api/v1/health
```

**2. VERITAS License Invalid:**
```
# Check license file
cat /path/to/veritas.license
# Contact VERITAS_TECH_GMBH
```

**3. UDS3 Backend Down:**
```
# Check backend health
GET /api/uds3/vpb/health
```

**4. Clara Not Responding:**
```bash
# Check Ollama server
curl http://localhost:11434/api/tags
```

---

## Related Documentation

- **[[UDS3-Backend]]** - Polyglot persistence details
- **[[Architecture]]** - System architecture
- **[[API-Reference]]** - REST API documentation
- **[[Development-Guide]]** - Setup and configuration

---

## External References

- **Covina Strategy:** `strategieVBP-Covina.md`
- **VERITAS Modules:** `vpb_compliance_engine.py`, `vpb_api_server.py`
- **UDS3 Core:** `core/polyglot_manager.py`
- **Clara AI:** `vpb/services/ai_service.py`, `ollama_client.py`

---

[[Home]] | [[Architecture]] | [[UDS3-Backend]]
