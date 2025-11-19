# Development Guide / Entwicklungshandbuch

**Version:** 0.5.0  
**Target:** Developers / Entwickler

---

## Overview / Übersicht

Dieser Leitfaden hilft Entwicklern, die VPB-Entwicklungsumgebung einzurichten und zum Projekt beizutragen.

This guide helps developers set up the VPB development environment and contribute to the project.

---

## Prerequisites / Voraussetzungen

### Required / Erforderlich

- **Python** 3.8 oder höher
- **pip** (Python Package Manager)
- **Git**
- **Code Editor** (VS Code, PyCharm, etc.)

### Optional (for UDS3 Backend)

- **Docker** & Docker Compose
- **PostgreSQL** 14+
- **Neo4j** 5.0+
- **ChromaDB** 0.4+

---

## Setup / Einrichtung

### 1. Clone Repository

```bash
git clone https://github.com/makr-code/VCC-VPB.git
cd VCC-VPB
```

### 2. Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Upgrade pip if needed
pip install --upgrade pip
```

**Main Dependencies:**
- **PyQt6** - GUI framework
- **FastAPI** - REST API
- **uvicorn** - ASGI server
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **pytest** - Testing framework

### 4. Verify Installation

```bash
# Check Python version
python --version  # Should be 3.8+

# Test imports
python -c "import PyQt6; print('PyQt6 OK')"
python -c "import fastapi; print('FastAPI OK')"
```

---

## Project Structure / Projektstruktur

```
VCC-VPB/
├── vpb/                      # Main application package
│   ├── models/               # Data models
│   │   ├── document.py       # DocumentModel
│   │   ├── element.py        # VPBElement
│   │   ├── connection.py     # VPBConnection
│   │   └── palette.py        # PaletteModel
│   │
│   ├── services/             # Business logic
│   │   ├── document_service.py
│   │   ├── validation_service.py
│   │   ├── export_service.py
│   │   ├── layout_service.py
│   │   ├── ai_service.py
│   │   ├── autosave_service.py
│   │   ├── backup_service.py
│   │   ├── code_sync_service.py
│   │   └── recent_files_service.py
│   │
│   ├── controllers/          # Application controllers
│   │   ├── document_controller.py
│   │   ├── element_controller.py
│   │   ├── connection_controller.py
│   │   ├── layout_controller.py
│   │   ├── validation_controller.py
│   │   ├── ai_controller.py
│   │   ├── export_controller.py
│   │   └── background_task_controller.py
│   │
│   ├── views/                # Views (PyQt6)
│   │   ├── main_window.py
│   │   ├── menu_bar.py
│   │   ├── toolbar.py
│   │   ├── status_bar.py
│   │   ├── canvas_view.py
│   │   ├── palette_view.py
│   │   └── properties_view.py
│   │
│   ├── ui/                   # UI components
│   │   ├── canvas.py
│   │   ├── palette_panel.py
│   │   ├── properties_panel.py
│   │   ├── chat_panel.py
│   │   ├── migration_dialog.py
│   │   └── ...
│   │
│   └── infrastructure/       # Infrastructure
│       ├── event_bus.py
│       ├── settings_manager.py
│       └── user_profile_manager.py
│
├── api/                      # REST API
│   ├── uds3_vpb_fastapi.py   # FastAPI application
│   └── uds3_vpb_endpoints.py # Endpoint implementations
│
├── core/                     # Core components
│   ├── polyglot_manager.py   # UDS3 Polyglot Manager
│   └── message_bus.py        # Message bus
│
├── migration/                # Migration tools
│   ├── migration_tool.py
│   ├── auto_fix.py
│   ├── validation.py
│   └── gap_detector.py
│
├── tests/                    # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                     # Documentation
├── processes/                # Example processes
├── palettes/                 # Element palettes
│
├── vpb_app.py                # Main application entry
├── requirements.txt          # Dependencies
└── pytest.ini                # Test configuration
```

---

## Running the Application / Anwendung ausführen

### Desktop GUI

```bash
# Start VPB Designer
python vpb_app.py
```

### API Server

```bash
# Development (with auto-reload)
uvicorn api.uds3_vpb_fastapi:app --reload

# Production
uvicorn api.uds3_vpb_fastapi:app --host 0.0.0.0 --port 8000
```

**Access API Docs:**
- http://localhost:8000/api/docs (Swagger UI)
- http://localhost:8000/api/redoc (ReDoc)

---

## Development Workflow / Entwicklungs-Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-new-feature
```

### 2. Make Changes

**Code Style:**
- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions small and focused

**Example:**
```python
def process_element(element: VPBElement) -> Dict[str, Any]:
    """
    Process a VPB element and return result.
    
    Args:
        element: The VPB element to process
        
    Returns:
        Dictionary with processing result
        
    Raises:
        ValueError: If element is invalid
    """
    if not element.is_valid():
        raise ValueError(f"Invalid element: {element.id}")
    
    return {
        "id": element.id,
        "type": element.type,
        "processed": True
    }
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_element.py

# Run with coverage
pytest --cov=vpb --cov-report=html

# Run specific test
pytest tests/test_element.py::test_element_creation -v
```

### 4. Run Linters

```bash
# Check code style (if flake8 installed)
flake8 vpb/ --max-line-length=120

# Type checking (if mypy installed)
mypy vpb/

# Format code (if black installed)
black vpb/
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: Add new feature X"

# Commit message format:
# feat: New feature
# fix: Bug fix
# docs: Documentation
# test: Tests
# refactor: Code refactoring
# style: Code style
```

