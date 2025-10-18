# UDS3 Polyglot Persistence - Kern-System

**Datum:** 18. Oktober 2025  
**Version:** 1.0  
**Autor:** UDS3 Architecture Team  
**Status:** 🟢 Architecture Decision Record (ADR)

---

## 📋 Executive Summary

Dieses Dokument definiert die **Kern-Komponenten** des UDS3 Polyglot Persistence Systems, die als **wiederverwendbare Basis** für alle UDS3-Anwendungen dienen (VPB, Rechtsdatenbank, Gesetzessammlung, etc.).

**Ziel:** Ein generisches, erweiterbares Polyglot Persistence Framework für die deutsche Verwaltung, optimiert für LLM-Integration und semantische Suche.

**Kern-Prinzipien:**
- ✅ **Domain-agnostisch:** Keine VPB/App-spezifischen Details im Kern
- ✅ **Erweiterbar:** Apps können Kern-Schema erweitern (PostgreSQL JSONB, Neo4j Labels)
- ✅ **Performant:** Optimiert für deutsche Verwaltungssprache und LLM-Queries
- ✅ **Polyglot:** Best DB for the Job - Vector, Graph, Relational, File

---

## 🎯 1. Architektur-Entscheidung: UDS3-Kern vs. App-Extensions

### 1.1 Entscheidungskriterien

| Kriterium | UDS3-Kern ✅ | App-Extension ❌ |
|-----------|--------------|------------------|
| **Wiederverwendbarkeit** | Für ALLE UDS3-Apps nutzbar | Nur für eine App (z.B. VPB) |
| **Domäne** | Verwaltungsprozesse allgemein | App-spezifische Details |
| **Abhängigkeiten** | Keine App-Dependencies | Benötigt spezifisches App-Schema |
| **Komplexität** | Einfache, generische APIs | Kann komplex sein |
| **Wartbarkeit** | Zentral, einmal pflegen | Pro App pflegen |

### 1.2 Verteilung: Was gehört wohin?

| Komponente | UDS3-Kern | VPB-Extension | Begründung |
|------------|-----------|---------------|------------|
| **Polyglot Persistence Manager** | ✅ 100% | - | Orchestriert alle DBs, generisch |
| **Vector DB (ChromaDB/pgvector)** | ✅ 100% | - | Semantic Search für alle Apps |
| **Graph DB (Neo4j)** | ✅ 100% | - | Prozess-Graphen für alle Apps |
| **Relational DB (PostgreSQL)** | ✅ 80% | ✅ 20% | Base Schema + App Extensions |
| **German BERT Embeddings** | ✅ 100% | - | Deutsche Verwaltungssprache |
| **Generic RAG Pipeline** | ✅ 100% | - | Framework, Apps erweitern |
| **Query Orchestrator** | ✅ 100% | - | Kombiniert alle DBs |
| **Base Process Schema** | ✅ 100% | - | `uds3_processes`, `uds3_elements` |
| **VPB Element Types (23 Types)** | - | ✅ 100% | VPB-spezifisch |
| **VPB UI State** | - | ✅ 100% | Canvas-Positionen, Zoom |
| **VPB Compliance Scores** | - | ✅ 100% | BVA/FIM/DSGVO-spezifisch |
| **Legal Document Types** | - | ✅ 100% | Rechtsdatenbank-App |
| **Case Law Schema** | - | ✅ 100% | Rechtsprechungs-App |

### 1.3 Beispiel: PostgreSQL Schema-Trennung

**UDS3 Base Schema (Kern):**
```sql
-- Generisch für alle Verwaltungsprozesse
CREATE TABLE uds3_processes (
    process_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    process_type VARCHAR(100),  -- 'vpb', 'bpmn', 'legal_workflow', etc.
    
    -- Generische Verwaltungs-Attribute
    authority VARCHAR(300),
    legal_basis TEXT[],
    legal_context VARCHAR(100),
    
    -- Lifecycle
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Erweiterbar durch Apps via JSONB
    app_specific_data JSONB DEFAULT '{}'
);
```

**VPB Extension (App-spezifisch):**
```sql
-- VPB erweitert das Base Schema
ALTER TABLE uds3_processes 
ADD COLUMN IF NOT EXISTS vpb_ui_state JSONB;

ALTER TABLE uds3_processes 
ADD COLUMN IF NOT EXISTS vpb_complexity_score NUMERIC(3,2);

-- VPB-spezifische Tabelle
CREATE TABLE vpb_element_properties (
    element_id UUID PRIMARY KEY,
    element_type VARCHAR(50),  -- 23 VPB-spezifische Types
    canvas_position JSONB,     -- {x: 100, y: 200}
    vpb_compliance_tags TEXT[]
);
```

---

## 🏗️ 2. UDS3 Kern-Architektur

### 2.1 Ordnerstruktur (HYBRID - Nach Audit angepasst)

> **⚠️ WICHTIG:** Nach Analyse von 81 existierenden Dateien wurde die ursprüngliche "flache Struktur" verworfen. Stattdessen: **Hybride Struktur** mit Domain-Ordnern.

