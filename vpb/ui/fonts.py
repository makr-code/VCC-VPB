"""
Font System für VPB Editor.

Zentrale Verwaltung von Schriftarten und Typografie.
Bietet konsistente Schriftgrößen und -stile über alle UI-Komponenten.

OOP-Prinzip: Single Responsibility - verwaltet nur Fonts
"""

from __future__ import annotations
import sys
from typing import Dict, Tuple, Optional


class FontSystem:
    """
    Schriftarten-Definitionen für den VPB Editor.
    
    Bietet plattformübergreifende Schriftarten-Auswahl und
    konsistente Typografie-Hierarchie.
    """
    
    # Plattform-spezifische Schriftfamilien
    if sys.platform == "win32":
        FAMILY_UI = "Segoe UI"
        FAMILY_MONO = "Consolas"
    elif sys.platform == "darwin":
        FAMILY_UI = "SF Pro"
        FAMILY_MONO = "SF Mono"
    else:  # Linux
        FAMILY_UI = "Ubuntu"
        FAMILY_MONO = "Ubuntu Mono"
    
    # Fallback-Schriftfamilien
    FALLBACK_UI = ["Helvetica Neue", "Arial", "sans-serif"]
    FALLBACK_MONO = ["Monaco", "Courier New", "monospace"]
    
    # Schriftgrößen
    SIZE_XXL = 20      # Hauptüberschriften
    SIZE_XL = 16       # Überschriften
    SIZE_LG = 14       # Große Labels
    SIZE_BASE = 12     # Normaler Text
    SIZE_SM = 10       # Kleiner Text
    SIZE_XS = 9        # Sehr klein
    
    # Schriftgewichte
    WEIGHT_LIGHT = "normal"    # Tkinter unterstützt nur normal/bold
    WEIGHT_NORMAL = "normal"
    WEIGHT_BOLD = "bold"


