"""
Properties View für Element- und Verbindungs-Eigenschaften.

Diese View ist verantwortlich für:
- Anzeige und Bearbeitung von Element-Eigenschaften
- Anzeige und Bearbeitung von Verbindungs-Eigenschaften
- Formular-Felder (Name, Typ, Beschreibung, etc.)
- Validation (über ValidationService)
- Apply/Reset-Buttons

Alle Änderungen werden über den Event-Bus publiziert.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, Optional

from vpb.models import VPBElement, VPBConnection
from vpb.infrastructure.event_bus import get_global_event_bus, EventBus
from vpb.ui.properties_panel import PropertiesPanel


class PropertiesView(tk.Frame):
    """
    Properties View für Element- und Verbindungs-Eigenschaften.
    
    Diese View wrapped die bestehende PropertiesPanel-Implementierung
    und fügt Event-Bus-Integration hinzu.
    
    Attributes:
        properties_panel (PropertiesPanel): Das eigentliche Properties-Widget
        event_bus (EventBus): Event-Bus für Kommunikation
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        event_bus: Optional[EventBus] = None,
        width: int = 360,
        **kwargs
    ):
        """
        Initialisiert die Properties View.
        
        Args:
            parent: Parent Widget
            event_bus: Event-Bus für Kommunikation (optional)
            width: Breite des Properties-Panels
            **kwargs: Zusätzliche Frame-Optionen
        """
        super().__init__(parent, **kwargs)
        
        self.event_bus = event_bus or get_global_event_bus()
        self._width = width
        self._current_element: Optional[VPBElement] = None
        self._current_connection: Optional[VPBConnection] = None
        
        # Create properties panel with callbacks
        self.properties_panel = PropertiesPanel(
            self,
            on_apply=self._on_apply,
            resolve_member_label=self._resolve_member_label,
            on_member_select=self._on_member_select,
            on_group_add=self._on_group_add,
            on_group_remove=self._on_group_remove
        )
        self.properties_panel.pack(fill=tk.BOTH, expand=True)
        
    def _on_apply(self, values: Dict[str, object]):
        """
        Callback wenn Apply-Button geklickt wurde.
        
        Args:
            values: Dictionary mit geänderten Werten
        """
        kind = values.get("kind", "element")  # Default to "element"
        
        if kind == "element":
            self.event_bus.publish("ui:properties:element_changed", {
                "element": self._current_element,
                "values": values
            })
        elif kind == "connection":
            self.event_bus.publish("ui:properties:connection_changed", {
                "connection": self._current_connection,
                "values": values
            })
        elif kind == "hierarchy":
            self.event_bus.publish("ui:properties:hierarchy_changed", {
                "values": values
            })
            
    def _resolve_member_label(self, element_id: str) -> str:
        """
        Resolves Element-ID zu Label.
        
        Args:
            element_id: Element-ID
            
        Returns:
            Label für Element
        """
        # Publish request for label resolution
        # For now, return element_id as fallback
        return element_id
        
    def _on_member_select(self, element_id: str):
        """
        Callback wenn Group-Member ausgewählt wurde.
        
        Args:
            element_id: Element-ID des ausgewählten Members
        """
        self.event_bus.publish("ui:properties:member_selected", {
            "element_id": element_id
        })
        
    def _on_group_add(self, group_id: str):
        """
        Callback wenn Element zu Gruppe hinzugefügt werden soll.
        
        Args:
            group_id: Gruppen-ID
        """
        self.event_bus.publish("ui:properties:group_add_requested", {
            "group_id": group_id
        })
        
    def _on_group_remove(self, group_id: str):
        """
        Callback wenn Element aus Gruppe entfernt werden soll.
        
        Args:
            group_id: Gruppen-ID
        """
        self.event_bus.publish("ui:properties:group_remove_requested", {
            "group_id": group_id
        })
        
    # ===== Public API =====
    
    def set_element(self, element: Optional[VPBElement]):
        """
        Setzt das anzuzeigende Element.
        
        Args:
            element: VPBElement oder None
        """
        self._current_element = element
        self._current_connection = None
        self.properties_panel.set_element(element)
        
    def set_connection(self, connection: Optional[VPBConnection]):
        """
        Setzt die anzuzeigende Verbindung.
        
        Args:
            connection: VPBConnection oder None
        """
        self._current_element = None
        self._current_connection = connection
        self.properties_panel.set_element(None, connection)
        
    def set_hierarchy(self, index: Optional[int], data: Optional[Dict[str, object]]):
        """
        Setzt die anzuzeigende Hierarchie-Kategorie.
        
        Args:
            index: Index der Hierarchie-Kategorie
            data: Hierarchie-Daten
        """
        self._current_element = None
        self._current_connection = None
        self.properties_panel.set_hierarchy(index, data)
        
    def clear(self):
        """Löscht alle Anzeigen."""
        self._current_element = None
        self._current_connection = None
        self.properties_panel.set_element(None)
        
    def get_current_element(self) -> Optional[VPBElement]:
        """
        Gibt das aktuell angezeigte Element zurück.
        
        Returns:
            VPBElement oder None
        """
        return self._current_element
        
    def get_current_connection(self) -> Optional[VPBConnection]:
        """
        Gibt die aktuell angezeigte Verbindung zurück.
        
        Returns:
            VPBConnection oder None
        """
        return self._current_connection
        
    def refresh_hierarchy_options(self, names: list[str]):
        """
        Aktualisiert Hierarchie-Optionen.
        
        Args:
            names: Liste von Hierarchie-Namen
        """
        self.properties_panel.refresh_hierarchy_options(names)
        
    def __repr__(self) -> str:
        if self._current_element:
            return f"<PropertiesView mode=element element_id={self._current_element.element_id}>"
        elif self._current_connection:
            return f"<PropertiesView mode=connection connection_id={self._current_connection.connection_id}>"
        else:
            return "<PropertiesView mode=empty>"


# ===== Factory Function =====

def create_properties_view(
    parent: tk.Widget,
    event_bus: Optional[EventBus] = None,
    width: int = 360,
    **kwargs
) -> PropertiesView:
    """
    Factory-Funktion zum Erstellen einer Properties View.
    
    Args:
        parent: Parent Widget
        event_bus: Event-Bus für Kommunikation
        width: Breite des Properties-Panels
        **kwargs: Zusätzliche Frame-Optionen
        
    Returns:
        Neue PropertiesView-Instanz
    """
    return PropertiesView(parent, event_bus=event_bus, width=width, **kwargs)