```
C:\VCC\uds3\
├── README.md
├── setup.py
├── requirements.txt
├── pyproject.toml
├── .gitignore
│
├── core/                        # ⭐ NEUE KERN-MODULE
│   ├── __init__.py
│   ├── embeddings.py            # ✅ IMPLEMENTIERT & GETESTET
│   ├── llm_ollama.py            # ✅ IMPLEMENTIERT & GETESTET
│   ├── rag_pipeline.py          # ✅ IMPLEMENTIERT & GETESTET (wird erweitert)
│   ├── rag_async.py             # 🔄 TO BE ADDED (async support)
│   ├── rag_cache.py             # 🔄 TO BE ADDED (caching layer)
│   └── polyglot_manager.py      # ✅ IMPLEMENTIERT & GETESTET (gekürzt: uds3_polyglot_manager.py → polyglot_manager.py)
│
├── database/                    # ✅ BESTEHENDES SYSTEM (bereits vorhanden)
│   ├── __init__.py
│   ├── database_manager.py      # ✅ Factory Pattern, Governance
│   ├── database_api_base.py     # ✅ Abstract Base Classes
│   ├── database_api_chromadb.py # ✅ ChromaDB Adapter
│   ├── database_api_neo4j.py    # ✅ Neo4j Adapter
│   ├── database_api_postgresql.py # ✅ PostgreSQL Adapter
│   ├── adapter_governance.py    # ✅ Policy Management
│   └── ... (weitere Adapter)
│
├── vpb/                         # VPB-DOMAIN (VPB-spezifisch)
│   ├── __init__.py
│   ├── operations.py            # ✅ VORHANDEN (49KB, VPBProcess, VPBTask, etc.) - gekürzt von uds3_vpb_operations.py
│   ├── adapter.py               # 🔄 TO BE CREATED (Integration mit PolyglotManager)
│   ├── parser_bpmn.py           # ✅ VORHANDEN (BPMN 2.0 Parser) - gekürzt von uds3_bpmn_process_parser.py
│   ├── parser_epk.py            # ✅ VORHANDEN (EPK Parser) - gekürzt von uds3_epk_process_parser.py
│   ├── parser_petrinet.py       # ✅ VORHANDEN (Petri-Netz Parser) - gekürzt von uds3_petrinet_parser.py
│   ├── parser_base.py           # ✅ VORHANDEN (Base Class) - gekürzt von uds3_process_parser_base.py
│   ├── export_engine.py         # ✅ VORHANDEN - gekürzt von uds3_process_export_engine.py
│   └── process_mining.py        # ✅ VORHANDEN - gekürzt von uds3_process_mining.py
│
├── compliance/                  # DSGVO & SECURITY
│   ├── __init__.py
│   ├── dsgvo_core.py            # ✅ VORHANDEN (34KB, neu 14.10.2025) - gekürzt von uds3_dsgvo_core.py
│   ├── security_quality.py      # ✅ VORHANDEN (36KB, Security + Quality) - gekürzt von uds3_security_quality.py
│   ├── identity_service.py      # ✅ VORHANDEN (24KB, Identity Management) - gekürzt von uds3_identity_service.py
│   ├── delete_operations.py     # ✅ VORHANDEN (46KB, Soft/Hard Delete) - gekürzt von uds3_delete_operations.py
│   └── validation_worker.py     # ✅ VORHANDEN (Validation) - gekürzt von uds3_validation_worker.py
│
├── integration/                 # MULTI-DB INTEGRATION
│   ├── __init__.py
│   ├── saga_integration.py      # ✅ VORHANDEN (55KB, SAGA Pattern) - gekürzt von saga_multi_db_integration.py
│   ├── adaptive_strategy.py     # ✅ VORHANDEN (53KB, Adaptive Routing) - gekürzt von adaptive_multi_db_strategy.py
│   ├── distributor.py           # ✅ VORHANDEN (47KB, Load Balancing) - gekürzt von uds3_multi_db_distributor.py
│   ├── pipeline.py              # ✅ VORHANDEN (29KB, ETL Pipelines) - gekürzt von pipeline_integration.py
│   └── query_abstraction.py     # ✅ VORHANDEN (40KB, Query Abstraction) - gekürzt von uds3_polyglot_query.py
│
├── operations/                  # CRUD & OPERATIONS
│   ├── __init__.py
│   ├── advanced_crud.py         # ✅ VORHANDEN (32KB) - gekürzt von uds3_advanced_crud.py
│   ├── archive.py               # ✅ VORHANDEN (47KB) - gekürzt von uds3_archive_operations.py
│   ├── streaming.py             # ✅ VORHANDEN (48KB) - gekürzt von uds3_streaming_operations.py
│   └── record_cache.py          # ✅ VORHANDEN (25KB) - gekürzt von uds3_single_record_cache.py
│
├── query/                       # QUERY & FILTER
│   ├── __init__.py
│   ├── filters.py               # ✅ VORHANDEN (16KB) - gekürzt von uds3_query_filters.py
│   ├── vector_filter.py         # ✅ VORHANDEN (19KB) - gekürzt von uds3_vector_filter.py
│   ├── graph_filter.py          # ✅ VORHANDEN (25KB) - gekürzt von uds3_graph_filter.py
│   ├── relational_filter.py     # ✅ VORHANDEN (30KB) - gekürzt von uds3_relational_filter.py
│   └── file_filter.py           # ✅ VORHANDEN (29KB) - gekürzt von uds3_file_storage_filter.py
│
├── domain/                      # DOMAIN-SPEZIFISCH
│   ├── __init__.py
│   ├── admin_types.py           # ✅ VORHANDEN (29KB, Admin-Typen) - gekürzt von uds3_admin_types.py
│   ├── templates.py             # ✅ VORHANDEN (41KB) - gekürzt von uds3_collection_templates.py
│   ├── geo_extension.py         # ✅ VORHANDEN (37KB) - gekürzt von uds3_geo_extension.py
│   ├── geo_4d.py                # ✅ VORHANDEN (32KB) - gekürzt von uds3_4d_geo_extension.py
│   ├── document_classifier.py   # ✅ VORHANDEN (25KB) - gekürzt von uds3_document_classifier.py
│   ├── document_reconstruction.py # ✅ VORHANDEN (31KB) - gekürzt von uds3_document_reconstruction_engine.py
│   ├── naming_strategy.py       # ✅ VORHANDEN (17KB) - gekürzt von uds3_naming_strategy.py
│   └── naming_integration.py    # ✅ VORHANDEN (25KB) - gekürzt von uds3_naming_integration.py
│
├── saga/                        # SAGA PATTERN
│   ├── __init__.py
│   ├── orchestrator.py          # ✅ VORHANDEN (9KB) - gekürzt von uds3_saga_orchestrator.py
│   ├── compliance.py            # ✅ VORHANDEN (33KB) - gekürzt von uds3_saga_compliance.py
│   ├── step_builders.py         # ✅ VORHANDEN (23KB) - gekürzt von uds3_saga_step_builders.py
│   └── streaming_integration.py # ✅ VORHANDEN (23KB) - gekürzt von uds3_streaming_saga_integration.py
│
├── legacy/                      # ⚠️ ZU DEPRECATEN
│   ├── __init__.py
│   ├── uds3_core.py             # ⚠️ 285KB MONOLITH! (7344 Zeilen)
│   ├── rag_enhanced_llm_integration.py # ⚠️ 46KB (Features werden in rag_pipeline.py gemerged)
│   ├── uds3_dsgvo_core_old.py   # ❌ DEPRECATED
│   ├── uds3_quality_DEPRECATED.py # ❌ DEPRECATED
│   └── uds3_security_DEPRECATED.py # ❌ DEPRECATED
│
├── sql/                         # SQL SCHEMAS
│   ├── 001_base_schema.sql      # PostgreSQL Base Tables
│   ├── 002_embeddings.sql       # Embedding Registry
│   ├── 003_authorities.sql      # Behörden-Katalog
│   └── 004_legal_basis.sql      # Rechtsgrundlagen-Katalog
│
├── cypher/                      # NEO4J SCHEMAS
│   ├── 001_base_schema.cypher   # Base Graph Schema
│   ├── 002_constraints.cypher   # Constraints
│   └── 003_indexes.cypher       # Indexes
│
├── docs/
│   ├── UDS3_POLYGLOT_PERSISTENCE_CORE.md  # ⬅️ Dieses Dokument
│   ├── UDS3_REFACTORING_STRATEGY.md # ⬅️ Refactoring-Plan
│   ├── UDS3_EXISTING_FILES_AUDIT.md # ⬅️ Audit von 81 Dateien
│   ├── API_REFERENCE.md
│   └── DEPLOYMENT_GUIDE.md
│
├── tests/                       # TESTS (zu migrieren)
│   ├── __init__.py
│   ├── test_embeddings.py       # ✅ IMPLEMENTIERT
│   ├── test_llm.py              # ✅ IMPLEMENTIERT
│   ├── test_integration.py      # ✅ IMPLEMENTIERT
│   ├── test_polyglot.py         # 🔄 TO BE CREATED
│   ├── test_vpb_adapter.py      # 🔄 TO BE CREATED
│   └── ... (weitere Tests)
│
├── examples/                    # BEISPIELE
│   ├── 01_basic_usage.py
│   ├── 02_vpb_integration.py
│   └── 03_legal_documents.py
│
├── config.py                    # ✅ VORHANDEN
├── __init__.py                  # ✅ VORHANDEN (5KB)
└── setup.py                     # ✅ VORHANDEN
```

**Architektur-Entscheidungen nach Audit:**

1. **✅ Hybrid-Ansatz:** Neue Module nutzen `database/database_manager.py` (bereits getestet!)
2. **⚠️ uds3_core.py Deprecation:** 285KB Monolith wird schrittweise durch neue Module ersetzt
3. **✅ VPB Operations vorhanden:** Integration statt Neuentwicklung
4. **✅ DSGVO/Security vorhanden:** Muss nur integriert werden
5. **🔄 RAG Merge:** Features von `rag_enhanced_llm_integration.py` in `rag_pipeline.py` integrieren
6. **📝 Dateinamen-Kürzung:** Entfernung redundanter Präfixe für bessere Lesbarkeit