class FontManager:
    """
    Verwaltet Schriftarten und Typografie.
    
    Bietet zentrale Verwaltung von Schriftarten für konsistente
    Darstellung über alle UI-Komponenten.
    
    Beispiel:
        >>> fonts = FontManager()
        >>> heading_font = fonts.get("heading_1")
        >>> body_font = fonts.get("body")
    """
    
    def __init__(self):
        """Initialisiert den Font Manager."""
        self._fonts = self._load_default_fonts()
        self._custom_fonts = {}
    
    def _load_default_fonts(self) -> Dict[str, Tuple[str, int, str]]:
        """
        Lädt Standard-Schriftarten.
        
        Returns:
            Dictionary mit Font-Definitionen (family, size, weight)
        """
        return {
            # Überschriften
            "heading_1": (FontSystem.FAMILY_UI, FontSystem.SIZE_XXL, FontSystem.WEIGHT_BOLD),
            "heading_2": (FontSystem.FAMILY_UI, FontSystem.SIZE_XL, FontSystem.WEIGHT_BOLD),
            "heading_3": (FontSystem.FAMILY_UI, FontSystem.SIZE_LG, FontSystem.WEIGHT_BOLD),
            
            # Body Text
            "body": (FontSystem.FAMILY_UI, FontSystem.SIZE_BASE, FontSystem.WEIGHT_NORMAL),
            "body_bold": (FontSystem.FAMILY_UI, FontSystem.SIZE_BASE, FontSystem.WEIGHT_BOLD),
            "body_large": (FontSystem.FAMILY_UI, FontSystem.SIZE_LG, FontSystem.WEIGHT_NORMAL),
            
            # UI-Elemente
            "button": (FontSystem.FAMILY_UI, FontSystem.SIZE_BASE, FontSystem.WEIGHT_NORMAL),
            "button_large": (FontSystem.FAMILY_UI, FontSystem.SIZE_LG, FontSystem.WEIGHT_NORMAL),
            "menu": (FontSystem.FAMILY_UI, 11, FontSystem.WEIGHT_NORMAL),
            "label": (FontSystem.FAMILY_UI, FontSystem.SIZE_BASE, FontSystem.WEIGHT_NORMAL),
            "label_bold": (FontSystem.FAMILY_UI, FontSystem.SIZE_BASE, FontSystem.WEIGHT_BOLD),
            
            # Kleine Texte
            "caption": (FontSystem.FAMILY_UI, FontSystem.SIZE_SM, FontSystem.WEIGHT_NORMAL),
            "small": (FontSystem.FAMILY_UI, FontSystem.SIZE_SM, FontSystem.WEIGHT_NORMAL),
            "tiny": (FontSystem.FAMILY_UI, FontSystem.SIZE_XS, FontSystem.WEIGHT_NORMAL),
            
            # Monospace/Code
            "code": (FontSystem.FAMILY_MONO, 11, FontSystem.WEIGHT_NORMAL),
            "code_large": (FontSystem.FAMILY_MONO, FontSystem.SIZE_BASE, FontSystem.WEIGHT_NORMAL),
            "code_small": (FontSystem.FAMILY_MONO, FontSystem.SIZE_SM, FontSystem.WEIGHT_NORMAL),
            
            # Tooltips
            "tooltip": (FontSystem.FAMILY_UI, FontSystem.SIZE_SM, FontSystem.WEIGHT_NORMAL),
            
            # Status Bar
            "statusbar": (FontSystem.FAMILY_UI, FontSystem.SIZE_SM, FontSystem.WEIGHT_NORMAL),
            
            # Toolbar
            "toolbar": (FontSystem.FAMILY_UI, FontSystem.SIZE_BASE, FontSystem.WEIGHT_NORMAL),
            
            # Properties Panel
            "property_label": (FontSystem.FAMILY_UI, FontSystem.SIZE_SM, FontSystem.WEIGHT_BOLD),
            "property_value": (FontSystem.FAMILY_UI, FontSystem.SIZE_SM, FontSystem.WEIGHT_NORMAL),
            
            # Palette
            "palette_title": (FontSystem.FAMILY_UI, FontSystem.SIZE_BASE, FontSystem.WEIGHT_BOLD),
            "palette_item": (FontSystem.FAMILY_UI, FontSystem.SIZE_SM, FontSystem.WEIGHT_NORMAL),
            
            # Canvas
            "canvas_label": (FontSystem.FAMILY_UI, 10, FontSystem.WEIGHT_NORMAL),
            "canvas_label_bold": (FontSystem.FAMILY_UI, 10, FontSystem.WEIGHT_BOLD),
            "ruler": (FontSystem.FAMILY_UI, 8, FontSystem.WEIGHT_NORMAL),
        }
    
    def get(self, font_name: str, default: Optional[Tuple[str, int, str]] = None) -> Tuple[str, int, str]:
        """
        Holt eine Schriftart.
        
        Args:
            font_name: Name der Schriftart
            default: Fallback-Schriftart falls nicht gefunden
            
        Returns:
            Font-Tupel (family, size, weight)
        """
        if default is None:
            default = (FontSystem.FAMILY_UI, FontSystem.SIZE_BASE, FontSystem.WEIGHT_NORMAL)
        
        # Erst in Custom-Fonts suchen
        if font_name in self._custom_fonts:
            return self._custom_fonts[font_name]
        
        # Dann in Standard-Fonts
        return self._fonts.get(font_name, default)
    
    def get_family(self, font_name: str) -> str:
        """
        Holt nur die Font-Familie.
        
        Args:
            font_name: Name der Schriftart
            
        Returns:
            Font-Familie als String
        """
        font = self.get(font_name)
        return font[0]
    
    def get_size(self, font_name: str) -> int:
        """
        Holt nur die Font-Größe.
        
        Args:
            font_name: Name der Schriftart
            
        Returns:
            Font-Größe als Integer
        """
        font = self.get(font_name)
        return font[1]
    
    def get_weight(self, font_name: str) -> str:
        """
        Holt nur das Font-Gewicht.
        
        Args:
            font_name: Name der Schriftart
            
        Returns:
            Font-Gewicht als String
        """
        font = self.get(font_name)
        return font[2]
    
    def set_custom(self, font_name: str, family: str, size: int, weight: str = "normal"):
        """
        Setzt eine benutzerdefinierte Schriftart.
        
        Args:
            font_name: Name der Schriftart
            family: Schriftfamilie
            size: Schriftgröße
            weight: Schriftgewicht
        """
        self._custom_fonts[font_name] = (family, size, weight)
    
    def reset_custom(self, font_name: str):
        """
        Setzt eine benutzerdefinierte Schriftart zurück.
        
        Args:
            font_name: Name der Schriftart
        """
        if font_name in self._custom_fonts:
            del self._custom_fonts[font_name]
    
    def get_all(self) -> Dict[str, Tuple[str, int, str]]:
        """
        Holt alle Schriftarten.
        
        Returns:
            Dictionary mit allen Font-Definitionen
        """
        result = self._fonts.copy()
        result.update(self._custom_fonts)
        return result
    
    def scale_size(self, font_name: str, factor: float) -> Tuple[str, int, str]:
        """
        Skaliert eine Schriftgröße.
        
        Args:
            font_name: Name der Schriftart
            factor: Skalierungsfaktor (z.B. 1.2 für 20% größer)
            
        Returns:
            Neues Font-Tupel mit skalierter Größe
        """
        family, size, weight = self.get(font_name)
        new_size = int(size * factor)
        return (family, new_size, weight)


# Globale Font-Manager-Instanz (Singleton-Pattern)
_global_font_manager: Optional[FontManager] = None


def get_font_manager() -> FontManager:
    """
    Holt die globale Font-Manager-Instanz.
    
    Returns:
        Globale FontManager-Instanz
    """
    global _global_font_manager
    if _global_font_manager is None:
        _global_font_manager = FontManager()
    return _global_font_manager


def get_font(font_name: str, default: Optional[Tuple[str, int, str]] = None) -> Tuple[str, int, str]:
    """
    Convenience-Funktion zum Holen einer Schriftart.
    
    Args:
        font_name: Name der Schriftart
        default: Fallback-Schriftart
        
    Returns:
        Font-Tupel
    """
    return get_font_manager().get(font_name, default)


__all__ = ["FontSystem", "FontManager", "get_font_manager", "get_font"]
