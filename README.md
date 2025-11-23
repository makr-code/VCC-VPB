# VPB Visual Process Designer

**Version:** 1.1.0 "Real Backend Integration"  
**Status:** 🚀 Production Ready  
**Last Updated:** 2025-11-17

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

## 📚 Documentation

### Strategic Planning
- **[Weiterentwicklungsstrategie](WEITERENTWICKLUNGSSTRATEGIE.md)** — 2025-2027 evolution strategy for VCC-VPB
- **[Roadmap](ROADMAP.md)** — Product roadmap and release planning
- **[System Integration](System-Integration.md)** — VCC ecosystem integration (Covina, VERITAS, Clara, Themis)
- **[Architecture](Architecture.md)** — System architecture and design patterns

### Quick Links
- **[API Reference](docs/api/UDS3_API_REFERENCE.md)** — REST API documentation (10 endpoints)
- **[Development Guide](DEVELOPMENT.md)** — Developer setup and workflow
- **[Documentation Summary](docs/DOCUMENTATION_SUMMARY.md)** — Consolidated project documentation
- **[Changelog](CHANGELOG.md)** — Complete change history
- **[Contributing](CONTRIBUTING.md)** — Contribution guidelines

### Project Documentation
- **[Gap Analysis](DOCUMENTATION_GAP_ANALYSIS.md)** — Documentation status and gaps
- **[Project Guide](DOCUMENTATION_PROJECT_GUIDE.md)** — Navigation guide for all documentation
- **[SPS Elements Status](SPS_IMPLEMENTATION_STATUS.md)** — SPS elements verification

### Examples & Tests
- `processes/` — Example processes and showcases
- `palettes/README.md` — Palette format documentation
- `tests/` — Comprehensive test suites

---

**Version:** 1.1.0  
**Single Source of Truth:** See `VERSION` file in repository root