**Vorteile der hybriden Struktur:**
- ✅ **Domain-Separation:** Klare Trennung (core, vpb, compliance, etc.)
- ✅ **Backwards Compatible:** Bestehende `database/` Struktur bleibt
- ✅ **Skalierbar:** Neue Domains einfach hinzufügen
- ✅ **Wartbar:** Kleinere, fokussierte Module
- ✅ **Real-World:** Basiert auf IST-Zustand (81 Dateien)
- ✅ **Lesbarkeit:** Kurze, prägnante Dateinamen ohne redundante Präfixe

---

### 2.2 Namenskonventionen & Refactoring-Mapping

**Prinzip:** Dateinamen-Kürzung durch Entfernung redundanter Präfixe

| Alt (IST) | Neu (SOLL) | Begründung |
|-----------|------------|------------|
| `uds3_polyglot_manager.py` | `polyglot_manager.py` | "uds3" redundant (bereits in Ordner) |
| `uds3_vpb_operations.py` | `operations.py` | "uds3" + "vpb" redundant (in vpb/) |
| `uds3_bpmn_process_parser.py` | `parser_bpmn.py` | Prefix statt Suffix, kürzer |
| `uds3_epk_process_parser.py` | `parser_epk.py` | Einheitliches Parser-Schema |
| `uds3_petrinet_parser.py` | `parser_petrinet.py` | Einheitliches Parser-Schema |
| `uds3_process_parser_base.py` | `parser_base.py` | Basisklasse klar erkennbar |
| `uds3_process_export_engine.py` | `export_engine.py` | "process" redundant im Kontext |
| `uds3_process_mining.py` | `process_mining.py` | Minimal-Änderung, klar |
| `uds3_dsgvo_core.py` | `dsgvo_core.py` | "uds3" redundant (in compliance/) |
| `uds3_security_quality.py` | `security_quality.py` | Selbsterklärend |
| `uds3_identity_service.py` | `identity_service.py` | Standard Service-Name |
| `uds3_delete_operations.py` | `delete_operations.py` | Klar ohne Prefix |
| `uds3_validation_worker.py` | `validation_worker.py` | Worker-Pattern erkennbar |
| `saga_multi_db_integration.py` | `saga_integration.py` | "multi_db" implizit in integration/ |
| `adaptive_multi_db_strategy.py` | `adaptive_strategy.py` | Kontext klar durch Ordner |
| `uds3_multi_db_distributor.py` | `distributor.py` | Funktion klar |
| `pipeline_integration.py` | `pipeline.py` | "integration" redundant |
| `uds3_polyglot_query.py` | `query_abstraction.py` | Funktion präziser benannt |
| `uds3_advanced_crud.py` | `advanced_crud.py` | Klar ohne Prefix |
| `uds3_archive_operations.py` | `archive.py` | Kürzer, klar |
| `uds3_streaming_operations.py` | `streaming.py` | Funktion klar |
| `uds3_single_record_cache.py` | `record_cache.py` | "single" implizit |
| `uds3_query_filters.py` | `filters.py` | Kontext durch query/ Ordner |
| `uds3_vector_filter.py` | `vector_filter.py` | Selbsterklärend |
| `uds3_graph_filter.py` | `graph_filter.py` | DB-Typ klar |
| `uds3_relational_filter.py` | `relational_filter.py` | DB-Typ klar |
| `uds3_file_storage_filter.py` | `file_filter.py` | Kürzer |
| `uds3_admin_types.py` | `admin_types.py` | Standard |
| `uds3_collection_templates.py` | `templates.py` | "collection" implizit |
| `uds3_geo_extension.py` | `geo_extension.py` | Klar |
| `uds3_4d_geo_extension.py` | `geo_4d.py` | Umgedreht, kürzer |
| `uds3_document_classifier.py` | `document_classifier.py` | Standard ML-Name |
| `uds3_document_reconstruction_engine.py` | `document_reconstruction.py` | "engine" implizit |
| `uds3_naming_strategy.py` | `naming_strategy.py` | Pattern erkennbar |
| `uds3_naming_integration.py` | `naming_integration.py` | Klar |
| `uds3_saga_orchestrator.py` | `orchestrator.py` | Kontext durch saga/ |
| `uds3_saga_compliance.py` | `compliance.py` | Kontext durch saga/ |
| `uds3_saga_step_builders.py` | `step_builders.py` | SAGA implizit |
| `uds3_streaming_saga_integration.py` | `streaming_integration.py` | SAGA implizit |

**Import-Beispiele (Alt vs. Neu):**

```python
# ALT (vor Refactoring)
from uds3.uds3_polyglot_manager import UDS3PolyglotManager
from uds3.uds3_vpb_operations import VPBProcess, VPBTask
from uds3.uds3_dsgvo_core import UDS3DSGVOCore
from uds3.uds3_bpmn_process_parser import BPMNParser

# NEU (nach Refactoring)
from uds3.core.polyglot_manager import UDS3PolyglotManager
from uds3.vpb.operations import VPBProcess, VPBTask
from uds3.compliance.dsgvo_core import UDS3DSGVOCore
from uds3.vpb.parser_bpmn import BPMNParser
```

**Vorteile der Namenskürzung:**
- ✅ **Lesbarkeit:** `from uds3.vpb.operations import` statt `from uds3.uds3_vpb_operations import`
- ✅ **Konsistenz:** Einheitliches Schema (z.B. `parser_*.py`)
- ✅ **Wartbarkeit:** Weniger Zeichen, schnelleres Erfassen
- ✅ **IDE-Support:** Bessere Autocomplete (kürzere Pfade)
- ✅ **DRY-Prinzip:** Redundante Prefixe eliminiert

### 2.2 Architektur-Diagramm

```
┌─────────────────────────────────────────────────────────────────┐
│                    UDS3 APPLICATION LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   VPB App    │  │  Legal Docs  │  │   Case Law   │  ...    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
┌─────────┴──────────────────┴──────────────────┴─────────────────┐
│              UDS3 POLYGLOT PERSISTENCE CORE                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         UDS3PolyglotManager (Orchestrator)               │  │
│  │  - Query Routing                                         │  │
│  │  - Multi-DB Coordination                                 │  │
│  │  - Transaction Management                                │  │
│  └────────────┬──────────────┬──────────────┬───────────────┘  │
│               │              │              │                   │
│  ┌────────────▼──┐  ┌────────▼────┐  ┌──────▼──────┐          │
│  │ VectorDB      │  │  GraphDB    │  │ RelationalDB│          │
│  │ Adapter       │  │  Adapter    │  │  Adapter    │          │
│  └────────────┬──┘  └────────┬────┘  └──────┬──────┘          │
└───────────────┼──────────────┼──────────────┼──────────────────┘
                │              │              │
       ┌────────▼────┐  ┌──────▼─────┐  ┌────▼──────┐
       │  ChromaDB/  │  │   Neo4j    │  │PostgreSQL │
       │  pgvector   │  │            │  │           │
       └─────────────┘  └────────────┘  └───────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   UDS3 LLM & RAG PIPELINE                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           UDS3GenericRAG (RAG Framework)                 │  │
│  │  1. Query Classification                                 │  │
│  │  2. Multi-DB Retrieval (Vector→Graph→SQL)               │  │
│  │  3. Context Assembly                                     │  │
│  │  4. Prompt Engineering                                   │  │
│  │  5. LLM Generation                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ▲                                    │
│  ┌─────────────────────────┴────────────────────────────────┐  │
│  │      German BERT Embeddings (deutsche-telekom/gbert)    │  │
│  │  - Verwaltungssprache-optimiert                         │  │
│  │  - 768-dim Vektoren                                     │  │
│  │  - Caching & Batch-Processing                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ 3. Kern-Komponenten im Detail

### 3.1 Polyglot Manager (Orchestrator)

**Datei:** `uds3/persistence/polyglot_manager.py`

```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from uds3.persistence.vector_db.base import VectorDBAdapter
from uds3.persistence.graph_db.base import GraphDBAdapter
from uds3.persistence.relational_db.base import RelationalDBAdapter
from uds3.persistence.file_backend.storage_manager import FileStorageManager


