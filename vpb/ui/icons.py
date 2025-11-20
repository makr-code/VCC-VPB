"""
Icon System für VPB Editor.

Zentrale Verwaltung von Unicode-Icons für bessere Visualisierung.
Bietet konsistente Icons über alle UI-Komponenten.

OOP-Prinzip: Single Responsibility - verwaltet nur Icons
"""

from __future__ import annotations
from typing import Dict, Optional


class UIIcons:
    """
    Unicode-Icons für den VPB Editor.
    
    Verwendet Unicode-Symbole für plattformübergreifende Darstellung
    ohne externe Icon-Dateien.
    """
    
    # Datei-Operationen
    NEW = "📄"
    OPEN = "📂"
    SAVE = "💾"
    SAVE_AS = "💾"
    EXPORT = "📤"
    IMPORT = "📥"
    CLOSE = "✖"
    RECENT = "🕒"
    
    # Bearbeiten
    UNDO = "↶"
    REDO = "↷"
    CUT = "✂"
    COPY = "📋"
    PASTE = "📋"
    DELETE = "🗑"
    DUPLICATE = "⧉"
    SELECT_ALL = "☐"
    
    # Ansicht
    ZOOM_IN = "🔍+"
    ZOOM_OUT = "🔍−"
    ZOOM_FIT = "⊡"
    ZOOM_100 = "⊙"
    FULLSCREEN = "⛶"
    GRID = "⊞"
    RULERS = "📏"
    MINIMAP = "🗺"
    
    # Layout/Anordnen
    ALIGN_LEFT = "◧"
    ALIGN_CENTER = "◫"
    ALIGN_RIGHT = "◨"
    ALIGN_TOP = "⬒"
    ALIGN_MIDDLE = "⬓"
    ALIGN_BOTTOM = "⬔"
    DISTRIBUTE_H = "⬌"
    DISTRIBUTE_V = "⬍"
    
    # Rotation und Flip
    ROTATE_LEFT = "↺"
    ROTATE_RIGHT = "↻"
    FLIP_H = "⇄"
    FLIP_V = "⇅"
    
    # Elemente
    ADD = "➕"
    ADD_ELEMENT = "➕"
    ADD_CONNECTION = "➡"
    GROUP = "⧉"
    UNGROUP = "⧈"
    LAYER_UP = "⬆"
    LAYER_DOWN = "⬇"
    LAYER_TOP = "⤒"
    LAYER_BOTTOM = "⤓"
    
    # Werkzeuge
    POINTER = "⊙"
    PENCIL = "✎"
    VALIDATE = "✓"
    CHECK = "✓"
    SETTINGS = "⚙"
    PREFERENCES = "⚙"
    HELP = "❓"
    INFO = "ℹ"
    WARNING = "⚠"
    ERROR = "⚠"
    DEBUG = "🐛"
    
    # Navigation
    EXPAND = "▾"
    COLLAPSE = "▸"
    EXPAND_ALL = "▾▾"
    COLLAPSE_ALL = "▸▸"
    REFRESH = "↻"
    RELOAD = "↻"
    SEARCH = "🔍"
    FILTER = "⊙"
    
    # Pfeile
    UP = "▲"
    DOWN = "▼"
    LEFT = "◀"
    RIGHT = "▶"
    UP_ARROW = "↑"
    DOWN_ARROW = "↓"
    LEFT_ARROW = "←"
    RIGHT_ARROW = "→"
    
    # Status
    SUCCESS = "✓"
    PENDING = "⏳"
    RUNNING = "⟳"
    FAILED = "✗"
    LOCKED = "🔒"
    UNLOCKED = "🔓"
    VISIBLE = "👁"
    HIDDEN = "⊘"
    
    # AI/Chat
    AI = "🤖"
    CHAT = "💬"
    SEND = "➤"
    STOP = "⏹"
    PAUSE = "⏸"
    PLAY = "▶"
    ATTACH = "📎"
    CODE = "⌨"
    
    # Prozess-Elemente
    EVENT = "⬭"
    FUNCTION = "▭"
    GATEWAY = "⬥"
    SUBPROCESS = "▢"
    START = "▶"
    END = "⏹"
    DECISION = "⬥"
    MERGE = "⧓"
    
    # Organisation
    ORGANIZATION = "🏢"
    PERSON = "👤"
    TEAM = "👥"
    ROLE = "🎭"
    
    # Daten/Dokumente
    DOCUMENT = "📄"
    DATABASE = "🗄"
    FOLDER = "📁"
    FILE = "📄"
    
    # Verbindungen
    SEQUENCE = "→"
    MESSAGE = "✉"
    ASSOCIATION = "⋯"
    
    # Sonstiges
    HOME = "⌂"
    STAR = "★"
    STAR_OUTLINE = "☆"
    BOOKMARK = "🔖"
    TAG = "🏷"
    CALENDAR = "📅"
    CLOCK = "🕐"
    LINK = "🔗"
    UNLINK = "⛓"
    
    # Formatting
    BOLD = "B"
    ITALIC = "I"
    UNDERLINE = "U"
    COLOR = "🎨"
    
    # Window Controls
    MINIMIZE = "−"
    MAXIMIZE = "□"
    RESTORE = "❐"
    CLOSE_WINDOW = "✖"


