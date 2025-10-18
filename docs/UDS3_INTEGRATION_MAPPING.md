# UDS3 Polyglot Persistence - Struktur-Mapping & Integration

**Datum:** 18. Oktober 2025  
**Version:** 1.0  
**Autor:** Integration Team  

---

## 📋 Ziel

Mapping zwischen:
- **Bestehendem UDS3** (`C:\VCC\uds3\`)
- **Neuem flachen Design** (geplant für Polyglot Persistence)
- **Integration-Strategie**

---

## 🗺️ 1. Existierende UDS3-Struktur (IST-Zustand)

### 1.1 Hauptverzeichnisse

```
C:\VCC\uds3\
├── database/                    # ⭐ KERN: Polyglot Database System
│   ├── database_api_base.py     # Abstract Base Class
│   ├── database_api_chromadb.py # ChromaDB Implementation
│   ├── database_api_neo4j.py    # Neo4j Implementation
│   ├── database_api_postgresql.py # PostgreSQL Implementation
│   ├── database_api_sqlite.py   # SQLite Implementation
│   ├── database_api_file_storage.py # File Storage
│   ├── database_manager.py      # Manager/Orchestrator
│   ├── saga_orchestrator.py     # SAGA Pattern für Transaktionen
│   └── docs/                    # Database Dokumentation
│
├── search/                      # Search API
│   └── search_api.py
│
├── docs/                        # Dokumentation
│   ├── UDS3_POLYGLOT_PERSISTENCE_CORE.md  # ✅ Bereits vorhanden!
│   └── ...
│
├── uds3_core.py                 # Core System
├── uds3_polyglot_query.py       # Polyglot Query Engine
├── uds3_dsgvo_core.py           # DSGVO Compliance
├── uds3_streaming_operations.py # Streaming
├── config.py                    # Configuration
└── ...
```

### 1.2 Wichtige Erkenntnisse

✅ **UDS3 hat bereits:**
- Polyglot Database System (`database/` Ordner)
- Alle 4 DB-Adapter (ChromaDB, Neo4j, PostgreSQL, SQLite)
- File Storage Adapter
- Database Manager (Orchestrator)
- SAGA Pattern für verteilte Transaktionen
- Polyglot Query Engine (`uds3_polyglot_query.py`)
- DSGVO Compliance Layer
- Streaming Operations
- Umfangreiche Dokumentation

❌ **UDS3 fehlt:**
- German BERT Embeddings (nicht gefunden)
- Generic RAG Pipeline (nicht gefunden)
- LLM Integration (Ollama Client)
- Flat Structure (database/ ist Unterordner)

---

## 🔄 2. Mapping: Bestehendes UDS3 ↔ Neues flaches Design

| Neue Datei (flach) | Existierende UDS3-Datei | Status | Aktion |
|--------------------|-------------------------|--------|--------|
| **Polyglot Manager** | | | |
| `polyglot_manager.py` | `database/database_manager.py` | ✅ Existiert | Erweitern für LLM-RAG |
| `config.py` | `config.py` + `database/config.py` | ✅ Existiert | Konsolidieren |
| **Vector DB** | | | |
| `vector_base.py` | `database/database_api_base.py` | ✅ Existiert | Verwenden |
| `vector_chromadb.py` | `database/database_api_chromadb.py` | ✅ Existiert | Verwenden |
| `vector_pgvector.py` | ❌ Nicht vorhanden | ❌ Fehlt | **NEU erstellen** |
| **Graph DB** | | | |
| `graph_base.py` | `database/database_api_base.py` | ✅ Existiert | Verwenden |
| `graph_neo4j.py` | `database/database_api_neo4j.py` | ✅ Existiert | Verwenden |
| `graph_networkx.py` | ❌ Nicht vorhanden | ❌ Fehlt | **NEU erstellen** |
| **Relational DB** | | | |
| `relational_base.py` | `database/database_api_base.py` | ✅ Existiert | Verwenden |
| `relational_postgresql.py` | `database/database_api_postgresql.py` | ✅ Existiert | Verwenden |
| `relational_sqlite.py` | `database/database_api_sqlite.py` | ✅ Existiert | Verwenden |
| **File Backend** | | | |
| `file_backend.py` | `database/database_api_file_storage.py` | ✅ Existiert | Verwenden |
| **LLM & RAG** | | | |
| `rag_pipeline.py` | ❌ Nicht vorhanden | ❌ Fehlt | **NEU erstellen** |
| `query_classifier.py` | Teilweise in `uds3_polyglot_query.py` | 🟡 Teilweise | Extrahieren + Erweitern |
| `retrieval_strategies.py` | Teilweise in `uds3_polyglot_query.py` | 🟡 Teilweise | Extrahieren + Erweitern |
| `context_assembler.py` | ❌ Nicht vorhanden | ❌ Fehlt | **NEU erstellen** |
| `prompt_templates.py` | ❌ Nicht vorhanden | ❌ Fehlt | **NEU erstellen** |
| `llm_ollama.py` | ❌ Nicht vorhanden | ❌ Fehlt | **NEU erstellen** |
| `llm_openai.py` | ❌ Nicht vorhanden | ❌ Fehlt | **NEU erstellen** |
| **Embeddings** | | | |
| `embeddings.py` | ❌ Nicht vorhanden | ❌ Fehlt | **NEU erstellen** (German BERT) |
| `embedding_cache.py` | ❌ Nicht vorhanden | ❌ Fehlt | **NEU erstellen** |
| **Schemas** | | | |
| `schema_process.py` | `uds3_database_schemas.py` | ✅ Existiert | Extrahieren |
| `schema_element.py` | `uds3_database_schemas.py` | ✅ Existiert | Extrahieren |
| `schema_connection.py` | `uds3_database_schemas.py` | ✅ Existiert | Extrahieren |
| **Utilities** | | | |
| `text_utils.py` | Verstreut in verschiedenen Modulen | 🟡 Teilweise | Konsolidieren |
| `validation.py` | Verstreut in verschiedenen Modulen | 🟡 Teilweise | Konsolidieren |
| `cli.py` | ❌ Nicht vorhanden | ❌ Fehlt | **NEU erstellen** |

---

## ✅ 3. Integration-Strategie: Schrittweise Refaktorisierung

### Phase 1: Analyse & Konsolidierung (Woche 1)

**Ziel:** Verstehe bestehende Struktur, keine Breaking Changes

**Aufgaben:**
- [x] Existierende UDS3-Struktur dokumentieren
- [ ] `database/database_manager.py` analysieren
- [ ] `uds3_polyglot_query.py` analysieren
- [ ] `uds3_database_schemas.py` analysieren
- [ ] Dependencies kartieren

**Output:**
- Detailliertes Mapping-Dokument (dieses Dokument)
- Liste aller zu migrierenden/neu erstellenden Module

### Phase 2: Neue Kern-Module (Woche 2-3)

**Ziel:** Erstelle fehlende LLM/RAG-Komponenten OHNE bestehenden Code zu brechen

**Neue Module (nicht in UDS3):**
1. **`embeddings.py`** - German BERT Embeddings
   - `sentence-transformers` Integration
   - deutsche-telekom/gbert-base
   - Caching Layer
   
2. **`embedding_cache.py`** - Embedding Cache
   - Memory + Disk Cache
   - SHA256 Hashing
   
3. **`rag_pipeline.py`** - Generic RAG Pipeline
   - Query Classification
   - Multi-DB Retrieval
   - Context Assembly
   - LLM Generation
   
4. **`llm_ollama.py`** - Ollama Client
   - REST API Client
   - Streaming Support
   
5. **`context_assembler.py`** - Context Builder
   - Token Management
   - Prompt Engineering

**Integration:**
- Nutze existierende `database_manager.py` als Datenbasis
- Kein Umbau von `database/` nötig
- Additive Änderungen only

### Phase 3: Fehlende DB-Adapter (Woche 4)

**Ziel:** Ergänze fehlende Adapter für Development

**Neue Adapter:**
1. **`vector_pgvector.py`** - pgvector Alternative zu ChromaDB
   - PostgreSQL Extension
   - SQL-basierte Vector Search
   
2. **`graph_networkx.py`** - NetworkX Fallback für Neo4j
   - In-Memory Graph
   - Development/Testing

**Implementierung:**
- Erbt von `database_api_base.py`
- Gleiche Interface wie existierende Adapter
- Unit Tests

### Phase 4: Flache Struktur (Optional, Woche 5-6)

**Ziel:** Refaktorisierung zu flacher Struktur (OPTIONAL!)

**Variante A: Graduelle Migration**
```python
# Alte Imports weiterhin unterstützen
from uds3.database.database_api_neo4j import Neo4jAdapter
# Neue flache Imports
from uds3.graph_neo4j import Neo4jAdapter  # symlink/alias
```

**Variante B: Status Quo beibehalten**
- `database/` Ordner bleibt
- Neue Module (RAG, Embeddings) kommen auf Root-Ebene
- Hybrid-Struktur:
  ```
  uds3/
  ├── database/       # Existing DB adapters (bleibt)
  ├── embeddings.py   # NEU: German BERT
  ├── rag_pipeline.py # NEU: RAG Framework
  ├── llm_ollama.py   # NEU: LLM Client
  └── ...
  ```

---

## 🎯 4. Empfehlung: Hybrid-Approach

### 4.1 Strategie

**NICHT refaktorisieren:** Existierende `database/` Struktur bleibt!

**Vorteile:**
- ✅ Keine Breaking Changes
- ✅ Bestehender Code funktioniert weiter
- ✅ Schnellere Implementierung
- ✅ Geringeres Risiko

**Neue Struktur:**
```
C:\VCC\uds3\
├── database/                    # ⭐ EXISTIERT - NICHT ANFASSEN
│   ├── database_api_*.py        # Alle DB-Adapter
│   ├── database_manager.py      # Orchestrator
│   └── ...
│
├── embeddings.py                # 🆕 NEU: German BERT Embeddings
├── embedding_cache.py           # 🆕 NEU: Caching Layer
├── rag_pipeline.py              # 🆕 NEU: Generic RAG
├── rag_retrieval.py             # 🆕 NEU: Retrieval Strategies
├── rag_context.py               # 🆕 NEU: Context Assembly
├── llm_ollama.py                # 🆕 NEU: Ollama Client
├── llm_openai.py                # 🆕 NEU: OpenAI Client (optional)
│
├── vector_pgvector.py           # 🆕 NEU: pgvector Adapter
├── graph_networkx.py            # 🆕 NEU: NetworkX Adapter
│
├── schema_process.py            # 🔄 REFACTOR: Aus uds3_database_schemas.py
├── schema_element.py            # 🔄 REFACTOR: Aus uds3_database_schemas.py
├── schema_connection.py         # 🔄 REFACTOR: Aus uds3_database_schemas.py
│
└── uds3_polyglot_manager.py     # 🔄 WRAPPER: Erweitert database_manager.py für RAG
```

### 4.2 Code-Beispiel: Integration

```python
# uds3_polyglot_manager.py (NEU - Wrapper um database_manager)
from uds3.database.database_manager import DatabaseManager
from uds3.embeddings import UDS3GermanEmbeddings
from uds3.rag_pipeline import UDS3GenericRAG

class UDS3PolyglotManager:
    """
    High-Level Polyglot Manager mit LLM-Integration
    
    Nutzt existierenden DatabaseManager + neue RAG-Komponenten
    """
    
    def __init__(self, config):
        # Nutze existierenden DatabaseManager
        self.db_manager = DatabaseManager(config)
        
        # NEU: Embeddings
        self.embeddings = UDS3GermanEmbeddings()
        
        # NEU: RAG Pipeline
        self.rag = UDS3GenericRAG(
            db_manager=self.db_manager,
            embeddings=self.embeddings
        )
    
    def save_process(self, process_data):
        """Speichert Prozess + generiert Embeddings"""
        # 1. Save via existierendem DatabaseManager
        process_id = self.db_manager.create_document(process_data)
        
        # 2. NEU: Embeddings generieren
        embedding = self.embeddings.embed_text(process_data["description"])
        
        # 3. NEU: Embedding speichern (via ChromaDB)
        self.db_manager.get_backend("chromadb").add_embedding(
            id=process_id,
            embedding=embedding,
            metadata={"process_id": process_id}
        )
        
        return process_id
    
    def semantic_search(self, query, top_k=10):
        """NEU: Semantic Search via RAG Pipeline"""
        return self.rag.search(query, top_k)
    
    def answer_query(self, query):
        """NEU: LLM-basierte Query-Antwort"""
        return self.rag.answer_query(query)
```

---

## 📋 5. Implementierungs-Checklist

### Woche 1: Analyse ✅
- [x] UDS3-Struktur kartieren
- [x] Mapping-Dokument erstellen
- [ ] `database_manager.py` Code-Review
- [ ] `uds3_polyglot_query.py` Code-Review

### Woche 2-3: Neue Module
- [ ] `embeddings.py` implementieren
- [ ] `embedding_cache.py` implementieren
- [ ] `rag_pipeline.py` implementieren
- [ ] `llm_ollama.py` implementieren
- [ ] `rag_context.py` implementieren
- [ ] Unit Tests für alle neuen Module

### Woche 4: Fehlende Adapter
- [ ] `vector_pgvector.py` implementieren
- [ ] `graph_networkx.py` implementieren
- [ ] Integration Tests

### Woche 5: Wrapper & Integration
- [ ] `uds3_polyglot_manager.py` (Wrapper)
- [ ] Integration mit bestehendem `DatabaseManager`
- [ ] End-to-End Tests
- [ ] Dokumentation aktualisieren

### Woche 6: VPB-Integration
- [ ] VPB Adapter für `UDS3PolyglotManager`
- [ ] Migration-Script: SQLite → UDS3
- [ ] VPB RAG Queries
- [ ] Performance-Tests

---

## 🔗 6. Nächste Schritte

**Sofort:**
1. ✅ Dieses Mapping-Dokument erstellen
2. [ ] `database_manager.py` analysieren (Code-Review)
3. [ ] `uds3_polyglot_query.py` analysieren
4. [ ] Entscheidung: Flat vs. Hybrid Structure

**Diese Woche:**
1. [ ] Erste neue Module implementieren (`embeddings.py`)
2. [ ] Unit Tests aufsetzen
3. [ ] CI/CD anpassen

---

**Status:** 🟡 In Progress - Mapping Complete, Implementation Pending

**Entscheidung benötigt:**
- [ ] Flat Structure vs. Hybrid Approach
- [ ] Breaking Changes erlaubt?
- [ ] Timeline für Refactoring

---

**Autor:** Integration Team  
**Letzte Aktualisierung:** 18. Oktober 2025
