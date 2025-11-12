# CHANGELOG — Kurzfassung (DE primär, EN sekundär)

## [1.1.0] - 2025-10-18 — Real Backend Integration
- Mock-Adapter ersetzt durch produktive Implementierungen: PostgreSQL, Neo4j, ChromaDB.
- UDS3 API Backend: Process Analysis & Health.
- Tests für Backend-Adapter ergänzt.
- Performance: Verbesserungen, erwartete Migration: 30–50 rec/s.

## [1.0.1] - 2025-10-18 — Hotfix
- Fix: ChromaDB Adapter API (add_embedding → add).
- Wechsel des Embedding-Modells zu sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2.
- Pre-Download Tool hinzugefügt.

## [1.0.0] - 2025-10-18 — UDS3 Complete
- Major: FastAPI REST API (11 Endpunkte), SAGA Pattern, Polyglot Persistence, Migration Tools.
- Tests: 20 API Integrationstests (alle bestanden).

## [0.3.0] — SPS Complete
- Einführung der 5 SPS-Elemente (COUNTER, CONDITION, ERROR_HANDLER, STATE, INTERLOCK).
- 40+ Unit-Tests, umfangreiche Dokumentation.

(Die vollständige Historie befindet sich in docs/CHANGELOG.md oder CHANGELOG.md im Repo.)
