# FAQ - Häufig gestellte Fragen

**Version:** 0.5.0

---

## General / Allgemein

### What is VPB? / Was ist VPB?

**EN:** VPB (Visual Process Builder) is a visual process designer for administrative processes with support for PLC-like elements (COUNTER, CONDITION, STATE, etc.) and UDS3 polyglot persistence backend.

**DE:** VPB (Visual Process Builder) ist ein visueller Prozess-Designer für Verwaltungsprozesse mit Unterstützung für SPS-ähnliche Elemente (COUNTER, CONDITION, STATE, etc.) und UDS3 Polyglot Persistence Backend.

---

### What is the current version? / Was ist die aktuelle Version?

**Current Version:** 0.5.0 (Alpha)

See **[[Changelog]]** for version history.

---

### Is VPB production-ready? / Ist VPB produktionsreif?

**EN:** VPB v0.5.0 is in **alpha status**. Core features are implemented and tested, but the system is still under active development.

**Recommended for:**
- ✅ Development and testing
- ✅ Proof of concept
- ✅ Internal evaluation

**Not recommended for:**
- ❌ Production deployments (yet)
- ❌ Critical business processes

---

## Installation / Installation

### What are the system requirements? / Was sind die Systemanforderungen?

**Minimum:**
- Python 3.8 or higher
- 4 GB RAM
- 2 GB disk space

**Recommended:**
- Python 3.10+
- 8 GB RAM
- 10 GB disk space (with backends)

**Operating Systems:**
- ✅ Windows 10/11
- ✅ macOS 11+
- ✅ Linux (Ubuntu 20.04+, Fedora, etc.)

---

### How do I install VPB? / Wie installiere ich VPB?

See **[[Getting-Started]]** for complete instructions.

**Quick Install:**
```bash
git clone https://github.com/makr-code/VCC-VPB.git
cd VCC-VPB
pip install -r requirements.txt
python vpb_app.py
```

---

### Can I use VPB without Docker? / Kann ich VPB ohne Docker verwenden?

**EN:** Yes! VPB Designer works standalone without any backend.

**Modes:**
1. **Standalone** (no Docker needed)
   - Local file storage (JSON)
   - All GUI features
   - Export functionality

2. **With UDS3 Backend** (Docker recommended)
   - PostgreSQL, Neo4j, ChromaDB
   - SAGA transactions
   - Semantic search

---

### Installation fails with "PyQt6 not found" / Installation schlägt fehl mit "PyQt6 not found"

**Solution:**

**Linux:**
```bash
sudo apt-get install python3-pyqt6
pip install PyQt6
```

**macOS:**
```bash
brew install pyqt@6
pip install PyQt6
```

**Windows:**
```bash
pip install --upgrade pip
pip install PyQt6
```

---

## Usage / Verwendung

### How do I create a new process? / Wie erstelle ich einen neuen Prozess?

1. Start VPB: `python vpb_app.py`
2. Menu: `File → New` or `Ctrl+N`
3. Add elements from palette (drag & drop)
4. Connect elements
5. Save: `File → Save` or `Ctrl+S`

See **[[User-Guide]]** for details.

---

### What are SPS elements? / Was sind SPS-Elemente?

**SPS** = Speicherprogrammierbare Steuerung (Programmable Logic Controller / PLC)

**Available Elements:**
- **COUNTER** - Counting events with limits
- **CONDITION** - Conditional branching
- **ERROR_HANDLER** - Error management
- **STATE** - State machines
- **INTERLOCK** - Safety locks

See **[[SPS-Elements]]** for detailed documentation.

---

### How do I export a process? / Wie exportiere ich einen Prozess?

**Supported Formats:**
- JSON (native)
- XML
- BPMN 2.0
- PNG (image)
- SVG (vector)
- PDF (document)

**Export:**
```
Menu: File → Export → [Format]
```

See **[[Export-Formats]]** for details.

---

### Can I search for processes semantically? / Kann ich semantisch nach Prozessen suchen?

**EN:** Yes, with UDS3 backend enabled!

