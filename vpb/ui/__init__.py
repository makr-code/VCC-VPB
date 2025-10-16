"""UI components for the VPB application."""

from .chat_panel import ChatPanel
from .canvas import VPBCanvas, MiniMapCanvas, HierarchyCanvas, RulerCanvas
from .properties_panel import PropertiesPanel
from .task_manager import TaskManager
from .palette_panel import PaletteLoader, PalettePanel
from .arrange_panel import ArrangePanel
from .menu_bar import create_main_menu, create_main_toolbar
from .code_editor import add_code_editor_tab
from .xml_viewer import add_xml_viewer_tab
from .chat_console import create_chat_console
from .chat_controller import ChatController
from .canvas_controller import CanvasController
from .task_controller import TaskController
from .app_task_dispatch import AppTaskDispatch
from .right_sidebar import create_right_sidebar
from .diagram_tab import add_diagram_tab
from .canvas_interactions import configure_canvas_interactions
from .status_bar import create_status_bar
from .main_layout import create_main_layout, MainLayout
from .shortcut_overlay import toggle_shortcut_overlay, show_shortcut_overlay, hide_shortcut_overlay
from .properties_controller import PropertiesController

__all__ = [
    "ChatPanel",
    "VPBCanvas",
    "MiniMapCanvas",
    "HierarchyCanvas",
    "RulerCanvas",
    "PropertiesPanel",
    "TaskManager",
    "PalettePanel",
    "ArrangePanel",
    "PaletteLoader",
    "create_main_menu",
    "create_main_toolbar",
    "add_code_editor_tab",
    "add_xml_viewer_tab",
    "create_chat_console",
    "ChatController",
    "CanvasController",
    "TaskController",
    "AppTaskDispatch",
    "create_right_sidebar",
    "add_diagram_tab",
    "configure_canvas_interactions",
    "create_status_bar",
    "create_main_layout",
    "MainLayout",
    "toggle_shortcut_overlay",
    "show_shortcut_overlay",
    "hide_shortcut_overlay",
    "PropertiesController",
]
