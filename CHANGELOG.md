# Changelog / Änderungsprotokoll

**Version:** Current - 0.5.0  
**Format:** [Keep a Changelog](https://keepachangelog.com/)  
**Versioning:** [Semantic Versioning](https://semver.org/)

---

## Overview / Übersicht

Dieses Dokument protokolliert alle wichtigen Änderungen am VPB Process Designer.

This document tracks all notable changes to the VPB Process Designer.

---

## [0.5.0] - 2025-11-19

### 🎯 Major Release: Documentation Consolidation

**Status:** ✅ Current Release  
**Focus:** GitHub Wiki Structure & System Integration

#### Added / Hinzugefügt

**Wiki Documentation Structure:**
- ✅ GitHub Wiki-compatible documentation format
- ✅ Home.md - Main landing page (bilingual DE/EN)
- ✅ _Sidebar.md - Navigation sidebar
- ✅ _Footer.md - Common footer
- ✅ Getting-Started.md - Installation and first steps
- ✅ User-Guide.md - Complete user manual
- ✅ SPS-Elements.md - SPS elements overview
- ✅ Architecture.md - System architecture documentation
- ✅ UDS3-Backend.md - Polyglot persistence details
- ✅ System-Integration.md - Covina, VERITAS, Themis, Clara integration
- ✅ API-Reference.md - Complete REST API documentation (10 endpoints)
- ✅ Development-Guide.md - Developer setup and workflow

**System Integration Documentation:**
- ✅ Covina integration strategy (UPS - Unified Process Schema)
- ✅ VERITAS compliance engine documentation
- ✅ UDS3 Polyglot Persistence (PostgreSQL, Neo4j, ChromaDB)
- ✅ SAGA Pattern for distributed transactions
- ✅ Themis (legal references) - planned integration
- ✅ Clara (AI assistant) - current integration

**Version Management:**
- ✅ VERSION file updated to 0.5.0
- ✅ Standardized version across all documentation

#### Documentation Verified Against Source Code

**Confirmed Components:**
- ✅ Controllers (8 files): document, element, connection, validation, export, ai, layout, background_task
- ✅ Services (9 files): document, validation, export, layout, ai, autosave, backup, code_sync, recent_files
- ✅ Models (4 files): document, element, connection, palette
- ✅ UI Components: Multiple files in vpb/ui/
- ✅ Views: Files in vpb/views/
- ✅ API: FastAPI REST API with 10 endpoints
- ✅ Core: Polyglot Manager (1329 lines), Message Bus

**API Endpoints Documented:**
- GET `/api/uds3/vpb/processes` - List processes
- POST `/api/uds3/vpb/processes` - Create process
- GET `/api/uds3/vpb/processes/{id}` - Get process
- PUT `/api/uds3/vpb/processes/{id}` - Update process
- DELETE `/api/uds3/vpb/processes/{id}` - Delete process
- GET `/api/uds3/vpb/search` - Semantic search
- GET `/api/uds3/vpb/health` - Health check
- GET `/api/uds3/saga/transactions` - List transactions
- GET `/api/uds3/saga/transactions/{id}` - Get transaction status
- GET `/` - API info

#### Changed / Geändert

**Documentation Structure:**
- Consolidated scattered documentation (160+ files)
- Organized into logical wiki sections
- Bilingual support (DE/EN) throughout
- Clear navigation structure

**Version Information:**
- Updated from multiple conflicting versions (v0.2.0-alpha, v1.0.0, v1.1.0)
- Standardized to v0.5.0

---

## [1.1.0] - 2025-10-18

### 🚀 Real Backend Integration

**Status:** Previous Release

#### Added

**Backend Implementations:**
- ✅ PostgreSQL adapter (production)
- ✅ Neo4j adapter (production)
- ✅ ChromaDB adapter (production)
- ✅ UDS3 API Backend module
- ✅ Connection pooling
- ✅ Session management

**Features:**
- ThreadedConnectionPool for PostgreSQL
- GraphDatabase driver for Neo4j
- Sentence-transformers embeddings for ChromaDB
- Process complexity analysis
- Quality metrics
- Semantic search

#### Changed

- Replaced mock backends with production implementations
- Improved error handling
- Added retry logic
- Enhanced performance

#### Technical Details

**Dependencies:**
- `psycopg2-binary>=2.9.9`
- `neo4j>=5.15.0,<6.0.0`
- `chromadb>=0.4.22`
- `sentence-transformers>=2.2.2`

**Graph Model:**
- Nodes: Process, Element
- Relationships: HAS_ELEMENT, CONNECTED_TO

**Embedding Model:**
- paraphrase-multilingual-MiniLM-L12-v2
- 384 dimensions
- 471 MB model size

---

## [1.0.0] - 2025-10-17

### 🎉 Major Release: UDS3 Complete

**Status:** Previous Major Release

#### Added

**UDS3 Polyglot Manager:**
- SAGA Pattern implementation
- Multi-backend coordination
- Transaction state management
- Rollback support

**Backend Adapters:**
- PostgreSQL adapter (initial)
- Neo4j adapter (initial)
- ChromaDB adapter (initial)

**API Layer:**
- FastAPI REST API
- OpenAPI/Swagger documentation
- Pydantic models
- CORS support

#### Features

- Complete CRUD operations
- Distributed transactions
- Health monitoring
- Error handling

---

## [0.2.0-alpha] - 2025-10-14

### Alpha Release

**Status:** Alpha Testing

#### Added

**Core Features:**
- Visual process designer
- SPS element support
- Basic export functionality
- SQLite persistence

**SPS Elements:**
- COUNTER
- CONDITION
- ERROR_HANDLER
- STATE
- INTERLOCK

**UI Components:**
- Canvas view
- Palette panel
- Properties panel
- Menu bar
- Toolbar

---

## [0.1.0] - 2025-10-01

### Initial Release

**Status:** Initial Development

#### Added

**Foundation:**
- Basic project structure
- PyQt6 GUI framework
- Element models
- Connection system

**Features:**
- Create/edit/delete elements
- Create connections
- Save/load processes (JSON)
- Basic validation

---

## Version History Summary / Versionshistorie-Übersicht

| Version | Date | Focus |
|---------|------|-------|
| **0.5.0** | 2025-11-19 | Documentation consolidation, Wiki structure |
| 1.1.0 | 2025-10-18 | Real backend integration |
| 1.0.0 | 2025-10-17 | UDS3 complete, SAGA pattern |
| 0.2.0-alpha | 2025-10-14 | Alpha release, SPS elements |
| 0.1.0 | 2025-10-01 | Initial release |

---

## Upcoming / Geplant

### v0.6.0 (Planned)

**Focus:** Migration Tools & Gap Detection

**Planned Features:**
- Enhanced migration UI
- Automated gap detection
- Process mining features
- Conformance checking

**Integrations:**
- Improved Covina integration
- Themis legal references
- Enhanced Clara AI features

---

## Migration Notes / Migrationhinweise

### From v1.1.0 to v0.5.0

**Version Numbering:**
- Corrected version to reflect alpha status
- v0.5.0 represents current development state

**No Breaking Changes:**
- All v1.1.0 features remain functional
- Documentation reorganized, not functionality

### From v0.2.0-alpha to v0.5.0

**Added:**
- UDS3 backend integration
- REST API
- SAGA transactions
- Comprehensive documentation

**Breaking Changes:**
- Backend storage format changed
- Migration tool available: `migration/migration_tool.py`

---

## Deprecated Features / Veraltete Funktionen

### v0.5.0

**Deprecated:**
- None currently

**Planned Deprecation:**
- SQLite-only mode (future)
- Mock backends (already replaced in v1.1.0)

---

## Security Updates / Sicherheitsupdates

### v0.5.0

**Security:**
- VERITAS compliance engine integration
- Audit logging improvements
- API access control (planned)

### v1.1.0

**Security:**
- Real database connections (no mocks)
- Connection pooling
- Error handling improvements

---

## Performance Improvements / Leistungsverbesserungen

### v0.5.0

**Documentation:**
- Better organized documentation
- Faster navigation
- Clear examples

### v1.1.0

**Backend:**
- Connection pooling (PostgreSQL)
- Session management (Neo4j)
- Batch operations support

**Semantic Search:**
- Multilingual embeddings
- 384-dim vectors
- Efficient similarity search

---

## Contributors / Mitwirkende

- VPB Development Team
- UDS3 Development Team
- VERITAS Tech GmbH

---

## Related Documentation

- **[[Home]]** - Main documentation
- **[[Architecture]]** - System architecture
- **[[API-Reference]]** - API changes
- **[[Development-Guide]]** - Development workflow

---

## External Links

- **GitHub Repository:** https://github.com/makr-code/VCC-VPB
- **Issue Tracker:** https://github.com/makr-code/VCC-VPB/issues
- **Keep a Changelog:** https://keepachangelog.com/
- **Semantic Versioning:** https://semver.org/

---

[[Home]] | [[Roadmap]]
