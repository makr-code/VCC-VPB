# VPB Visual Process Designer — Dokumentation (DE primär, EN sekundär)

Version: 1.1.0 "Real Backend Integration" (Stand: 2025-10-18)

Kurzbeschreibung (DE):
- VPB ist ein visueller Prozess-Designer für Verwaltungsprozesse mit Unterstützung für SPS-Elemente (COUNTER, CONDITION, ERROR_HANDLER, STATE, INTERLOCK) und einer UDS3-kompatiblen Backend-Integration (PostgreSQL, Neo4j, ChromaDB).
- Dieses Repository enthält: Designer-GUI, FastAPI UDS3 REST API mit SAGA Pattern, Migrationstools (SQLite → UDS3), Auto-Fix Engine und Tests.

Kurzbeschreibung (EN):
- VPB is a visual process designer for administrative processes supporting SPS elements and a UDS3-compatible backend integration (PostgreSQL, Neo4j, ChromaDB).
- This repository contains: Designer GUI, FastAPI UDS3 REST API with SAGA pattern, migration tools (SQLite → UDS3), Auto-Fix engine and tests.

Schnellstart (DE):
1. Repository klonen:
   git clone https://github.com/makr-code/VCC-VPB.git
   cd VCC-VPB

2. Abhängigkeiten installieren:
   pip install -r requirements.txt

3. Optionen:
   - Designer GUI starten:
     python vpb_app.py
   - API Server (Entwicklung / Mock):
     uvicorn api.uds3_vpb_fastapi:app --reload
     OpenAPI: http://localhost:8000/api/docs

Quickstart (EN):
1. Clone repository:
   git clone https://github.com/makr-code/VCC-VPB.git
   cd VCC-VPB

2. Install dependencies:
   pip install -r requirements.txt

3. Options:
   - Start Designer GUI:
     python vpb_app.py
   - Start API Server (dev/mock):
     uvicorn api.uds3_vpb_fastapi:app --reload
     OpenAPI: http://localhost:8000/api/docs

Wichtige Links im Repo:
- docs/DOCUMENTATION_SUMMARY.md — Konsolidierte Projektdokumentation (DE/EN)
- docs/CHANGELOG_SUMMARY.md — Kurzfassung des Changelogs (DE/EN)
- processes/ — Beispiele & Showcases
- palettes/README.md — Paletten-Format
- CONTRIBUTING.md — Beitragshinweise
- tests/ — Test-Suites

Wenn gewünscht, kann ich weitere Dateien hinzufügen oder diese README anpassen.
