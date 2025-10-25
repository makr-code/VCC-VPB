"""
Element Controller für VPB Process Designer.

Koordiniert Element-CRUD Operationen:
- Element aus Palette hinzufügen
- Element per Click platzieren
- Element bearbeiten (Properties)
- Element löschen
- Element-Selection
- Element verschieben (Drag & Drop)

Subscribed Events:
- ui:palette:element_picked - Element aus Palette ausgewählt
- ui:canvas:left_click - Click auf Canvas (Element platzieren)
- ui:canvas:delete_key - Element löschen
- ui:properties:element_changed - Element-Properties geändert
- ui:canvas:element_selected - Element selektiert
- ui:menu:edit:delete - Element löschen via Menü

Published Events:
- element:created
- element:deleted
- element:modified
- element:selected
"""

from __future__ import annotations

from typing import Optional, Dict, Any

from vpb.infrastructure.event_bus import EventBus
from vpb.models import VPBElement, ElementFactory, DocumentModel


class ElementController:
    """
    Controller für Element-CRUD Operationen.
    
    Verantwortlich für:
    - Element-Erstellung aus Palette
    - Element-Platzierung auf Canvas
    - Element-Properties Editing
    - Element-Deletion
    - Element-Selection Management
    
    Attributes:
        event_bus (EventBus): Event-Bus für Kommunikation
        current_document (DocumentModel): Aktuelles Dokument
        selected_palette_item (Dict): Aktuell aus Palette gewähltes Element
        selected_element_id (str): ID des aktuell selektierten Elements
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        current_document: Optional[DocumentModel] = None
    ):
        """
        Initialisiert den ElementController.
        
        Args:
            event_bus: Event-Bus für Kommunikation
            current_document: Aktuelles Dokument (optional)
        """
        self.event_bus = event_bus
        self.current_document = current_document
        
        self.selected_palette_item: Optional[Dict[str, Any]] = None
        self.selected_element_id: Optional[str] = None
        self._canvas_ref = None  # Will be set from vpb_app.py
        
        # Subscribe to events
        self._subscribe_events()
        
    def set_canvas(self, canvas):
        """Setzt die Canvas-Referenz (wird von vpb_app.py aufgerufen)."""
        self._canvas_ref = canvas
        
    def _get_canvas(self):
        """Gibt die Canvas-Referenz zurück."""
        return self._canvas_ref
        
    def _subscribe_events(self):
        """Subscribed zu allen relevanten Events."""
        # Palette Events
        self.event_bus.subscribe("ui:palette:element_picked", self._on_palette_element_picked)
        
        # Canvas Events
        self.event_bus.subscribe("ui:canvas:left_click", self._on_canvas_click)
        self.event_bus.subscribe("ui:canvas:delete_key", self._on_delete_key)
        self.event_bus.subscribe("ui:canvas:element_selected", self._on_element_selected)
        
        # Properties Events
        self.event_bus.subscribe("ui:properties:element_changed", self._on_element_properties_changed)
        
        # Menu Events
        self.event_bus.subscribe("ui:menu:edit:delete", self._on_delete_key)
        
        # Document Events
        self.event_bus.subscribe("document:created", self._on_document_changed)
        self.event_bus.subscribe("document:loaded", self._on_document_changed)
        self.event_bus.subscribe("document:closed", self._on_document_closed)
        
    # ===== Event Handlers =====
    
    def _on_palette_element_picked(self, data: Dict[str, Any]):
        """
        Handler für Palette Element Picked Event.
        
        Args:
            data: Event-Daten mit 'item_data' (Element-Template)
        """
        item_data = data.get("item_data", {})
        self.selected_palette_item = item_data
        
        # Extract element info
        element_type = item_data.get("type", "FUNCTION")
        element_name = item_data.get("name", "Neues Element")
        
        # Check if this is a connection type (not an element)
        connection_types = [
            "SEQUENCE", "MESSAGE", "ASSOCIATION", "LEGAL", "APPROVAL", 
            "REJECTION", "DEADLINE", "ESCALATION", "DOCUMENT", 
            "NOTIFICATION", "GEO_REF"
        ]
        
        if element_type.upper() in connection_types:
            # This is a connection - delegate to ConnectionController
            self.event_bus.publish("ui:palette:connection_picked", {
                "connection_data": item_data
            })
            return
        
        # This is a regular element - start add mode on canvas
        from vpb.ui.canvas import VPBCanvas
        canvas = self._get_canvas()
        if canvas and isinstance(canvas, VPBCanvas):
            try:
                canvas.start_add_mode(element_type, default_name=element_name)
            except Exception:
                pass
        
        # Inform user via status bar
        self.event_bus.publish("ui:statusbar:message", {
            "message": f"{element_type} ausgewählt - Click auf Canvas zum Platzieren",
            "level": "info"
        })
        
    def _on_canvas_click(self, data: Dict[str, Any]):
        """
        Handler für Canvas Click Event.
        
        Args:
            data: Event-Daten mit 'x', 'y' Koordinaten
        """
        # Only create element if palette item is selected
        if not self.selected_palette_item or not self.current_document:
            return
            
        x = data.get("x", 0)
        y = data.get("y", 0)
        
        # Create element from palette template
        element_type = self.selected_palette_item.get("type", "ACTIVITY")
        
        # Use ElementFactory
        element = ElementFactory.create(
            element_type=element_type,
            x=x,
            y=y,
            name=self.selected_palette_item.get("name", "Neues Element")
        )
        
        # Add to document
        self.current_document.add_element(element)
        
        # Publish event
        self.event_bus.publish("element:created", {
            "element": element
        })
        
        # Clear palette selection
        self.selected_palette_item = None
        
        # Update status bar
        self.event_bus.publish("ui:statusbar:message", {
            "message": f"Element '{element.name}' erstellt",
            "level": "success"
        })
        
    def _on_delete_key(self, data: Dict[str, Any]):
        """
        Handler für Delete Key Event.
        
        Args:
            data: Event-Daten
        """
        if not self.selected_element_id or not self.current_document:
            return
            
        # Get element
        element = self.current_document.get_element(self.selected_element_id)
        if not element:
            return
            
        # Remove from document
        self.current_document.remove_element(self.selected_element_id)
        
        # Publish event
        self.event_bus.publish("element:deleted", {
            "element_id": self.selected_element_id,
            "element": element
        })
        
        # Clear selection
        self.selected_element_id = None
        
        # Update status bar
        self.event_bus.publish("ui:statusbar:message", {
            "message": f"Element '{element.name}' gelöscht",
            "level": "info"
        })
        
    def _on_element_selected(self, data: Dict[str, Any]):
        """
        Handler für Element Selected Event.
        
        Args:
            data: Event-Daten mit 'element_id'
        """
        element_id = data.get("element_id")
        self.selected_element_id = element_id
        
        if element_id and self.current_document:
            element = self.current_document.get_element(element_id)
            
            # Publish selection event
            self.event_bus.publish("element:selected", {
                "element_id": element_id,
                "element": element
            })
            
    def _on_element_properties_changed(self, data: Dict[str, Any]):
        """
        Handler für Element Properties Changed Event.
        
        Args:
            data: Event-Daten mit 'element' und 'values'
        """
        element = data.get("element")
        values = data.get("values", {})
        
        if not element or not self.current_document:
            return
            
        # Update element properties (alle Felder)
        if "name" in values:
            element.name = values["name"]
        if "description" in values:
            element.description = values["description"]
        if "element_type" in values:
            element.element_type = values["element_type"]
        if "responsible_authority" in values:
            element.responsible_authority = values["responsible_authority"]
        if "legal_basis" in values:
            element.legal_basis = values["legal_basis"]
        if "deadline_days" in values:
            try:
                element.deadline_days = int(values["deadline_days"])
            except (ValueError, TypeError):
                element.deadline_days = 0
        if "geo_reference" in values:
            element.geo_reference = values["geo_reference"]
        if "hierarchy" in values:
            element.hierarchy = values["hierarchy"]
        
        # GROUP-spezifische Properties
        if element.element_type == "GROUP":
            if "collapsed" in values:
                element.collapsed = bool(values["collapsed"])
            
        # Publish modified event
        self.event_bus.publish("element:modified", {
            "element_id": element.element_id,
            "element": element,
            "changes": values
        })
        
        # Update status bar
        self.event_bus.publish("ui:statusbar:message", {
            "message": f"Element '{element.name}' aktualisiert",
            "level": "success"
        })
        
    def _on_document_changed(self, data: Dict[str, Any]):
        """
        Handler für Document Changed Events.
        
        Args:
            data: Event-Daten mit 'document'
        """
        self.current_document = data.get("document")
        self.selected_element_id = None
        self.selected_palette_item = None
        
    def _on_document_closed(self, data: Dict[str, Any]):
        """
        Handler für Document Closed Event.
        
        Args:
            data: Event-Daten
        """
        self.current_document = None
        self.selected_element_id = None
        self.selected_palette_item = None
        
    # ===== Public API =====
    
    def set_document(self, document: Optional[DocumentModel]):
        """
        Setzt aktuelles Dokument.
        
        Args:
            document: DocumentModel oder None
        """
        self.current_document = document
        self.selected_element_id = None
        
    def get_selected_element_id(self) -> Optional[str]:
        """
        Gibt ID des selektierten Elements zurück.
        
        Returns:
            Element-ID oder None
        """
        return self.selected_element_id
        
    def get_selected_element(self) -> Optional[VPBElement]:
        """
        Gibt selektiertes Element zurück.
        
        Returns:
            VPBElement oder None
        """
        if not self.selected_element_id or not self.current_document:
            return None
            
        return self.current_document.get_element(self.selected_element_id)
        
    def clear_palette_selection(self):
        """Löscht Palette-Selection."""
        self.selected_palette_item = None
        
    def __repr__(self) -> str:
        doc_status = "with document" if self.current_document else "no document"
        sel_status = f"selected={self.selected_element_id}" if self.selected_element_id else "no selection"
        return f"<ElementController {doc_status}, {sel_status}>"
