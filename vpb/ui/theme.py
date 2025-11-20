"""
Theme System für VPB Editor.

Zentrale Verwaltung von Farben und visuellen Stilen.
Unterstützt konsistentes Design über alle UI-Komponenten.

OOP-Prinzip: Single Responsibility - verwaltet nur Theme/Farben
"""

from __future__ import annotations
from typing import Dict, Optional, Tuple


class ThemeColors:
    """
    Zentrale Farbdefinitionen für den VPB Editor.
    
    Folgt einem modernen, professionellen Farbschema mit klarer Hierarchie.
    Alle Farben sind als Hex-Strings definiert (#RRGGBB).
    """
    
    # Primärfarben
    PRIMARY = "#2563EB"              # Blau - Hauptaktionen
    PRIMARY_HOVER = "#1D4ED8"        # Dunkleres Blau - Hover
    PRIMARY_LIGHT = "#DBEAFE"        # Hellblau - Hintergrund
    PRIMARY_DARK = "#1E40AF"         # Dunkelblau - Aktiv
    
    # Sekundärfarben
    SECONDARY = "#64748B"            # Grau - Sekundäre Elemente
    SECONDARY_HOVER = "#475569"      # Dunkleres Grau - Hover
    SECONDARY_LIGHT = "#F1F5F9"      # Hellgrau - Hintergrund
    
    # Status-Farben
    SUCCESS = "#10B981"              # Grün - Erfolg
    SUCCESS_LIGHT = "#D1FAE5"        # Hellgrün - Hintergrund
    WARNING = "#F59E0B"              # Orange - Warnung
    WARNING_LIGHT = "#FEF3C7"        # Hellorange - Hintergrund
    ERROR = "#EF4444"                # Rot - Fehler
    ERROR_LIGHT = "#FEE2E2"          # Hellrot - Hintergrund
    INFO = "#3B82F6"                 # Hellblau - Info
    INFO_LIGHT = "#DBEAFE"           # Info Hintergrund
    
    # Hintergrundfarben
    BG_PRIMARY = "#FFFFFF"           # Weiß - Haupthintergrund
    BG_SECONDARY = "#F8FAFC"         # Hellgrau - Sekundärer Hintergrund
    BG_TERTIARY = "#F1F5F9"          # Grau - Toolbar/Sidebar
    BG_DARK = "#1E293B"              # Dunkel - Dark Mode (zukünftig)
    BG_HOVER = "#F8FAFC"             # Hover-Hintergrund
    BG_SELECTED = "#EFF6FF"          # Ausgewählt
    BG_DISABLED = "#F9FAFB"          # Deaktiviert
    
    # Textfarben
    TEXT_PRIMARY = "#0F172A"         # Dunkel - Haupttext
    TEXT_SECONDARY = "#475569"       # Grau - Sekundärtext
    TEXT_MUTED = "#94A3B8"           # Hellgrau - Deaktiviert
    TEXT_INVERSE = "#F8FAFC"         # Hell - Auf dunklem Hintergrund
    TEXT_LINK = "#2563EB"            # Link-Farbe
    
    # Border/Outline
    BORDER_LIGHT = "#E2E8F0"         # Helle Border
    BORDER_MEDIUM = "#CBD5E1"        # Mittlere Border
    BORDER_DARK = "#94A3B8"          # Dunkle Border
    BORDER_FOCUS = "#2563EB"         # Focus Border
    
    # Canvas-spezifisch
    CANVAS_BG = "#FAFBFC"            # Canvas Hintergrund
    GRID_LINE = "#E5E7EB"            # Grid-Linien
    GRID_MAJOR = "#D1D5DB"           # Haupt-Grid-Linien
    RULER_BG = "#F3F4F6"             # Lineal-Hintergrund
    RULER_TEXT = "#6B7280"           # Lineal-Text
    SELECTION = "#3B82F6"            # Auswahl-Rahmen
    SELECTION_FILL = "#3B82F640"     # Auswahl-Füllung (mit Alpha)
    GUIDE_LINE = "#F59E0B"           # Hilfslinien
    
    # Toolbar/Menu
    TOOLBAR_BG = "#F8FAFC"           # Toolbar Hintergrund
    TOOLBAR_SEPARATOR = "#E2E8F0"    # Toolbar Separator
    MENU_HOVER = "#F1F5F9"           # Menu Item Hover
    
    # Shadows (für zukünftige Verwendung)
    SHADOW_SM = "#0000000D"          # Kleiner Schatten (opacity ~5%)
    SHADOW_MD = "#0000001A"          # Mittlerer Schatten (opacity ~10%)
    SHADOW_LG = "#00000026"          # Großer Schatten (opacity ~15%)