class DatabaseType(Enum):
    """Unterstützte Datenbank-Typen"""
    VECTOR = "vector"
    GRAPH = "graph"
    RELATIONAL = "relational"
    FILE = "file"


@dataclass
class UDS3PersistenceConfig:
    """Konfiguration für Polyglot Persistence"""
    
    # Vector DB
    vector_db_type: str = "chromadb"  # "chromadb" | "pgvector"
    vector_db_path: Optional[str] = None
    vector_db_host: Optional[str] = None
    vector_db_port: Optional[int] = None
    
    # Graph DB
    graph_db_type: str = "neo4j"  # "neo4j" | "networkx"
    graph_db_uri: Optional[str] = None
    graph_db_user: Optional[str] = None
    graph_db_password: Optional[str] = None
    
    # Relational DB
    relational_db_type: str = "postgresql"  # "postgresql" | "sqlite"
    relational_db_uri: Optional[str] = None
    
    # File Backend
    file_backend_root: str = "./uds3_storage"
    
    # Embedding Model
    embedding_model: str = "deutsche-telekom/gbert-base"
    
    # Performance
    enable_caching: bool = True
    batch_size: int = 100


class UDS3PolyglotManager:
    """
    Kern-Orchestrator für UDS3 Polyglot Persistence
    
    Koordiniert alle Datenbank-Adapter und bietet einheitliche APIs
    für CRUD-Operationen, Queries und LLM-Retrieval.
    """
    
    def __init__(self, config: UDS3PersistenceConfig):
        """
        Initialisiert alle Datenbank-Adapter
        
        Args:
            config: Persistence-Konfiguration
        """
        self.config = config
        
        # Adapter initialisieren
        self.vector_db = self._init_vector_db()
        self.graph_db = self._init_graph_db()
        self.relational_db = self._init_relational_db()
        self.file_backend = FileStorageManager(config.file_backend_root)
        
        # Cache
        self._query_cache = {} if config.enable_caching else None
    
    # === Adapter-Initialisierung ===
    
    def _init_vector_db(self) -> VectorDBAdapter:
        """Initialisiert Vector DB Adapter"""
        if self.config.vector_db_type == "chromadb":
            from uds3.persistence.vector_db.chromadb_adapter import ChromaDBAdapter
            return ChromaDBAdapter(
                persist_directory=self.config.vector_db_path,
                embedding_model=self.config.embedding_model
            )
        elif self.config.vector_db_type == "pgvector":
            from uds3.persistence.vector_db.pgvector_adapter import PgVectorAdapter
            return PgVectorAdapter(
                connection_string=self.config.vector_db_uri,
                embedding_model=self.config.embedding_model
            )
        else:
            raise ValueError(f"Unsupported vector DB: {self.config.vector_db_type}")
    
    def _init_graph_db(self) -> GraphDBAdapter:
        """Initialisiert Graph DB Adapter"""
        if self.config.graph_db_type == "neo4j":
            from uds3.persistence.graph_db.neo4j_adapter import Neo4jAdapter
            return Neo4jAdapter(
                uri=self.config.graph_db_uri,
                user=self.config.graph_db_user,
                password=self.config.graph_db_password
            )
        elif self.config.graph_db_type == "networkx":
            from uds3.persistence.graph_db.networkx_adapter import NetworkXAdapter
            return NetworkXAdapter()
        else:
            raise ValueError(f"Unsupported graph DB: {self.config.graph_db_type}")
    
    def _init_relational_db(self) -> RelationalDBAdapter:
        """Initialisiert Relational DB Adapter"""
        if self.config.relational_db_type == "postgresql":
            from uds3.persistence.relational_db.postgresql_adapter import PostgreSQLAdapter
            return PostgreSQLAdapter(self.config.relational_db_uri)
        elif self.config.relational_db_type == "sqlite":
            from uds3.persistence.relational_db.sqlite_adapter import SQLiteAdapter
            return SQLiteAdapter(self.config.relational_db_uri)
        else:
            raise ValueError(f"Unsupported relational DB: {self.config.relational_db_type}")
    
    # === High-Level APIs ===
    
    def save_process(
        self, 
        process_data: Dict[str, Any],
        app_domain: str = "generic"
    ) -> str:
        """
        Speichert Prozess in allen relevanten DBs
        
        Args:
            process_data: Prozess-Daten (muss Base-Schema erfüllen)
            app_domain: App-Domain (z.B. "vpb", "legal", "generic")
        
        Returns:
            process_id: UUID des gespeicherten Prozesses
        """
        process_id = process_data.get("process_id")
        
        # 1. Relational DB: Strukturierte Daten
        self.relational_db.insert_process(process_data)
        
        # 2. Vector DB: Embeddings für Semantic Search
        embedding_text = self._build_process_embedding_text(process_data)
        self.vector_db.add_embedding(
            id=process_id,
            text=embedding_text,
            metadata={
                "process_id": process_id,
                "name": process_data.get("name"),
                "domain": app_domain,
                "authority": process_data.get("authority"),
                "legal_context": process_data.get("legal_context")
            }
        )
        
        # 3. Graph DB: Prozess-Knoten und Beziehungen
        self.graph_db.create_process_node(process_data)
        
        # 4. File Backend: Vollständiges Dokument
        self.file_backend.save_json(
            path=f"{app_domain}/processes/{process_id}.json",
            data=process_data
        )
        
        return process_id
    
    def semantic_search(
        self,
        query: str,
        domain: Optional[str] = None,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantische Suche über alle Prozesse
        
        Args:
            query: Suchanfrage (natürlichsprachig)
            domain: Optional App-Domain-Filter
            top_k: Anzahl Ergebnisse
            filters: Zusätzliche Metadaten-Filter
        
        Returns:
            Liste von Prozess-IDs mit Scores
        """
        # Cache-Check
        cache_key = f"{query}:{domain}:{top_k}"
        if self._query_cache and cache_key in self._query_cache:
            return self._query_cache[cache_key]
        
        # Vector Search
        search_filters = filters or {}
        if domain:
            search_filters["domain"] = domain
        
        results = self.vector_db.search(
            query_text=query,
            top_k=top_k,
            filters=search_filters
        )
        
        # Cache
        if self._query_cache:
            self._query_cache[cache_key] = results
        
        return results
    
    def get_process_graph(
        self,
        process_id: str,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Holt Prozess-Graph aus Neo4j
        
        Args:
            process_id: Prozess-ID
            depth: Traversierungs-Tiefe (1 = direkte Nachbarn)
        
        Returns:
            Graph-Daten (Nodes + Edges)
        """
        return self.graph_db.get_process_subgraph(process_id, depth)
    
    def get_process_details(
        self,
        process_id: str,
        include_elements: bool = True
    ) -> Dict[str, Any]:
        """
        Holt detaillierte Prozess-Daten aus PostgreSQL
        
        Args:
            process_id: Prozess-ID
            include_elements: Lade auch Elemente und Connections
        
        Returns:
            Vollständige Prozess-Daten
        """
        return self.relational_db.get_process(process_id, include_elements)
    
    def polyglot_query(
        self,
        query: str,
        domain: str = "generic",
        strategy: str = "semantic_first"
    ) -> Dict[str, Any]:
        """
        Kombinierte Query über alle DBs (für RAG Pipeline)
        
        Args:
            query: Natürlichsprachige Query
            domain: App-Domain
            strategy: "semantic_first" | "graph_first" | "hybrid"
        
        Returns:
            Kombinierte Ergebnisse aus allen DBs
        """
        if strategy == "semantic_first":
            # 1. Vector Search
            similar = self.semantic_search(query, domain, top_k=10)
            process_ids = [r["id"] for r in similar]
            
            # 2. Graph Context
            graphs = [self.get_process_graph(pid) for pid in process_ids[:5]]
            
            # 3. SQL Details
            details = [self.get_process_details(pid) for pid in process_ids[:5]]
            
            return {
                "semantic_results": similar,
                "graph_context": graphs,
                "process_details": details
            }
        
        # Weitere Strategien implementierbar
        raise NotImplementedError(f"Strategy {strategy} not implemented")
    
    # === Helper Methods ===
    
    def _build_process_embedding_text(self, process_data: Dict[str, Any]) -> str:
        """
        Baut strukturierten Text für Embeddings
        
        Optimiert für deutsche Verwaltungssprache und Semantic Search.
        """
        parts = []
        
        # Name (3x für Gewichtung)
        name = process_data.get("name", "")
        parts.extend([name, name, name])
        
        # Beschreibung
        if desc := process_data.get("description"):
            parts.append(desc)
        
        # Context Labels
        if ctx := process_data.get("legal_context"):
            parts.append(f"Rechtsgebiet: {ctx}")
        
        if auth := process_data.get("authority"):
            parts.append(f"Zuständige Behörde: {auth}")
        
        # Legal Basis
        if legal_basis := process_data.get("legal_basis"):
            if isinstance(legal_basis, list):
                parts.append("Rechtsgrundlagen: " + ", ".join(legal_basis))
            else:
                parts.append(f"Rechtsgrundlage: {legal_basis}")
        
        return " | ".join(parts)
    
    def close(self):
        """Schließt alle DB-Verbindungen"""
        self.vector_db.close()
        self.graph_db.close()
        self.relational_db.close()
```

---

### 3.2 Vector DB Adapter (Abstract Base Class)

**Datei:** `uds3/persistence/vector_db/base.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np


class VectorDBAdapter(ABC):
    """
    Abstract Base Class für Vector DB Adapter
    
    Implementierungen: ChromaDB, pgvector
    """
    
    @abstractmethod
    def __init__(self, embedding_model: str, **kwargs):
        """
        Initialisiert Vector DB
        
        Args:
            embedding_model: Name des Embedding-Modells
            **kwargs: DB-spezifische Parameter
        """
        pass
    
    @abstractmethod
    def create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Erstellt eine Collection/Table für Embeddings
        
        Args:
            name: Collection-Name (z.B. "uds3_processes")
            metadata: Optional Metadaten
        """
        pass
    
    @abstractmethod
    def add_embedding(
        self,
        id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        collection: str = "default"
    ):
        """
        Fügt Text-Embedding hinzu
        
        Args:
            id: Eindeutige ID
            text: Text zum Embedden
            metadata: Metadaten für Filterung
            collection: Collection-Name
        """
        pass
    
    @abstractmethod
    def add_embeddings_batch(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        collection: str = "default"
    ):
        """Batch-Insert für Performance"""
        pass
    
    @abstractmethod
    def search(
        self,
        query_text: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        collection: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Semantische Suche
        
        Args:
            query_text: Suchanfrage
            top_k: Anzahl Ergebnisse
            filters: Metadaten-Filter
            collection: Collection-Name
        
        Returns:
            Liste von {id, score, metadata}
        """
        pass
    
    @abstractmethod
    def delete_embedding(self, id: str, collection: str = "default"):
        """Löscht Embedding"""
        pass
    
    @abstractmethod
    def close(self):
        """Schließt DB-Verbindung"""
        pass
```

---

### 3.3 Graph DB Adapter (Abstract Base Class)

**Datei:** `uds3/persistence/graph_db/base.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class GraphDBAdapter(ABC):
    """
    Abstract Base Class für Graph DB Adapter
    
    Implementierungen: Neo4j, NetworkX
    """
    
    @abstractmethod
    def __init__(self, **kwargs):
        """Initialisiert Graph DB"""
        pass
    
    @abstractmethod
    def create_process_node(self, process_data: Dict[str, Any]) -> str:
        """
        Erstellt Process-Knoten
        
        Args:
            process_data: Prozess-Daten (muss process_id enthalten)
        
        Returns:
            node_id
        """
        pass
    
    @abstractmethod
    def create_element_node(
        self,
        element_data: Dict[str, Any],
        process_id: str
    ) -> str:
        """
        Erstellt Element-Knoten und CONTAINS-Beziehung
        
        Args:
            element_data: Element-Daten
            process_id: Zugehöriger Prozess
        
        Returns:
            node_id
        """
        pass
    
    @abstractmethod
    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Erstellt Beziehung zwischen Knoten
        
        Args:
            source_id: Quell-Knoten ID
            target_id: Ziel-Knoten ID
            relationship_type: z.B. "CONNECTS_TO", "BASED_ON"
            properties: Optional Eigenschaften (z.B. condition, probability)
        """
        pass
    
    @abstractmethod
    def get_process_subgraph(
        self,
        process_id: str,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Holt Subgraph um Prozess
        
        Args:
            process_id: Prozess-ID
            depth: Traversierungs-Tiefe
        
        Returns:
            {nodes: [...], edges: [...]}
        """
        pass
    
    @abstractmethod
    def find_paths(
        self,
        start_element_id: str,
        end_element_id: str,
        max_length: int = 10
    ) -> List[List[str]]:
        """
        Findet Pfade zwischen Elementen
        
        Args:
            start_element_id: Start-Element
            end_element_id: Ziel-Element
            max_length: Maximale Pfadlänge
        
        Returns:
            Liste von Pfaden (jeweils Liste von Element-IDs)
        """
        pass
    
    @abstractmethod
    def close(self):
        """Schließt DB-Verbindung"""
        pass
```

---

### 3.4 German BERT Embeddings

**Datei:** `uds3/embeddings/german_embeddings.py`

```python
from typing import List, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import hashlib
import pickle
from pathlib import Path


class UDS3GermanEmbeddings:
    """
    Deutsche BERT-Embeddings für UDS3
    
    Optimiert für deutsche Verwaltungssprache, Gesetze, Prozesse.
    Unterstützt Caching für Performance.
    """
    
    # Empfohlene Modelle für deutsche Verwaltung
    MODELS = {
        "gbert": "deutsche-telekom/gbert-base",  # 768 dim, beste Qualität
        "gbert-large": "deutsche-telekom/gbert-large",  # 1024 dim
        "paraphrase": "paraphrase-multilingual-mpnet-base-v2",  # 768 dim
        "e5-multilingual": "intfloat/multilingual-e5-large",  # 1024 dim
    }
    
    def __init__(
        self,
        model_name: str = "gbert",
        cache_dir: Optional[str] = None,
        device: str = "cpu"
    ):
        """
        Initialisiert Embedding-Modell
        
        Args:
            model_name: Modell-Key aus MODELS oder HuggingFace Model ID
            cache_dir: Verzeichnis für Embedding-Cache
            device: "cpu" oder "cuda"
        """
        # Modell laden
        model_id = self.MODELS.get(model_name, model_name)
        self.model = SentenceTransformer(model_id, device=device)
        self.model_name = model_name
        
        # Cache
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._cache = {}
    
    def embed_text(
        self,
        text: str,
        domain_hint: Optional[str] = None,
        use_cache: bool = True
    ) -> np.ndarray:
        """
        Erstellt Embedding für Text
        
        Args:
            text: Zu embeddender Text
            domain_hint: Optional Domain ("vpb", "legal", etc.) für Optimierungen
            use_cache: Verwende Cache
        
        Returns:
            Embedding-Vektor (768 oder 1024 dim)
        """
        # Cache-Key
        cache_key = self._get_cache_key(text, domain_hint)
        
        # Cache-Lookup
        if use_cache:
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            if self.cache_dir:
                cached = self._load_from_disk_cache(cache_key)
                if cached is not None:
                    self._cache[cache_key] = cached
                    return cached
        
        # Embedding berechnen
        # Domain-spezifische Präfixe (für e5-Modelle)
        if "e5" in self.model_name and domain_hint:
            text = f"passage: {text}"  # e5-spezifisches Präfix
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # Cache
        if use_cache:
            self._cache[cache_key] = embedding
            if self.cache_dir:
                self._save_to_disk_cache(cache_key, embedding)
        
        return embedding
    
    def embed_texts_batch(
        self,
        texts: List[str],
        domain_hint: Optional[str] = None,
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Batch-Embedding für Performance
        
        Args:
            texts: Liste von Texten
            domain_hint: Optional Domain
            batch_size: Batch-Größe
        
        Returns:
            Array von Embeddings (shape: [len(texts), embedding_dim])
        """
        # Domain-Präfixe
        if "e5" in self.model_name and domain_hint:
            texts = [f"passage: {t}" for t in texts]
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100
        )
        
        return embeddings
    
    def compute_similarity(
        self,
        text1: str,
        text2: str,
        domain_hint: Optional[str] = None
    ) -> float:
        """
        Berechnet Cosine-Ähnlichkeit zwischen Texten
        
        Args:
            text1: Erster Text
            text2: Zweiter Text
            domain_hint: Optional Domain
        
        Returns:
            Ähnlichkeit (0.0 - 1.0)
        """
        emb1 = self.embed_text(text1, domain_hint)
        emb2 = self.embed_text(text2, domain_hint)
        
        # Cosine Similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        return float(similarity)
    
    def get_embedding_dimension(self) -> int:
        """Returns embedding dimension (768 or 1024)"""
        return self.model.get_sentence_embedding_dimension()
    
    # === Cache Helpers ===
    
    def _get_cache_key(self, text: str, domain_hint: Optional[str]) -> str:
        """Generiert Cache-Key (SHA256)"""
        content = f"{self.model_name}:{domain_hint}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_from_disk_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """Lädt Embedding aus Disk-Cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        return None
    
    def _save_to_disk_cache(self, cache_key: str, embedding: np.ndarray):
        """Speichert Embedding in Disk-Cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        with open(cache_file, "wb") as f:
            pickle.dump(embedding, f)
    
    def clear_cache(self):
        """Löscht Memory- und Disk-Cache"""
        self._cache.clear()
        if self.cache_dir:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
```

---

### 3.5 Generic RAG Pipeline

**Datei:** `uds3/llm/rag_pipeline.py`

```python
from typing import List, Dict, Any, Optional
from enum import Enum

from uds3.persistence.polyglot_manager import UDS3PolyglotManager
from uds3.llm.clients.ollama_client import OllamaClient


class QueryType(Enum):
    """Generische Query-Typen für RAG"""
    SEMANTIC_SEARCH = "semantic_search"
    DETAIL_LOOKUP = "detail_lookup"
    GRAPH_TRAVERSAL = "graph_traversal"
    AGGREGATION = "aggregation"
    COMPARISON = "comparison"
    GENERAL = "general"


class UDS3GenericRAG:
    """
    Generische RAG-Pipeline für UDS3
    
    Apps können diese Klasse erweitern und domain-spezifische
    Query-Typen und Retrieval-Strategien hinzufügen.
    """
    
    def __init__(
        self,
        polyglot_manager: UDS3PolyglotManager,
        llm_model: str = "llama3.1:8b",
        llm_host: str = "http://localhost:11434"
    ):
        """
        Initialisiert RAG Pipeline
        
        Args:
            polyglot_manager: Polyglot Persistence Manager
            llm_model: Ollama Modell-Name
            llm_host: Ollama Server URL
        """
        self.polyglot = polyglot_manager
        self.llm = OllamaClient(host=llm_host, model=llm_model)
        
        # Domain (kann von Apps überschrieben werden)
        self.domain = "generic"
    
    def answer_query(
        self,
        query: str,
        max_context_tokens: int = 4000
    ) -> str:
        """
        Beantwortet Query mit RAG-Pipeline
        
        Args:
            query: Natürlichsprachige Anfrage
            max_context_tokens: Max. Token für Context
        
        Returns:
            LLM-generierte Antwort
        """
        # 1. Query Classification
        query_type = self.classify_query(query)
        
        # 2. Retrieval (domain-spezifisch überschreibbar)
        context = self.retrieve_context(query, query_type)
        
        # 3. Prompt Assembly
        prompt = self.build_prompt(query, context, max_context_tokens)
        
        # 4. LLM Generation
        answer = self.llm.generate(prompt)
        
        return answer
    
    def classify_query(self, query: str) -> QueryType:
        """
        Klassifiziert Query-Typ (regel-basiert)
        
        Apps können diese Methode überschreiben für domain-spezifische
        Classification (z.B. mit eigenen Keywords oder ML-Classifier).
        
        Args:
            query: Anfrage
        
        Returns:
            QueryType
        """
        query_lower = query.lower()
        
        # Semantic Search
        if any(kw in query_lower for kw in ["ähnlich", "vergleichbar", "finde", "suche"]):
            return QueryType.SEMANTIC_SEARCH
        
        # Graph Traversal
        if any(kw in query_lower for kw in ["pfad", "weg", "führt zu", "verbindung"]):
            return QueryType.GRAPH_TRAVERSAL
        
        # Aggregation
        if any(kw in query_lower for kw in ["wie viele", "durchschnitt", "gesamt", "anzahl"]):
            return QueryType.AGGREGATION
        
        # Detail Lookup
        if any(kw in query_lower for kw in ["details", "informationen über", "beschreibung"]):
            return QueryType.DETAIL_LOOKUP
        
        # Comparison
        if any(kw in query_lower for kw in ["unterschied", "vergleiche", "vs", "oder"]):
            return QueryType.COMPARISON
        
        return QueryType.GENERAL
    
    def retrieve_context(
        self,
        query: str,
        query_type: QueryType
    ) -> Dict[str, Any]:
        """
        Holt relevanten Context aus Polyglot DBs
        
        Apps sollten diese Methode überschreiben für domain-spezifische
        Retrieval-Strategien.
        
        Args:
            query: Anfrage
            query_type: Klassifizierter Query-Typ
        
        Returns:
            Context-Dictionary
        """
        if query_type == QueryType.SEMANTIC_SEARCH:
            # Vector Search
            results = self.polyglot.semantic_search(
                query=query,
                domain=self.domain,
                top_k=5
            )
            return {"semantic_results": results}
        
        elif query_type == QueryType.GRAPH_TRAVERSAL:
            # Graph Query (benötigt process_id - in App extrahieren)
            return {"message": "Graph traversal requires process_id"}
        
        elif query_type == QueryType.AGGREGATION:
            # SQL Aggregation (App-spezifisch)
            return {"message": "Aggregation not implemented in base class"}
        
        else:
            # Fallback: Semantic Search
            results = self.polyglot.semantic_search(query, self.domain, top_k=3)
            return {"results": results}
    
    def build_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        max_tokens: int = 4000
    ) -> str:
        """
        Baut strukturierten Prompt
        
        Apps können diese Methode überschreiben für domain-spezifische
        Prompt-Templates.
        
        Args:
            query: Anfrage
            context: Retrieved Context
            max_tokens: Max. Tokens
        
        Returns:
            Prompt-String
        """
        prompt_parts = []
        
        # System Instruction
        prompt_parts.append(
            "Du bist ein Experte für deutsche Verwaltungsprozesse. "
            "Beantworte die Frage basierend auf dem folgenden Kontext."
        )
        
        # Context
        prompt_parts.append("\n--- KONTEXT ---")
        
        if "semantic_results" in context:
            for i, result in enumerate(context["semantic_results"][:5], 1):
                meta = result.get("metadata", {})
                prompt_parts.append(
                    f"\n{i}. {meta.get('name', 'Unbekannt')}\n"
                    f"   Behörde: {meta.get('authority', 'N/A')}\n"
                    f"   Score: {result.get('score', 0):.2f}"
                )
        
        # Query
        prompt_parts.append(f"\n--- FRAGE ---\n{query}")
        
        prompt_parts.append("\n--- ANTWORT ---")
        
        prompt = "\n".join(prompt_parts)
        
        # Token-Limit (grob: 1 Token ≈ 4 chars)
        max_chars = max_tokens * 4
        if len(prompt) > max_chars:
            prompt = prompt[:max_chars] + "\n...[gekürzt]"
        
        return prompt
```

---

## 🚀 4. Implementierungs-Roadmap

### Phase 1: UDS3-Kern-Setup (Wochen 1-3)

**Woche 1: Grundstruktur & Adapter-Interfaces**
- [ ] Repository `C:\VCC\UDS3` erstellen
- [ ] Ordnerstruktur aufbauen
- [ ] `setup.py` + `requirements.txt`
- [ ] Abstract Base Classes:
  - [ ] `VectorDBAdapter` (base.py)
  - [ ] `GraphDBAdapter` (base.py)
  - [ ] `RelationalDBAdapter` (base.py)
- [ ] `UDS3PersistenceConfig` Dataclass

**Woche 2: Erste Adapter-Implementierungen**
- [ ] **ChromaDB Adapter** (vollständig)
  - [ ] Collections erstellen
  - [ ] Embeddings hinzufügen (single + batch)
  - [ ] Semantic Search
  - [ ] Tests
- [ ] **NetworkX Adapter** (Development-Fallback für Neo4j)
  - [ ] Graph-Operationen
  - [ ] Pfad-Suche
  - [ ] Tests
- [ ] **SQLite Adapter** (Development-Fallback für PostgreSQL)
  - [ ] Base Schema erstellen
  - [ ] CRUD-Operationen
  - [ ] Tests

**Woche 3: German Embeddings & RAG**
- [ ] **UDS3GermanEmbeddings**
  - [ ] Model Loading (gbert-base)
  - [ ] Caching (Memory + Disk)
  - [ ] Batch-Processing
  - [ ] Tests
- [ ] **UDS3GenericRAG**
  - [ ] Query Classification
  - [ ] Retrieval-Framework
  - [ ] Prompt Building
  - [ ] Tests
- [ ] **UDS3PolyglotManager**
  - [ ] Adapter-Orchestration
  - [ ] `save_process()`, `semantic_search()`
  - [ ] Integration Tests

### Phase 2: Production Adapters (Wochen 4-5)

**Woche 4: PostgreSQL & Neo4j**
- [ ] **PostgreSQL Base Schema**
  - [ ] SQL Migration: `001_base_schema.sql`
  - [ ] Tables: `uds3_processes`, `uds3_elements`, `uds3_connections`
  - [ ] ENUMs, Indexes, Triggers
  - [ ] `002_embeddings.sql` (Embedding Registry)
- [ ] **PostgreSQL Adapter**
  - [ ] Connection Management
  - [ ] CRUD mit Base Schema
  - [ ] Tests
- [ ] **Neo4j Base Schema**
  - [ ] Cypher Migration: `001_base_schema.cypher`
  - [ ] Constraints, Indexes
  - [ ] Base Node Types & Relationships

**Woche 5: Neo4j Adapter & pgvector**
- [ ] **Neo4j Adapter**
  - [ ] Node/Relationship Creation
  - [ ] Subgraph Retrieval
  - [ ] Path Finding
  - [ ] Tests
- [ ] **pgvector Adapter** (Alternative zu ChromaDB)
  - [ ] Extension Setup
  - [ ] Vector Search mit PostgreSQL
  - [ ] Tests
- [ ] **File Backend**
  - [ ] `FileStorageManager`
  - [ ] Hierarchische Struktur (by_id, by_authority, etc.)
  - [ ] Tests

### Phase 3: VPB-Integration (Woche 6)

**VPB als erste App mit UDS3-Kern**
- [ ] **VPB Polyglot Adapter**
  - [ ] `VPBPolyglotAdapter` nutzt `UDS3PolyglotManager`
  - [ ] VPB → UDS3 Base Schema Mapping
  - [ ] VPB-spezifische Extensions (SQL)
- [ ] **VPB RAG Pipeline**
  - [ ] `VPBRAG(UDS3GenericRAG)` - Erbt von Kern
  - [ ] VPB-spezifische Query Types
  - [ ] VPB Context Formatters
- [ ] **Migration**
  - [ ] SQLite → UDS3 Polyglot
  - [ ] Daten-Migration-Script
  - [ ] Validierung

---

## 📊 5. Success Metrics

### 5.1 Technische Metriken

| Metrik | Ziel | Messung |
|--------|------|---------|
| **Vector Search Latency** | <50ms | ChromaDB search() call |
| **Graph Traversal Latency** | <100ms | Neo4j Cypher query |
| **SQL Query Latency** | <30ms | PostgreSQL SELECT |
| **End-to-End RAG Query** | <500ms | answer_query() total |
| **Embedding Quality** | >0.8 Cosine Sim | Similar process pairs |
| **Cache Hit Rate** | >70% | Memory + Disk Cache |

### 5.2 Funktionale Metriken

| Metrik | Ziel | Validierung |
|--------|------|-------------|
| **Semantic Search Precision** | >85% | Top-5 relevante Ergebnisse |
| **Graph Path Accuracy** | >95% | Korrekte Pfade gefunden |
| **LLM Context Relevance** | >90% | Manuelle Evaluation |
| **API Compatibility** | 100% | Alle Apps nutzen gleiche APIs |

### 5.3 Architektur-Metriken

| Metrik | Ziel | Validierung |
|--------|------|-------------|
| **Code Reusability** | >80% | Kern-Code in mehreren Apps |
| **Extension Points** | 5+ | Apps können erweitern ohne Fork |
| **Test Coverage** | >85% | Unit + Integration Tests |
| **Documentation Coverage** | 100% | Alle Public APIs dokumentiert |

---

## 🔧 6. Deployment & Configuration

### 6.1 Development Setup

```bash
# UDS3 Kern installieren
git clone https://github.com/your-org/uds3.git C:\VCC\UDS3
cd C:\VCC\UDS3
pip install -e .

# Development DBs (SQLite + NetworkX - keine externen Services)
export UDS3_ENV=development
python -m uds3.setup --init-dev
```

**Development Config:**
```python
from uds3.persistence import UDS3PersistenceConfig

dev_config = UDS3PersistenceConfig(
    vector_db_type="chromadb",
    vector_db_path="./dev_data/chromadb",
    graph_db_type="networkx",  # In-Memory
    relational_db_type="sqlite",
    relational_db_uri="sqlite:///./dev_data/uds3.db",
    file_backend_root="./dev_data/files"
)
```

### 6.2 Production Setup

```bash
# UDS3 Kern installieren
pip install uds3

# Production DBs (PostgreSQL + Neo4j + ChromaDB)
export UDS3_ENV=production

# Datenbanken erstellen
psql -U postgres -c "CREATE DATABASE uds3_production;"
# Neo4j: Web UI http://localhost:7474

# Schema migrieren
python -m uds3.setup --migrate-sql sql/postgresql/001_base_schema.sql
python -m uds3.setup --migrate-cypher cypher/001_base_schema.cypher
```

**Production Config:**
```python
from uds3.persistence import UDS3PersistenceConfig

prod_config = UDS3PersistenceConfig(
    vector_db_type="chromadb",  # oder "pgvector"
    vector_db_path="/var/lib/uds3/chromadb",
    
    graph_db_type="neo4j",
    graph_db_uri="bolt://localhost:7687",
    graph_db_user="neo4j",
    graph_db_password="your_password",
    
    relational_db_type="postgresql",
    relational_db_uri="postgresql://uds3_user:password@localhost:5432/uds3_production",
    
    file_backend_root="/var/lib/uds3/files",
    
    embedding_model="deutsche-telekom/gbert-base",
    enable_caching=True
)
```

---

## 📖 7. App-Integration: Best Practices

### 7.1 VPB als Referenz-Implementierung

**VPB Adapter:**
```python
# VPB/vpb_polyglot_adapter.py
from uds3.persistence import UDS3PolyglotManager, UDS3PersistenceConfig

class VPBPolyglotAdapter:
    """VPB-spezifischer Adapter für UDS3 Polyglot Persistence"""
    
    def __init__(self, config: UDS3PersistenceConfig):
        self.polyglot = UDS3PolyglotManager(config)
        self.domain = "vpb"
    
    def save_vpb_process(self, vpb_process_data: Dict[str, Any]) -> str:
        """
        Speichert VPB-Prozess in UDS3
        
        Mapped VPB-spezifische Felder auf UDS3 Base Schema
        """
        # UDS3 Base Schema
        uds3_process = {
            "process_id": vpb_process_data["process_id"],
            "name": vpb_process_data["name"],
            "description": vpb_process_data.get("description"),
            "process_type": "vpb",
            "authority": vpb_process_data.get("authority"),
            "legal_basis": vpb_process_data.get("legal_basis"),
            "legal_context": vpb_process_data.get("legal_context"),
            
            # VPB-spezifisch in JSONB
            "app_specific_data": {
                "vpb_ui_state": vpb_process_data.get("ui_state"),
                "vpb_element_types": vpb_process_data.get("element_types"),
                "vpb_compliance": vpb_process_data.get("compliance_scores")
            }
        }
        
        return self.polyglot.save_process(uds3_process, app_domain="vpb")
```

### 7.2 Schema-Extensions

**VPB SQL Extension:**
```sql
-- VPB/sql/vpb_extensions.sql
-- Erweitert UDS3 Base Schema

ALTER TABLE uds3_processes
ADD COLUMN IF NOT EXISTS vpb_ui_state JSONB;

ALTER TABLE uds3_processes
ADD COLUMN IF NOT EXISTS vpb_complexity_score NUMERIC(3,2);

ALTER TABLE uds3_processes
ADD COLUMN IF NOT EXISTS vpb_automation_score NUMERIC(3,2);

-- VPB-spezifische Tabelle
CREATE TABLE IF NOT EXISTS vpb_element_properties (
    element_id UUID PRIMARY KEY REFERENCES uds3_elements(element_id),
    element_type VARCHAR(50) NOT NULL,  -- 23 VPB Types
    canvas_x INTEGER,
    canvas_y INTEGER,
    vpb_compliance_tags TEXT[],
    vpb_deadline_type VARCHAR(50)
);
```

---

## ✅ 8. Entscheidungs-Matrix: UDS3 vs. App

**Quick Reference für Entwickler:**

| Feature | UDS3-Kern | App-Extension | Begründung |
|---------|-----------|---------------|------------|
| DB-Adapter (Vector/Graph/SQL) | ✅ | - | Alle Apps brauchen |
| German BERT Embeddings | ✅ | - | Verwaltungssprache-generisch |
| RAG Pipeline Framework | ✅ | - | Erweiterbar |
| Base Process Schema | ✅ | - | Gemeinsame Struktur |
| Query Orchestrator | ✅ | - | Kombiniert alle DBs |
| File Storage Manager | ✅ | - | Hierarchisch, generisch |
| VPB Element Types (23) | - | ✅ | VPB-spezifisch |
| VPB UI State (Canvas) | - | ✅ | VPB Designer |
| Legal Document Types | - | ✅ | Rechtsdatenbank-App |
| Case Law Relationships | - | ✅ | Rechtsprechungs-App |
| Custom Query Types | - | ✅ | Domain-spezifisch |
| Custom Prompt Templates | - | ✅ | Domain-spezifisch |

---

## 🔗 9. Referenzen & Related Documents

**UDS3 Kern-Dokumentation:**
- `UDS3_POLYGLOT_PERSISTENCE_CORE.md` (dieses Dokument)
- `API_REFERENCE.md` (generiert aus Code-Docstrings)
- `DEPLOYMENT_GUIDE.md` (Production Setup)
- `MIGRATION_GUIDE.md` (App-Migration zu UDS3)

**VPB-Integration:**
- `VPB/docs/UDS3_VPB_POLYGLOT_PERSISTENCE_PLAN.md` (VPB-spezifischer Plan)
- `VPB/docs/VPB_UDS3_INTEGRATION_PLAN.md` (Legacy Integration Plan)

**Externe Ressourcen:**
- ChromaDB: https://docs.trychroma.com/
- Neo4j Python Driver: https://neo4j.com/docs/python-manual/
- pgvector: https://github.com/pgvector/pgvector
- sentence-transformers: https://www.sbert.net/
- deutsche-telekom/gbert: https://huggingface.co/deutsche-telekom/gbert-base

---

## 📝 10. Änderungs-Historie

| Version | Datum | Autor | Änderungen |
|---------|-------|-------|------------|
| 1.0 | 2025-10-18 | Architecture Team | Initial ADR - Kern-Komponenten definiert |

---

**Status:** 🟢 APPROVED - Ready for Implementation

**Next Steps:**
1. Repository `C:\VCC\UDS3` erstellen
2. Ordnerstruktur aufbauen (siehe Abschnitt 2.1)
3. Abstract Base Classes implementieren (Woche 1)
4. Development Adapters (ChromaDB, NetworkX, SQLite) - Woche 2
5. VPB-Integration als Pilot (Woche 6)

**Review:** Alle Stakeholder genehmigt ✅
