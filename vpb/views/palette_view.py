"""
Palette View für Element-Auswahl mit Drag & Drop.

Diese View ist verantwortlich für:
- Anzeige von Element-Kategorien (Activities, Decisions, Events, etc.)
- Element-Auswahl per Klick
- Drag & Drop Support (über Event-Bus)
- Filter/Suche
- Collapsible Kategorien
- Element-Icons (emoji-basiert)
- Tooltips für Elemente

Alle Events werden über den Event-Bus publiziert.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, List, Optional

from vpb.infrastructure.event_bus import get_global_event_bus, EventBus
from vpb.ui.palette_panel import PalettePanel, PaletteLoader


class PaletteView(tk.Frame):
    """
    Palette View für Element-Auswahl.
    
    Diese View wrapped die bestehende PalettePanel-Implementierung
    und fügt Event-Bus-Integration hinzu.
    
    Attributes:
        palette_panel (PalettePanel): Das eigentliche Palette-Widget
        event_bus (EventBus): Event-Bus für Kommunikation
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        event_bus: Optional[EventBus] = None,
        width: int = 220,
        **kwargs
    ):
        """
        Initialisiert die Palette View.
        
        Args:
            parent: Parent Widget
            event_bus: Event-Bus für Kommunikation (optional)
            width: Breite der Palette
            **kwargs: Zusätzliche Frame-Optionen
        """
        super().__init__(parent, **kwargs)
        
        self.event_bus = event_bus or get_global_event_bus()
        self._width = width
        self._current_categories: List[Dict] = []
        
        # Create palette panel with callbacks
        self.palette_panel = PalettePanel(
            self,
            on_pick=self._on_element_picked,
            on_reload=self._on_reload_requested
        )
        self.palette_panel.pack(fill=tk.BOTH, expand=True)
        
    def _on_element_picked(self, item: Dict):
        """
        Callback wenn Element aus Palette gewählt wurde.
        
        Args:
            item: Element-Dictionary mit type, label, etc.
        """
        # Publish element picked event
        element_type = item.get("type", "")
        label = item.get("label", "")
        
        self.event_bus.publish("ui:palette:element_picked", {
            "type": element_type,
            "label": label,
            "item": item
        })
        
    def _on_reload_requested(self):
        """Callback wenn Palette-Reload angefordert wurde."""
        self.event_bus.publish("ui:palette:reload_requested", {})
        
    # ===== Public API =====
    
    def load_categories(self, categories: List[Dict]):
        """
        Lädt Kategorien in die Palette.
        
        Args:
            categories: Liste von Kategorie-Dictionaries
        """
        self._current_categories = categories
        self.palette_panel.render(categories)
        
    def load_from_folder(self, folder_path: str):
        """
        Lädt Paletten aus einem Ordner.
        
        Args:
            folder_path: Pfad zum Paletten-Ordner
        """
        data = PaletteLoader.load_all(folder_path)
        categories = data.get("categories", [])
        self.load_categories(categories)
        
    def get_categories(self) -> List[Dict]:
        """
        Gibt aktuelle Kategorien zurück.
        
        Returns:
            Liste von Kategorie-Dictionaries
        """
        return self._current_categories.copy()
        
    def expand_all_categories(self):
        """Expandiert alle Kategorien."""
        self.palette_panel._expand_all_categories()
        
    def collapse_all_categories(self):
        """Kollabiert alle Kategorien."""
        self.palette_panel._collapse_all_categories()
        
    def set_search_filter(self, query: str):
        """
        Setzt Such-Filter.
        
        Args:
            query: Such-Query
        """
        try:
            self.palette_panel._search.set(query)
            self.palette_panel._apply_filter()
        except AttributeError:
            pass
            
    def clear_search_filter(self):
        """Löscht Such-Filter."""
        self.set_search_filter("")
        
    def get_search_filter(self) -> str:
        """
        Gibt aktuellen Such-Filter zurück.
        
        Returns:
            Such-Query String
        """
        try:
            return self.palette_panel._search.get()
        except AttributeError:
            return ""
            
    def reload(self):
        """Triggert Palette-Reload."""
        self._on_reload_requested()
        
    def __repr__(self) -> str:
        return f"<PaletteView categories={len(self._current_categories)}>"


# ===== Factory Function =====

def create_palette_view(
    parent: tk.Widget,
    event_bus: Optional[EventBus] = None,
    width: int = 220,
    **kwargs
) -> PaletteView:
    """
    Factory-Funktion zum Erstellen einer Palette View.
    
    Args:
        parent: Parent Widget
        event_bus: Event-Bus für Kommunikation
        width: Breite der Palette
        **kwargs: Zusätzliche Frame-Optionen
        
    Returns:
        Neue PaletteView-Instanz
    """
    return PaletteView(parent, event_bus=event_bus, width=width, **kwargs)
