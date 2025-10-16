# VPB Controllers

Controller layer for VPB Process Designer.

## Overview

Controllers mediate between Views and Models:

- **AppController**: Main application controller
- **CanvasController**: Canvas interactions (drag, select, etc.)
- **DocumentController**: Document lifecycle (new, open, save)
- **ToolbarController**: Toolbar button states

## Architecture

Controllers follow these principles:

- **Event-Driven**: Subscribe to View events via Event-Bus
- **Coordinate Services**: Call Services for business operations
- **Update Views**: Notify Views of state changes via Events
- **Stateless**: State lives in Models
- **Testable**: Can be tested with mocks

## Usage

```python
from vpb.infrastructure import EventBus
from vpb.controllers import AppController
from vpb.models import DocumentModel
from vpb.views import MainWindow

event_bus = EventBus()
model = DocumentModel()
view = MainWindow(root, event_bus)

# Create controller
controller = AppController(model, view, event_bus)

# Controller subscribes to events:
# - 'file.save' → controller.handle_save()
# - 'element.add' → controller.handle_add_element()
```

## Event Flow

```
User Action → View → Event-Bus → Controller → Service → Model
                                                          ↓
                                       Event-Bus ← Observer
                                            ↓
                                          View
```

## Testing

Controllers have unit tests with mocks in `tests/controllers/`.