**Requirements:**
- ChromaDB backend running
- Process indexed with embeddings

**API:**
```
GET /api/uds3/vpb/search?q=Baugenehmigung&top_k=5
```

See **[[API-Reference]]** for details.

---

## Technical / Technisch

### What databases does VPB use? / Welche Datenbanken verwendet VPB?

**UDS3 Polyglot Persistence:**

| Backend | Purpose | Technology |
|---------|---------|------------|
| **PostgreSQL** | Structured data | Relational DB |
| **Neo4j** | Process graphs | Graph DB |
| **ChromaDB** | Semantic search | Vector DB |

See **[[UDS3-Backend]]** for architecture.

---

### What is the SAGA pattern? / Was ist das SAGA-Pattern?

**EN:** SAGA is a pattern for distributed transactions across multiple databases.

**How it works:**
1. Begin transaction
2. Execute steps on each backend
3. If all succeed → Commit
4. If one fails → Rollback (compensation)

**Example:**
```
PostgreSQL ✅ → Neo4j ✅ → ChromaDB ❌
          ← Rollback ← Rollback
```

See **[[UDS3-Backend#SAGA-Pattern]]** for details.

---

### Can I extend VPB with custom elements? / Kann ich VPB mit eigenen Elementen erweitern?

**EN:** Yes! VPB supports custom elements.

**Steps:**
1. Create element class (inherit from `VPBElement`)
2. Define properties
3. Add validation rules
4. Register in palette

See **[[Extension-Development]]** (coming soon) or **[[Development-Guide]]**.

---

### How do I access the API? / Wie greife ich auf die API zu?

**Start API Server:**
```bash
uvicorn api.uds3_vpb_fastapi:app --reload
```

**Access:**
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

See **[[API-Reference]]** for complete documentation.

---

## Integration / Integration

### What is Covina? / Was ist Covina?

**Covina** = Compliance + Organization + Intelligence + Analysis

**Purpose:**  
Central system for process and organizational modeling with gap detection and process mining.

**Integration:**
- VPB exports processes to Covina
- Covina performs gap detection
- Results fed back to VPB

See **[[System-Integration#Covina]]** for details.

---

### What is VERITAS? / Was ist VERITAS?

**VERITAS** = Verification + Integrity + Tracking + Audit + Security

**Purpose:**  
Compliance engine and governance framework

**Features:**
- License validation
- Module protection
- Audit logging
- Access control

See **[[System-Integration#VERITAS]]** for details.

---

### What is UDS3? / Was ist UDS3?

**UDS3** = Unified Data Services 3

**Purpose:**  
Polyglot persistence layer with SAGA pattern for distributed transactions

**Backends:**
- PostgreSQL (relational)
- Neo4j (graph)
- ChromaDB (vector)

See **[[UDS3-Backend]]** for complete documentation.

---

### Can VPB integrate with my existing systems? / Kann VPB in meine bestehenden Systeme integriert werden?

**EN:** Yes, through multiple integration points:

1. **REST API** - Standard HTTP/JSON API
2. **Export Formats** - JSON, XML, BPMN
3. **Database** - Direct PostgreSQL/Neo4j access
4. **Covina** - Process ingestion API

See **[[System-Integration]]** and **[[API-Reference]]**.

---

## Troubleshooting / Fehlerbehebung

### VPB won't start / VPB startet nicht

**Check:**
1. Python version: `python --version` (≥ 3.8)
2. Dependencies: `pip install -r requirements.txt`
3. Permissions: Can you write to current directory?

**Debug:**
```bash
python vpb_app.py --debug
```

See **[[Troubleshooting]]** for more solutions.

---

### Database connection failed / Datenbankverbindung fehlgeschlagen

**Check Docker:**
```bash
docker-compose ps
docker-compose logs postgres
docker-compose logs neo4j
docker-compose logs chromadb
```

**Restart:**
```bash
docker-compose restart
```

**Check Health:**
```
GET /api/uds3/vpb/health
```

---

### API returns 500 error / API gibt 500-Fehler zurück

**Common Causes:**
1. Backend database not running
2. SAGA transaction failed
3. Invalid input data

**Check Transaction:**
```
GET /api/uds3/saga/transactions/{transaction_id}
```

**Check Logs:**
```bash
uvicorn api.uds3_vpb_fastapi:app --log-level debug
```

---

### Process won't validate / Prozess validiert nicht

**Common Issues:**
- Missing connections
- Invalid property values
- Dead-end elements
- Circular dependencies

**Run Validation:**
```
Process → Validate (F5)
```

**Check Errors:**
- Red indicators on elements
- Error messages in status bar
- Validation panel (if open)

---

## Development / Entwicklung

### How can I contribute? / Wie kann ich beitragen?

See **[[Contributing]]** for complete guidelines.

**Quick Start:**
1. Fork repository
2. Create feature branch
3. Make changes
4. Write tests
5. Submit PR

---

### Where can I report bugs? / Wo kann ich Fehler melden?

**GitHub Issues:** https://github.com/makr-code/VCC-VPB/issues

**Include:**
- VPB version
- Operating system
- Steps to reproduce
- Error messages
- Screenshots (if applicable)

---

### How do I run tests? / Wie führe ich Tests aus?

```bash
# All tests
pytest

# With coverage
pytest --cov=vpb

# Specific test
pytest tests/test_element.py -v
```

See **[[Development-Guide#Testing]]** for details.

---

### What code style should I follow? / Welchen Code-Stil soll ich befolgen?

**Python:**
- PEP 8
- Type hints
- Docstrings
- Max line length: 120

**Tools:**
```bash
flake8 vpb/ --max-line-length=120
black vpb/
mypy vpb/
```

See **[[Development-Guide]]** for complete guidelines.

---

## Performance / Leistung

### VPB is slow / VPB ist langsam

**Optimization Tips:**
1. Enable caching (config)
2. Reduce canvas elements
3. Use batch operations
4. Close unnecessary panels

**Check Performance:**
- Task Manager / Activity Monitor
- Backend response times
- Log analysis

---

### Semantic search is slow / Semantische Suche ist langsam

**Causes:**
- Large number of indexed processes
- First query (model loading)
- Network latency (remote ChromaDB)

**Solutions:**
- Use local ChromaDB
- Increase ChromaDB resources
- Reduce `top_k` parameter

---

## Licensing / Lizenzierung

### What license does VPB use? / Welche Lizenz verwendet VPB?

**Check:** LICENSE file in repository

**VERITAS Protected Modules:**
- Some modules protected by VERITAS Tech GmbH
- See module headers for details

---

### Can I use VPB commercially? / Kann ich VPB kommerziell nutzen?

**Check:** LICENSE file for terms

**For protected modules:**
- Contact: VERITAS Tech GmbH

---

## Support / Unterstützung

### Where can I get help? / Wo bekomme ich Hilfe?

**Resources:**
- **[[Home]]** - Start here
- **[[User-Guide]]** - Complete manual
- **[[Troubleshooting]]** - Common issues
- **GitHub Issues** - Bug reports
- **GitHub Discussions** - Community (coming soon)

---

### How do I request a feature? / Wie fordere ich ein Feature an?

1. Check **[[Roadmap]]** (planned features)
2. Search existing issues
3. Create new issue: "Feature Request"
4. Describe use case
5. Wait for feedback

---

### Is there commercial support available? / Gibt es kommerziellen Support?

**Contact:**
- Repository owner: makr-code
- VERITAS Tech GmbH (for protected modules)

---

## Related Documentation

- **[[Home]]** - Main page
- **[[Getting-Started]]** - Installation
- **[[User-Guide]]** - User manual
- **[[Development-Guide]]** - Developer docs
- **[[Troubleshooting]]** - Problem solving
- **[[Changelog]]** - Version history

---

**Still have questions?**  
Create an issue: https://github.com/makr-code/VCC-VPB/issues

[[Home]] | [[Troubleshooting]] | [[Support]]