class ThemeManager:
    """
    Verwaltet Theme-Einstellungen und -Farben.
    
    Ermöglicht zentrale Verwaltung von Farben und einfaches
    Wechseln zwischen verschiedenen Themes (z.B. Light/Dark).
    
    Beispiel:
        >>> theme = ThemeManager()
        >>> primary = theme.get_color("primary")
        >>> bg = theme.get_color("bg_primary")
    """
    
    def __init__(self, theme_name: str = "light"):
        """
        Initialisiert den Theme Manager.
        
        Args:
            theme_name: Name des zu verwendenden Themes ("light" oder "dark")
        """
        self.theme_name = theme_name
        self._colors = self._load_theme(theme_name)
        self._observers = []
    
    def _load_theme(self, theme_name: str) -> Dict[str, str]:
        """
        Lädt Theme-Farben basierend auf dem Namen.
        
        Args:
            theme_name: Name des Themes
            
        Returns:
            Dictionary mit Farb-Mappings
        """
        if theme_name == "light":
            return {
                # Primärfarben
                "primary": ThemeColors.PRIMARY,
                "primary_hover": ThemeColors.PRIMARY_HOVER,
                "primary_light": ThemeColors.PRIMARY_LIGHT,
                "primary_dark": ThemeColors.PRIMARY_DARK,
                
                # Sekundärfarben
                "secondary": ThemeColors.SECONDARY,
                "secondary_hover": ThemeColors.SECONDARY_HOVER,
                "secondary_light": ThemeColors.SECONDARY_LIGHT,
                
                # Status
                "success": ThemeColors.SUCCESS,
                "success_light": ThemeColors.SUCCESS_LIGHT,
                "warning": ThemeColors.WARNING,
                "warning_light": ThemeColors.WARNING_LIGHT,
                "error": ThemeColors.ERROR,
                "error_light": ThemeColors.ERROR_LIGHT,
                "info": ThemeColors.INFO,
                "info_light": ThemeColors.INFO_LIGHT,
                
                # Hintergründe
                "bg_primary": ThemeColors.BG_PRIMARY,
                "bg_secondary": ThemeColors.BG_SECONDARY,
                "bg_tertiary": ThemeColors.BG_TERTIARY,
                "bg_hover": ThemeColors.BG_HOVER,
                "bg_selected": ThemeColors.BG_SELECTED,
                "bg_disabled": ThemeColors.BG_DISABLED,
                
                # Text
                "text_primary": ThemeColors.TEXT_PRIMARY,
                "text_secondary": ThemeColors.TEXT_SECONDARY,
                "text_muted": ThemeColors.TEXT_MUTED,
                "text_link": ThemeColors.TEXT_LINK,
                
                # Borders
                "border_light": ThemeColors.BORDER_LIGHT,
                "border_medium": ThemeColors.BORDER_MEDIUM,
                "border_dark": ThemeColors.BORDER_DARK,
                "border_focus": ThemeColors.BORDER_FOCUS,
                
                # Canvas
                "canvas_bg": ThemeColors.CANVAS_BG,
                "grid_line": ThemeColors.GRID_LINE,
                "grid_major": ThemeColors.GRID_MAJOR,
                "ruler_bg": ThemeColors.RULER_BG,
                "ruler_text": ThemeColors.RULER_TEXT,
                "selection": ThemeColors.SELECTION,
                "selection_fill": ThemeColors.SELECTION_FILL,
                "guide_line": ThemeColors.GUIDE_LINE,
                
                # Toolbar/Menu
                "toolbar_bg": ThemeColors.TOOLBAR_BG,
                "toolbar_separator": ThemeColors.TOOLBAR_SEPARATOR,
                "menu_hover": ThemeColors.MENU_HOVER,
            }
        else:
            # Dark theme (zukünftig)
            return self._load_theme("light")  # Fallback to light
    
    def get_color(self, color_name: str, default: str = "#000000") -> str:
        """
        Holt eine Farbe aus dem aktuellen Theme.
        
        Args:
            color_name: Name der Farbe (z.B. "primary", "bg_secondary")
            default: Fallback-Farbe falls Name nicht gefunden
            
        Returns:
            Hex-Farbstring
        """
        return self._colors.get(color_name, default)
    
    def get_rgb(self, color_name: str) -> Optional[Tuple[int, int, int]]:
        """
        Holt eine Farbe als RGB-Tupel.
        
        Args:
            color_name: Name der Farbe
            
        Returns:
            RGB-Tupel (r, g, b) oder None falls nicht gefunden
        """
        hex_color = self.get_color(color_name)
        if not hex_color or len(hex_color) != 7:
            return None
        
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            return (r, g, b)
        except ValueError:
            return None
    
    def switch_theme(self, theme_name: str):
        """
        Wechselt zu einem anderen Theme.
        
        Args:
            theme_name: Name des neuen Themes
        """
        self.theme_name = theme_name
        self._colors = self._load_theme(theme_name)
        self._notify_observers()
    
    def subscribe(self, callback):
        """
        Registriert einen Observer für Theme-Änderungen.
        
        Args:
            callback: Funktion die bei Theme-Wechsel aufgerufen wird
        """
        if callback not in self._observers:
            self._observers.append(callback)
    
    def unsubscribe(self, callback):
        """
        Entfernt einen Observer.
        
        Args:
            callback: Zu entfernende Callback-Funktion
        """
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self):
        """Benachrichtigt alle Observer über Theme-Änderung."""
        for callback in self._observers:
            callback(self.theme_name)


# Globale Theme-Instanz (Singleton-Pattern)
_global_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """
    Holt die globale Theme-Manager-Instanz.
    
    Returns:
        Globale ThemeManager-Instanz
    """
    global _global_theme_manager
    if _global_theme_manager is None:
        _global_theme_manager = ThemeManager()
    return _global_theme_manager


__all__ = ["ThemeColors", "ThemeManager", "get_theme_manager"]