class IconManager:
    """
    Verwaltet Icons und deren Verwendung.
    
    Ermöglicht zentrale Verwaltung und einfaches Anpassen von Icons.
    
    Beispiel:
        >>> icons = IconManager()
        >>> save_icon = icons.get("save")
        >>> icons.set_custom("save", "⎘")
    """
    
    def __init__(self):
        """Initialisiert den Icon Manager."""
        self._icons = self._load_default_icons()
        self._custom_icons = {}
    
    def _load_default_icons(self) -> Dict[str, str]:
        """
        Lädt Standard-Icons.
        
        Returns:
            Dictionary mit Icon-Mappings
        """
        return {
            # Datei
            "new": UIIcons.NEW,
            "open": UIIcons.OPEN,
            "save": UIIcons.SAVE,
            "save_as": UIIcons.SAVE_AS,
            "export": UIIcons.EXPORT,
            "import": UIIcons.IMPORT,
            "close": UIIcons.CLOSE,
            "recent": UIIcons.RECENT,
            
            # Bearbeiten
            "undo": UIIcons.UNDO,
            "redo": UIIcons.REDO,
            "cut": UIIcons.CUT,
            "copy": UIIcons.COPY,
            "paste": UIIcons.PASTE,
            "delete": UIIcons.DELETE,
            "duplicate": UIIcons.DUPLICATE,
            "select_all": UIIcons.SELECT_ALL,
            
            # Ansicht
            "zoom_in": UIIcons.ZOOM_IN,
            "zoom_out": UIIcons.ZOOM_OUT,
            "zoom_fit": UIIcons.ZOOM_FIT,
            "zoom_100": UIIcons.ZOOM_100,
            "fullscreen": UIIcons.FULLSCREEN,
            "grid": UIIcons.GRID,
            "rulers": UIIcons.RULERS,
            "minimap": UIIcons.MINIMAP,
            
            # Layout
            "align_left": UIIcons.ALIGN_LEFT,
            "align_center": UIIcons.ALIGN_CENTER,
            "align_right": UIIcons.ALIGN_RIGHT,
            "align_top": UIIcons.ALIGN_TOP,
            "align_middle": UIIcons.ALIGN_MIDDLE,
            "align_bottom": UIIcons.ALIGN_BOTTOM,
            "distribute_h": UIIcons.DISTRIBUTE_H,
            "distribute_v": UIIcons.DISTRIBUTE_V,
            
            # Rotation
            "rotate_left": UIIcons.ROTATE_LEFT,
            "rotate_right": UIIcons.ROTATE_RIGHT,
            "flip_h": UIIcons.FLIP_H,
            "flip_v": UIIcons.FLIP_V,
            
            # Elemente
            "add": UIIcons.ADD,
            "add_element": UIIcons.ADD_ELEMENT,
            "add_connection": UIIcons.ADD_CONNECTION,
            "group": UIIcons.GROUP,
            "ungroup": UIIcons.UNGROUP,
            
            # Werkzeuge
            "validate": UIIcons.VALIDATE,
            "settings": UIIcons.SETTINGS,
            "help": UIIcons.HELP,
            "info": UIIcons.INFO,
            "warning": UIIcons.WARNING,
            "error": UIIcons.ERROR,
            
            # Navigation
            "expand": UIIcons.EXPAND,
            "collapse": UIIcons.COLLAPSE,
            "expand_all": UIIcons.EXPAND_ALL,
            "collapse_all": UIIcons.COLLAPSE_ALL,
            "refresh": UIIcons.REFRESH,
            "search": UIIcons.SEARCH,
            
            # Status
            "success": UIIcons.SUCCESS,
            "pending": UIIcons.PENDING,
            "running": UIIcons.RUNNING,
            "failed": UIIcons.FAILED,
            
            # AI
            "ai": UIIcons.AI,
            "chat": UIIcons.CHAT,
            "send": UIIcons.SEND,
            "stop": UIIcons.STOP,
            "attach": UIIcons.ATTACH,
        }
    
    def get(self, icon_name: str, default: str = "•") -> str:
        """
        Holt ein Icon.
        
        Args:
            icon_name: Name des Icons
            default: Fallback-Icon falls nicht gefunden
            
        Returns:
            Icon-String (Unicode)
        """
        # Erst in Custom-Icons suchen
        if icon_name in self._custom_icons:
            return self._custom_icons[icon_name]
        
        # Dann in Standard-Icons
        return self._icons.get(icon_name, default)
    
    def set_custom(self, icon_name: str, icon_value: str):
        """
        Setzt ein benutzerdefiniertes Icon.
        
        Args:
            icon_name: Name des Icons
            icon_value: Unicode-String für das Icon
        """
        self._custom_icons[icon_name] = icon_value
    
    def reset_custom(self, icon_name: str):
        """
        Setzt ein benutzerdefiniertes Icon zurück.
        
        Args:
            icon_name: Name des Icons
        """
        if icon_name in self._custom_icons:
            del self._custom_icons[icon_name]
    
    def get_all(self) -> Dict[str, str]:
        """
        Holt alle Icons.
        
        Returns:
            Dictionary mit allen Icon-Mappings
        """
        result = self._icons.copy()
        result.update(self._custom_icons)
        return result


# Globale Icon-Manager-Instanz (Singleton-Pattern)
_global_icon_manager: Optional[IconManager] = None


def get_icon_manager() -> IconManager:
    """
    Holt die globale Icon-Manager-Instanz.
    
    Returns:
        Globale IconManager-Instanz
    """
    global _global_icon_manager
    if _global_icon_manager is None:
        _global_icon_manager = IconManager()
    return _global_icon_manager


def get_icon(icon_name: str, default: str = "•") -> str:
    """
    Convenience-Funktion zum Holen eines Icons.
    
    Args:
        icon_name: Name des Icons
        default: Fallback-Icon
        
    Returns:
        Icon-String
    """
    return get_icon_manager().get(icon_name, default)


__all__ = ["UIIcons", "IconManager", "get_icon_manager", "get_icon"]