### 6. Push and Create PR

```bash
git push origin feature/my-new-feature
```

Then create Pull Request on GitHub.

---

## Testing / Testen

### Test Structure

```
tests/
├── unit/                    # Unit tests (isolated)
│   ├── test_models.py
│   ├── test_services.py
│   └── test_controllers.py
│
├── integration/             # Integration tests
│   ├── test_api.py
│   ├── test_uds3.py
│   └── test_migration.py
│
├── e2e/                     # End-to-end tests
│   └── test_workflow.py
│
└── fixtures/                # Test data
    ├── sample_process.json
    └── test_palette.json
```

### Writing Tests

**Unit Test Example:**
```python
import pytest
from vpb.models.element import VPBElement

def test_element_creation():
    """Test creating a VPB element"""
    element = VPBElement(
        id="test1",
        type="COUNTER",
        name="Test Counter"
    )
    
    assert element.id == "test1"
    assert element.type == "COUNTER"
    assert element.name == "Test Counter"

def test_element_validation():
    """Test element validation"""
    element = VPBElement(id="test1", type="COUNTER")
    
    # Missing required properties
    assert not element.is_valid()
    
    # Add required properties
    element.set_property("initial_value", 0)
    element.set_property("max", 100)
    
    assert element.is_valid()
```

**Integration Test Example:**
```python
import pytest
from api.uds3_vpb_fastapi import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_create_process():
    """Test process creation via API"""
    response = client.post("/api/uds3/vpb/processes", json={
        "name": "Test Process",
        "description": "Test",
        "status": "draft",
        "process_data": {}
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "process_id" in data
```

### Running Tests

```bash
# All tests
pytest

# Specific category
pytest tests/unit/
pytest tests/integration/

# Verbose output
pytest -v

# With coverage
pytest --cov=vpb

# Stop on first failure
pytest -x

# Run in parallel (if pytest-xdist installed)
pytest -n auto
```

---

## Debugging / Fehlersuche

### VS Code Configuration

**`.vscode/launch.json`:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "VPB App",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/vpb_app.py",
            "console": "integratedTerminal"
        },
        {
            "name": "API Server",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "api.uds3_vpb_fastapi:app",
                "--reload"
            ],
            "console": "integratedTerminal"
        },
        {
            "name": "Pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["-v"],
            "console": "integratedTerminal"
        }
    ]
}
```

### Logging

**Enable Debug Logging:**
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

**Log Levels:**
- DEBUG: Detailed information
- INFO: General information
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

---

## UDS3 Backend Development

### Local Backend Setup (Docker)

**`docker-compose.yml`:**
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: uds3
      POSTGRES_USER: vpb_user
      POSTGRES_PASSWORD: secret
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  neo4j:
    image: neo4j:5.0
    environment:
      NEO4J_AUTH: neo4j/secret
    ports:
      - "7687:7687"
      - "7474:7474"
    volumes:
      - neo4j_data:/data
  
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma

volumes:
  postgres_data:
  neo4j_data:
  chroma_data:
```

**Start Backends:**
```bash
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Database Migrations

**PostgreSQL:**
```bash
# Create migration
alembic revision -m "Add new table"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Code Review Checklist

Before submitting PR:

- [ ] Code follows PEP 8 style guide
- [ ] All tests pass (`pytest`)
- [ ] New code has tests (coverage ≥ 80%)
- [ ] Type hints added
- [ ] Docstrings added/updated
- [ ] No commented-out code
- [ ] No debug print statements
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts

---

## Performance Guidelines

### Optimization Tips

**1. Lazy Loading:**
```python
# ✅ Good - load on demand
def get_process(self, process_id):
    if process_id not in self._cache:
        self._cache[process_id] = self._load_process(process_id)
    return self._cache[process_id]
```

**2. Batch Operations:**
```python
# ❌ Bad - individual saves
for element in elements:
    service.save_element(element)

# ✅ Good - batch save
service.save_elements_batch(elements)
```

**3. Async Operations:**
```python
# ✅ Good - non-blocking
async def save_process_async(self, process):
    await asyncio.sleep(0)  # Yield control
    return self._save_process(process)
```

---

## Troubleshooting / Problemlösung

### Common Issues

**1. PyQt6 Import Error:**
```bash
# Linux fix
sudo apt-get install python3-pyqt6

# macOS fix
brew install pyqt@6

# Windows: Reinstall
pip uninstall PyQt6
pip install PyQt6
```

**2. Database Connection Failed:**
```bash
# Check Docker containers
docker-compose ps

# Restart containers
docker-compose restart

# Check logs
docker-compose logs postgres
```

**3. Tests Failing:**
```bash
# Clear pytest cache
pytest --cache-clear

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## Contributing

See **[[Contributing]]** for detailed contribution guidelines.

**Quick Links:**
- Issue Tracker: https://github.com/makr-code/VCC-VPB/issues
- Pull Requests: https://github.com/makr-code/VCC-VPB/pulls
- Discussions: GitHub Discussions (coming soon)

---

## Resources / Ressourcen

### Documentation

- **[[Architecture]]** - System architecture
- **[[API-Reference]]** - REST API
- **[[UDS3-Backend]]** - Backend details
- **[[Testing]]** - Testing guide (coming soon)

### External Links

- **Python:** https://www.python.org/
- **PyQt6:** https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **FastAPI:** https://fastapi.tiangolo.com/
- **pytest:** https://docs.pytest.org/

---

[[Home]] | [[Architecture]] | [[Contributing]]
