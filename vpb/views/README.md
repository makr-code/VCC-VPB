# VPB Views

GUI components for VPB Process Designer.

## Overview

This package contains all visual components:

- **MainWindow**: Application main window layout
- **ToolbarView**: Toolbar with VPB branding (🔄 logo)
- **MenuBarView**: Menu bar with all commands
- **CanvasView**: Process diagram canvas
- **PaletteView**: Element palette panel
- **PropertiesView**: Element properties editor
- **Dialogs**: About, Settings, Export dialogs

## Architecture

Views follow these principles:

- **No Business Logic**: Views only display data and emit events
- **Event-Driven**: All user actions publish events via Event-Bus
- **Stateless**: State lives in Models, not Views
- **Composable**: Views are self-contained components
- **Testable**: Can be tested with Tkinter test harness

## Usage

```python
from vpb.infrastructure import EventBus
from vpb.views import MainWindow

event_bus = EventBus()
root = tk.Tk()

# Create main window
window = MainWindow(root, event_bus)

# Views emit events:
# - 'file.new', 'file.open', 'file.save'
# - 'element.add', 'element.delete'
# - etc.
```

## Testing

Views have UI tests in `tests/views/`.
