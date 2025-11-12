# VPB — Konsolidierte Projektdokumentation (DE primär, EN sekundär)

Inhalt
- Übersicht & Ziele
- Architektur & Komponenten
- UDS3 REST API (Endpunkte & Beispiele)
- Polyglot Backends (PostgreSQL, Neo4j, ChromaDB)
- Migrationstools & Auto-Fix
- SPS-Elemente (Kurzreferenz)
- Installation & Konfiguration
- Tests & CI
- Performance & Known Issues
- Contribution

1. Übersicht & Ziele (DE)
VPB (Visual Process Designer) ist ein Tool zum grafischen Entwurf, zur Migration und zum Management von Verwaltungsprozessen. Ziel: Produktionstaugliche Speicherung, semantische Suche und robuste Migration in ein UDS3-Backend.

1. Overview & Goals (EN)
VPB is a tool for visual design, migration and management of administrative processes. Goal: production-ready storage, semantic search and robust migration into a UDS3 backend.

2. Architektur & Hauptkomponenten (DE)
- Designer GUI: vpb_app.py, vpb/* — Diagramm-Editor, Export (PDF/PNG/SVG), Paletten und Beispiele.
- API Server: api/uds3_vpb_fastapi.py — FastAPI mit 11 Endpunkten, OpenAPI.
- Polyglot Manager: core/polyglot_manager.py — SAGA Orchestrator & Backend Adapters.
- Migration: migration/*, vpb/ui/migration_dialog.py — SQLite → UDS3 Migration, Auto-Fix Engine.
- Tests: tests/* — Integration, Auto-Fix, Performance.

2. Architecture & Components (EN)
- Designer GUI: visual editor, exports, palettes and examples.
- API Server: FastAPI application with OpenAPI.
- Polyglot Manager: SAGA orchestrator and adapters for Postgres/Neo4j/ChromaDB.
- Migration: tools and UI for migrating from SQLite to UDS3, including Auto-Fix.
- Tests: suites for API, auto-fix and performance.

3. UDS3 REST API — Kurzreferenz (DE)
Wesentliche Endpunkte:
- POST /api/uds3/vpb/processes — Create process (SAGA)
- GET /api/uds3/vpb/processes — List (Filter: domain, date, limit)
- GET /api/uds3/vpb/processes/{id} — Read
- PUT /api/uds3/vpb/processes/{id} — Update (SAGA)
- DELETE /api/uds3/vpb/processes/{id} — Delete (soft/hard)
- GET /api/uds3/vpb/search — Semantic search (query required)
- GET /api/uds3/vpb/health — Backend health
- GET /api/uds3/saga/transactions — List transactions
- GET /api/uds3/saga/transactions/{id} — Transaction status

3. UDS3 REST API — Short reference (EN)
See same endpoints listed above; OpenAPI docs available at /api/docs when server runs.

4. Polyglot Backends (DE)
- PostgreSQL: Relational storage, JSONB, transactions, pooling (psycopg2).
- Neo4j: Graph storage for elements & connections.
- ChromaDB: Vector store for embeddings (sentence-transformers).

4. Polyglot Backends (EN)
Same as above.

5. Migration & Auto-Fix (DE)
- Migration-UI: 3 Tabs (Config, Progress, Results). Menü: Tools → Migration.
- CLI: python -m migration.migration_tool --source sqlite:///data/vpb.db --batch-size 100 --validate
- Auto-Fix-Strategien: COPY_FROM_SOURCE, DELETE_FROM_TARGET, UPDATE_TARGET, MERGE_DATA, SKIP
- Reports: JSON with migration_id, summary, gaps, validation results.

5. Migration & Auto-Fix (EN)
Same as above.

6. SPS-Elemente (Kurzreferenz) (DE)
- COUNTER: Schleifen-/Batchsteuerung.
- CONDITION: Bedingte Verzweigung.
- ERROR_HANDLER: Retry- und Fehlerwege.
- STATE: Zustandsautomat (Transitions).
- INTERLOCK: Ressourcensteuerung (MUTEX/SEMAPHORE).

6. SPS Elements (EN)
Same as above.

7. Installation & Konfiguration (DE)
Voraussetzungen: Python 3.10+ (3.13 empfohlen), optional PostgreSQL, Neo4j, Ghostscript. ChromaDB kann lokal initialisiert werden.
Umgebungsvariablen:
- UDS3_POSTGRES_HOST, UDS3_POSTGRES_PORT, UDS3_POSTGRES_USER, UDS3_POSTGRES_PASSWORD, UDS3_POSTGRES_DB
- UDS3_NEO4J_URI, UDS3_NEO4J_USER, UDS3_NEO4J_PASSWORD
- UDS3_CHROMADB_PATH

7. Installation & Configuration (EN)
Same as above.

8. Tests & CI (DE)
- API Integration: pytest tests/test_uds3_fastapi.py
- Auto-Fix: pytest tests/test_auto_fix.py
- Performance: pytest tests/test_migration_performance.py

8. Tests & CI (EN)
Same as above.

9. Performance & Known Issues (DE)
- Erwartete Migration: 30–50 rec/s nach Fixes.
- Neo4j: Kompatibilität mit neo4j<6.0 empfohlen.
- Dev-Modus: Backends können deaktiviert werden (use_mock).

9. Performance & Known Issues (EN)
Same as above.

10. Contribution (DE)
Siehe CONTRIBUTING.md — Tests, Dokumentation und Conventional Commits erwünscht.

10. Contribution (EN)
See CONTRIBUTING.md — tests, docs and Conventional Commits expected.
