"""
Spacing System für VPB Editor.

Zentrale Verwaltung von Abständen, Padding und Margins.
Folgt einem 8pt-Grid-System für konsistente Abstände.

OOP-Prinzip: Single Responsibility - verwaltet nur Spacing
"""

from __future__ import annotations
from typing import Dict, Tuple, Optional


class SpacingSystem:
    """
    Spacing-Definitionen für den VPB Editor.
    
    Folgt einem 8pt-Grid-System (Basis: 8px) für konsistente
    und vorhersagbare Abstände.
    """
    
    # Basis-Spacing (8pt Grid)
    XS = 4       # Extra small (0.5 × 8)
    SM = 8       # Small (1 × 8)
    MD = 16      # Medium (2 × 8)
    LG = 24      # Large (3 × 8)
    XL = 32      # Extra large (4 × 8)
    XXL = 48     # Extra extra large (6 × 8)
    
    # Spezielle Werte
    NONE = 0
    TINY = 2     # Für sehr enge Abstände
    HUGE = 64    # Für sehr große Abstände
    
    # Padding-Presets (horizontal, vertical)
    PADDING_TIGHT = (4, 2)        # Sehr eng
    PADDING_COMPACT = (6, 4)      # Kompakt
    PADDING_NORMAL = (8, 4)       # Normal
    PADDING_COMFORTABLE = (12, 6) # Komfortabel
    PADDING_SPACIOUS = (16, 8)    # Geräumig
    
    # Button-Padding
    BUTTON_PADDING_SM = (8, 4)    # Kleine Buttons
    BUTTON_PADDING_MD = (12, 6)   # Normale Buttons
    BUTTON_PADDING_LG = (16, 8)   # Große Buttons
    
    # Input-Padding
    INPUT_PADDING_SM = (6, 3)     # Kleine Inputs
    INPUT_PADDING_MD = (8, 4)     # Normale Inputs
    INPUT_PADDING_LG = (10, 5)    # Große Inputs
    
    # Panel-Padding
    PANEL_PADDING = (12, 12)      # Standard-Panel-Padding
    SIDEBAR_PADDING = (8, 8)      # Sidebar-Padding
    DIALOG_PADDING = (16, 16)     # Dialog-Padding
    
    # Margins (alle Seiten)
    MARGIN_XS = 4
    MARGIN_SM = 8
    MARGIN_MD = 12
    MARGIN_LG = 16
    MARGIN_XL = 24
    
    # Spezielle Margins
    SEPARATOR_MARGIN = 8          # Zwischen Button-Gruppen
    SECTION_MARGIN = 16           # Zwischen Sections
    FORM_FIELD_MARGIN = 8         # Zwischen Formular-Feldern
    
    # Border-Widths
    BORDER_THIN = 1
    BORDER_NORMAL = 2
    BORDER_THICK = 3
    
    # Mindestgrößen
    MIN_BUTTON_HEIGHT = 28
    MIN_BUTTON_WIDTH = 60
    MIN_INPUT_HEIGHT = 24
    MIN_TOOLBAR_HEIGHT = 40
    MIN_SIDEBAR_WIDTH = 250
    MIN_PANEL_WIDTH = 300
    MIN_ICON_BUTTON = 32
    
    # Canvas-spezifisch
    CANVAS_PADDING = 20           # Padding um Canvas-Inhalt
    GRID_SPACING = 20             # Grid-Abstände
    ELEMENT_SPACING = 40          # Mindestabstand zwischen Elementen
    CONNECTION_SPACING = 10       # Abstand für Verbindungspunkte


