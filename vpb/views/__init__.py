"""
VPB Views Layer
===============

GUI components and visual elements for VPB Process Designer.

This package contains:
- MainWindow: Application main window
- MenuBarView: Menu bar with all menus
- ToolbarView: Toolbar with VPB branding and buttons
- StatusBarView: Status bar with messages and info
- CanvasView: Process diagram canvas (TODO)
- PaletteView: Element palette panel (TODO)
- PropertiesView: Element properties panel (TODO)
- Dialogs: Various dialog windows (TODO)

WICHTIG: Views enthalten NUR GUI-Code!
- Keine Business-Logik
- Keine direkten Service-Aufrufe  
- Alle Aktionen über Event-Bus an Controller
"""

from .main_window import (
    MainWindow,
    create_main_window,
    restore_window_state,
    save_window_state,
)
from .menu_bar import (
    MenuBarView,
    create_menu_bar,
    get_menu_bar_state,
    restore_menu_bar_state,
)
from .toolbar import (
    ToolbarView,
    create_toolbar,
)
from .status_bar import (
    StatusBarView,
    create_status_bar,
    get_status_bar_state,
    restore_status_bar_state,
)
from .canvas_view import (
    CanvasView,
    create_canvas_view,
)
from .palette_view import (
    PaletteView,
    create_palette_view,
)
from .properties_view import (
    PropertiesView,
    create_properties_view,
)
from .dialogs import (
    AboutDialog,
    create_about_dialog,
)

__all__ = [
    # Main Window
    'MainWindow',
    'create_main_window',
    'restore_window_state',
    'save_window_state',
    # Menu Bar
    'MenuBarView',
    'create_menu_bar',
    'get_menu_bar_state',
    'restore_menu_bar_state',
    # Toolbar
    'ToolbarView',
    'create_toolbar',
    # Status Bar
    'StatusBarView',
    'create_status_bar',
    'get_status_bar_state',
    'restore_status_bar_state',
    # Canvas
    'CanvasView',
    'create_canvas_view',
    # Palette
    'PaletteView',
    'create_palette_view',
    # Properties
    'PropertiesView',
    'create_properties_view',
    # Dialogs
    'AboutDialog',
    'create_about_dialog',
]
