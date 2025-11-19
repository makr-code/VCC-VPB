# Architecture / Architektur

**Version:** 0.5.0  
**Target:** Developers / Entwickler

---

## System Overview / Systemübersicht

VPB follows a layered architecture with clear separation of concerns.

VPB folgt einer Schichtenarchitektur mit klarer Aufgabentrennung.

---

## Architecture Layers / Architekturschichten

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│                  (UI / Views / Dialogs)                  │
├─────────────────────────────────────────────────────────┤
│                   Application Layer                      │
│                   (Controllers / Coordinators)           │
├─────────────────────────────────────────────────────────┤
│                    Business Logic Layer                  │
│                  (Services / Domain Logic)               │
├─────────────────────────────────────────────────────────┤
│                      Data Layer                          │
│                  (Models / Repositories)                 │
├─────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                   │
│            (Event Bus / Settings / Persistence)          │
└─────────────────────────────────────────────────────────┘
```

---

## Layer Details / Schichtendetails

### 1. Presentation Layer (UI)

**Location:** `vpb/ui/`, `vpb/views/`

**Responsibilities:**
- User interface components
- User input handling
- Display logic
- Visual feedback

**Key Components:**
- Canvas (process visualization)
- Palette (element library)
- Properties panel
- Dialogs and wizards

**Technology:**
- PyQt6 (GUI framework)
- Custom widgets
- Event-driven UI

---

### 2. Application Layer (Controllers)

**Location:** `vpb/controllers/`

**Responsibilities:**
- Coordinate between layers
- Handle user actions
- Manage application flow
- Event orchestration

**Key Controllers:**
- `DocumentController` - Document operations
- `ElementController` - Element management
- `ConnectionController` - Connection handling
- `ValidationController` - Process validation
- `ExportController` - Export operations
- `AIController` - AI features
- `LayoutController` - Auto-layout

**Pattern:** Event-driven architecture with message bus

---

### 3. Business Logic Layer (Services)

**Location:** `vpb/services/`

**Responsibilities:**
- Business rules
- Process validation
- Export logic
- AI integration
- Layout algorithms

**Key Services:**
- `DocumentService` - CRUD operations
- `ValidationService` - Validation rules
- `ExportService` - Multi-format export
- `LayoutService` - Auto-layout algorithms
- `AIService` - AI/ML integration
- `AutosaveService` - Auto-save functionality
- `BackupService` - Backup management

---

### 4. Data Layer (Models)

**Location:** `vpb/models/`

**Responsibilities:**
- Data structures
- Domain models
- Validation rules
- Serialization

**Key Models:**
- `DocumentModel` - Process document
- `VPBElement` - Process elements
- `VPBConnection` - Element connections
- `PaletteModel` - Element palette

**Patterns:**
- Observer pattern (model changes)
- Factory pattern (element creation)
- Builder pattern (complex objects)

---

### 5. Infrastructure Layer

**Location:** `vpb/infrastructure/`, `core/`

**Responsibilities:**
- Event bus
- Settings management
- User profiles
- Backend integration

**Key Components:**
- `EventBus` - Pub/sub messaging
- `SettingsManager` - Configuration
- `UserProfileManager` - User preferences
- `PolyglotManager` - Multi-backend persistence

---

## Design Patterns / Designmuster

### 1. Event-Driven Architecture

**Event Bus Pattern:**
```python
# Publish event
event_bus.publish("element.created", element)

# Subscribe to event
event_bus.subscribe("element.created", handler)
```

**Benefits:**
- Loose coupling
- Extensibility
- Testability

---

### 2. Model-View-Controller (MVC)

**Separation:**
- **Model:** Data and business logic
- **View:** UI presentation
- **Controller:** Coordination

**Flow:**
```
User Action → View → Controller → Service → Model
                ↑                              ↓
                └──────── Event Bus ───────────┘