class SpacingManager:
    """
    Verwaltet Spacing-Werte.
    
    Bietet zentrale Verwaltung von Abständen für konsistente
    Layouts über alle UI-Komponenten.
    
    Beispiel:
        >>> spacing = SpacingManager()
        >>> padding = spacing.get_padding("normal")
        >>> margin = spacing.get_margin("md")
    """
    
    def __init__(self):
        """Initialisiert den Spacing Manager."""
        self._spacing = self._load_default_spacing()
        self._padding = self._load_default_padding()
        self._custom_spacing = {}
        self._custom_padding = {}
    
    def _load_default_spacing(self) -> Dict[str, int]:
        """
        Lädt Standard-Spacing-Werte.
        
        Returns:
            Dictionary mit Spacing-Mappings
        """
        return {
            "none": SpacingSystem.NONE,
            "tiny": SpacingSystem.TINY,
            "xs": SpacingSystem.XS,
            "sm": SpacingSystem.SM,
            "md": SpacingSystem.MD,
            "lg": SpacingSystem.LG,
            "xl": SpacingSystem.XL,
            "xxl": SpacingSystem.XXL,
            "huge": SpacingSystem.HUGE,
        }
    
    def _load_default_padding(self) -> Dict[str, Tuple[int, int]]:
        """
        Lädt Standard-Padding-Werte.
        
        Returns:
            Dictionary mit Padding-Mappings (x, y)
        """
        return {
            # Allgemein
            "tight": SpacingSystem.PADDING_TIGHT,
            "compact": SpacingSystem.PADDING_COMPACT,
            "normal": SpacingSystem.PADDING_NORMAL,
            "comfortable": SpacingSystem.PADDING_COMFORTABLE,
            "spacious": SpacingSystem.PADDING_SPACIOUS,
            
            # Buttons
            "button_sm": SpacingSystem.BUTTON_PADDING_SM,
            "button_md": SpacingSystem.BUTTON_PADDING_MD,
            "button_lg": SpacingSystem.BUTTON_PADDING_LG,
            
            # Inputs
            "input_sm": SpacingSystem.INPUT_PADDING_SM,
            "input_md": SpacingSystem.INPUT_PADDING_MD,
            "input_lg": SpacingSystem.INPUT_PADDING_LG,
            
            # Panels
            "panel": SpacingSystem.PANEL_PADDING,
            "sidebar": SpacingSystem.SIDEBAR_PADDING,
            "dialog": SpacingSystem.DIALOG_PADDING,
        }
    
    def get_spacing(self, size_name: str) -> int:
        """
        Holt einen Spacing-Wert.
        
        Args:
            size_name: Name der Größe (xs, sm, md, lg, xl, xxl)
            
        Returns:
            Spacing-Wert in Pixeln
        """
        # Erst in Custom-Spacing suchen
        if size_name in self._custom_spacing:
            return self._custom_spacing[size_name]
        
        # Dann in Standard-Spacing
        return self._spacing.get(size_name, SpacingSystem.MD)
    
    def get_padding(self, padding_name: str) -> Tuple[int, int]:
        """
        Holt einen Padding-Wert.
        
        Args:
            padding_name: Name des Paddings
            
        Returns:
            Padding-Tupel (x, y)
        """
        # Erst in Custom-Padding suchen
        if padding_name in self._custom_padding:
            return self._custom_padding[padding_name]
        
        # Dann in Standard-Padding
        return self._padding.get(padding_name, SpacingSystem.PADDING_NORMAL)
    
    def get_margin(self, size_name: str) -> int:
        """
        Holt einen Margin-Wert (gleich wie spacing).
        
        Args:
            size_name: Name der Größe
            
        Returns:
            Margin-Wert in Pixeln
        """
        return self.get_spacing(size_name)
    
    def set_custom_spacing(self, size_name: str, value: int):
        """
        Setzt einen benutzerdefinierten Spacing-Wert.
        
        Args:
            size_name: Name der Größe
            value: Wert in Pixeln
        """
        self._custom_spacing[size_name] = value
    
    def set_custom_padding(self, padding_name: str, x: int, y: int):
        """
        Setzt einen benutzerdefinierten Padding-Wert.
        
        Args:
            padding_name: Name des Paddings
            x: Horizontales Padding
            y: Vertikales Padding
        """
        self._custom_padding[padding_name] = (x, y)
    
    def reset_custom_spacing(self, size_name: str):
        """
        Setzt einen benutzerdefinierten Spacing-Wert zurück.
        
        Args:
            size_name: Name der Größe
        """
        if size_name in self._custom_spacing:
            del self._custom_spacing[size_name]
    
    def reset_custom_padding(self, padding_name: str):
        """
        Setzt einen benutzerdefinierten Padding-Wert zurück.
        
        Args:
            padding_name: Name des Paddings
        """
        if padding_name in self._custom_padding:
            del self._custom_padding[padding_name]
    
    def scale_spacing(self, size_name: str, factor: float) -> int:
        """
        Skaliert einen Spacing-Wert.
        
        Args:
            size_name: Name der Größe
            factor: Skalierungsfaktor
            
        Returns:
            Skalierter Spacing-Wert
        """
        value = self.get_spacing(size_name)
        return int(value * factor)
    
    def scale_padding(self, padding_name: str, factor: float) -> Tuple[int, int]:
        """
        Skaliert einen Padding-Wert.
        
        Args:
            padding_name: Name des Paddings
            factor: Skalierungsfaktor
            
        Returns:
            Skaliertes Padding-Tupel
        """
        x, y = self.get_padding(padding_name)
        return (int(x * factor), int(y * factor))


# Globale Spacing-Manager-Instanz (Singleton-Pattern)
_global_spacing_manager: Optional[SpacingManager] = None


def get_spacing_manager() -> SpacingManager:
    """
    Holt die globale Spacing-Manager-Instanz.
    
    Returns:
        Globale SpacingManager-Instanz
    """
    global _global_spacing_manager
    if _global_spacing_manager is None:
        _global_spacing_manager = SpacingManager()
    return _global_spacing_manager


def get_spacing(size_name: str) -> int:
    """
    Convenience-Funktion zum Holen eines Spacing-Werts.
    
    Args:
        size_name: Name der Größe
        
    Returns:
        Spacing-Wert in Pixeln
    """
    return get_spacing_manager().get_spacing(size_name)


def get_padding(padding_name: str) -> Tuple[int, int]:
    """
    Convenience-Funktion zum Holen eines Padding-Werts.
    
    Args:
        padding_name: Name des Paddings
        
    Returns:
        Padding-Tupel (x, y)
    """
    return get_spacing_manager().get_padding(padding_name)


__all__ = ["SpacingSystem", "SpacingManager", "get_spacing_manager", "get_spacing", "get_padding"]