```

---

### 3. Observer Pattern

**Model Changes:**
```python
class DocumentModel:
    def add_element(self, element):
        self.elements.append(element)
        self.notify_observers("element_added", element)
```

**Observers:**
- UI updates automatically
- Validation triggers
- Auto-save activates

---

### 4. Strategy Pattern

**Layout Algorithms:**
```python
class LayoutService:
    def set_strategy(self, strategy):
        self.strategy = strategy
    
    def apply_layout(self, document):
        return self.strategy.layout(document)
```

**Strategies:**
- Hierarchical
- Grid
- Circular
- Force-directed

---

### 5. SAGA Pattern

**Distributed Transactions:**
```python
# UDS3 Backend Integration
transaction = saga_manager.begin_transaction()
try:
    saga_manager.save_to_postgres(data)
    saga_manager.save_to_neo4j(graph)
    saga_manager.save_to_chroma(vectors)
    saga_manager.commit()
except:
    saga_manager.rollback()
```

**Benefits:**
- Consistency across backends
- Rollback capability
- Error recovery

---

## Component Dependencies / Komponenten-Abhängigkeiten

### Dependency Graph

```
Views
  ├── Controllers
  │     ├── Services
  │     │     ├── Models
  │     │     └── Infrastructure
  │     └── Infrastructure (Event Bus)
  └── Models (read-only)

API
  ├── Core (Polyglot Manager)
  │     └── Backends (PostgreSQL, Neo4j, ChromaDB)
  └── Models
```

### Dependency Rules

1. **No circular dependencies**
2. **Depend on abstractions, not implementations**
3. **UI depends on controllers, not services**
4. **Services don't depend on UI**

---

## Data Flow / Datenfluss

### Creating an Element

```
1. User drags element from palette
   ↓
2. View publishes "element.drop" event
   ↓
3. ElementController receives event
   ↓
4. Controller calls ElementService.create()
   ↓
5. Service creates VPBElement model
   ↓
6. Service publishes "element.created" event
   ↓
7. DocumentController updates document
   ↓
8. Canvas view refreshes display
```

### Saving a Process

```
1. User clicks Save
   ↓
2. Menu publishes "document.save" event
   ↓
3. DocumentController receives event
   ↓
4. Controller calls DocumentService.save()
   ↓
5. Service serializes DocumentModel to JSON
   ↓
6. Service writes to file
   ↓
7. Service publishes "document.saved" event
   ↓
8. StatusBar shows "Saved" message
```

---

## UDS3 Backend Architecture

### Polyglot Persistence

**Three Backend Systems:**

```
┌──────────────────────────────────────────────────┐
│           VPB Application Layer                   │
└────────────────┬─────────────────────────────────┘
                 │
         ┌───────┴────────┐
         │ Polyglot Mgr   │ (SAGA Pattern)
         └───────┬────────┘
                 │
    ┌────────────┼────────────┐
    ↓            ↓            ↓
┌─────────┐ ┌─────────┐ ┌──────────┐
│PostgreSQL│ │ Neo4j   │ │ChromaDB  │
│ (Data)   │ │(Graph)  │ │(Vectors) │
└─────────┘ └─────────┘ └──────────┘
```

**Data Distribution:**
- **PostgreSQL:** Structured process data (CRUD)
- **Neo4j:** Process graph relationships
- **ChromaDB:** Vector embeddings for AI search

**See:** [[UDS3-Backend]] for details

---

## API Architecture

### REST API (FastAPI)

**Endpoints:**
```
GET    /api/uds3/vpb/processes
POST   /api/uds3/vpb/processes
GET    /api/uds3/vpb/processes/{id}
PUT    /api/uds3/vpb/processes/{id}
DELETE /api/uds3/vpb/processes/{id}
GET    /api/uds3/vpb/search
GET    /api/uds3/vpb/health
```

**Architecture:**
```
Request → FastAPI → Endpoint Handler → Polyglot Manager
                                            ↓
                                    SAGA Transaction
                                            ↓
                                  PostgreSQL + Neo4j + ChromaDB
```

**See:** [[API-Reference]] for details

---

## Event System / Event-System

### Event Bus

**Central Message Bus:**
```python
class EventBus:
    def publish(self, event_type, data):
        """Publish event to all subscribers"""
        
    def subscribe(self, event_type, handler):
        """Subscribe to event type"""
```

### Event Types

**Document Events:**
- `document.created`
- `document.loaded`
- `document.saved`
- `document.closed`

**Element Events:**
- `element.created`
- `element.modified`
- `element.deleted`
- `element.selected`

**Connection Events:**
- `connection.created`
- `connection.deleted`

**Validation Events:**
- `validation.started`
- `validation.completed`
- `validation.error`

---

## Testing Architecture / Test-Architektur

### Test Pyramid

```
        ╱╲
       ╱  ╲     E2E Tests (10%)
      ╱────╲
     ╱      ╲   Integration Tests (20%)
    ╱────────╲
   ╱          ╲ Unit Tests (70%)
  ╱────────────╲
```

### Test Organization

```
tests/
├── unit/           # Unit tests (isolated components)
├── integration/    # Integration tests (multi-component)
├── e2e/           # End-to-end tests (full workflows)
└── fixtures/      # Test data and mocks
```

**See:** [[Testing]] for details

---

## Extension Points / Erweiterungspunkte

### 1. Custom Elements

**Create new SPS elements:**
```python
class CustomElement(VPBElement):
    def __init__(self):
        super().__init__()
        self.type = "CUSTOM"
```

### 2. Custom Export Formats

**Add export format:**
```python
class CustomExporter:
    def export(self, document):
        # Custom export logic
        pass
```

### 3. Custom Layout Algorithms

**Add layout strategy:**
```python
class CustomLayout:
    def layout(self, elements):
        # Custom layout logic
        pass
```

### 4. Custom Validators

**Add validation rules:**
```python
class CustomValidator:
    def validate(self, element):
        # Custom validation logic
        pass
```

**See:** [[Extension-Development]] for details

---

## Technology Stack / Technologie-Stack

### Frontend (Desktop GUI)
- **PyQt6** - GUI framework
- **Python 3.8+** - Programming language

### Backend (API Server)
- **FastAPI** - REST API framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### Persistence
- **PostgreSQL** - Relational database
- **Neo4j** - Graph database
- **ChromaDB** - Vector database
- **SQLAlchemy** - ORM

### AI/ML
- **Ollama** - Local LLM integration
- **LangChain** - AI orchestration (planned)

### Testing
- **pytest** - Test framework
- **pytest-qt** - Qt testing
- **coverage** - Code coverage

---

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**
   - Load processes on demand
   - Defer heavy computations

2. **Caching**
   - Cache validation results
   - Cache layout calculations

3. **Async Operations**
   - Background tasks
   - Non-blocking UI

4. **Batch Updates**
   - Group UI updates
   - Minimize redraws

---

## Security Considerations

### Current Status (v0.5.0)

**Security Features:**
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)
- Type safety (Python type hints)

**Future Enhancements:**
- Authentication
- Authorization
- Encryption at rest
- Audit logging

---

## Deployment

### Desktop Application

**Standalone Deployment:**
```bash
python vpb_app.py
```

### API Server

**Development:**
```bash
uvicorn api.uds3_vpb_fastapi:app --reload
```

**Production:**
```bash
uvicorn api.uds3_vpb_fastapi:app --host 0.0.0.0 --port 8000
```

---

## Related Documentation

- **[[Development-Guide]]** - Setup development environment
- **[[API-Reference]]** - API documentation
- **[[UDS3-Backend]]** - Backend architecture
- **[[Extension-Development]]** - Extending VPB

---

[[Home]] | [[Development-Guide]] | [[API-Reference]]
