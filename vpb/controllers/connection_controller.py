"""
ConnectionController
====================

Controller für Connection CRUD Operations.

Responsibilities:
- Connection erstellen (Drag von Element zu Element)
- Connection löschen
- Connection Properties bearbeiten
- Routing Mode ändern
- Arrow Style ändern

Event Subscriptions:
- ui:canvas:connection_start (start_element_id)
- ui:canvas:connection_end (end_element_id)
- ui:canvas:delete_key
- ui:properties:connection_changed
- ui:menu:edit:delete
- document:created, document:loaded, document:closed

Event Publications:
- connection:created (connection)
- connection:deleted (connection_id, connection)
- connection:modified (connection_id, connection, changes)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from vpb.infrastructure.event_bus import EventBus
    from vpb.models import DocumentModel, VPBConnection

from vpb.models import ConnectionFactory


class ConnectionController:
    """
    Controller für Connection Management.
    
    Koordiniert Connection CRUD zwischen Views und Models.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        current_document: Optional[DocumentModel] = None
    ):
        """
        Initialisiert ConnectionController.
        
        Args:
            event_bus: Event-Bus für Kommunikation
            current_document: Aktuelles Dokument (optional)
        """
        self.event_bus = event_bus
        self.current_document = current_document
        
        # State für Connection-Creation
        self.connection_start_element_id: Optional[str] = None
        self.selected_connection_id: Optional[str] = None
        
        # Subscribe to Events
        self._subscribe_to_events()
        
    def _subscribe_to_events(self) -> None:
        """Subscribe zu relevanten Events."""
        # Canvas Events
        self.event_bus.subscribe("ui:canvas:connection_start", self._on_connection_start)
        self.event_bus.subscribe("ui:canvas:connection_end", self._on_connection_end)
        self.event_bus.subscribe("ui:canvas:delete_key", self._on_delete_key)
        self.event_bus.subscribe("ui:canvas:connection_selected", self._on_connection_selected)
        
        # Properties Events
        self.event_bus.subscribe("ui:properties:connection_changed", self._on_connection_properties_changed)
        
        # Menu Events
        self.event_bus.subscribe("ui:menu:edit:delete", self._on_delete_key)
        
        # Document Events
        self.event_bus.subscribe("document:created", self._on_document_changed)
        self.event_bus.subscribe("document:loaded", self._on_document_changed)
        self.event_bus.subscribe("document:closed", self._on_document_closed)
        
    # ===== Event Handlers: Connection Creation =====
    
    def _on_connection_start(self, data: Dict[str, Any]) -> None:
        """
        User startet Connection von einem Element.
        
        Args:
            data: {"start_element_id": str}
        """
        start_element_id = data.get("start_element_id")
        
        if not start_element_id:
            return
            
        self.connection_start_element_id = start_element_id
        
        # Status-Feedback
        self.event_bus.publish("ui:statusbar:message", {
            "text": f"Verbindung starten von Element {start_element_id[:8]}...",
            "timeout": 3000
        })
        
    def _on_connection_end(self, data: Dict[str, Any]) -> None:
        """
        User beendet Connection auf einem Element.
        
        Args:
            data: {"end_element_id": str}
        """
        end_element_id = data.get("end_element_id")
        
        if not self.connection_start_element_id or not end_element_id:
            return
            
        if not self.current_document:
            return
            
        # Verhindere Self-Connections
        if self.connection_start_element_id == end_element_id:
            self.connection_start_element_id = None
            return
            
        # Create Connection
        connection = ConnectionFactory.create(
            source_element=self.connection_start_element_id,
            target_element=end_element_id
        )
        
        self.current_document.add_connection(connection)
        
        # Publish Event
        self.event_bus.publish("connection:created", {"connection": connection})
        
        # Status-Feedback
        self.event_bus.publish("ui:statusbar:message", {
            "text": f"Verbindung erstellt: {connection.connection_id[:8]}...",
            "timeout": 3000
        })
        
        # Reset state
        self.connection_start_element_id = None
        
    # ===== Event Handlers: Connection Deletion =====
    
    def _on_delete_key(self, data: Dict[str, Any]) -> None:
        """
        User drückt Delete-Taste (oder Menu Delete).
        
        Args:
            data: Event-Daten (leer)
        """
        if not self.selected_connection_id:
            return
            
        if not self.current_document:
            return
            
        # Get connection before deletion
        connection = self.current_document.get_connection(self.selected_connection_id)
        
        if not connection:
            return
            
        # Remove connection
        self.current_document.remove_connection(self.selected_connection_id)
        
        # Publish Event
        self.event_bus.publish("connection:deleted", {
            "connection_id": self.selected_connection_id,
            "connection": connection
        })
        
        # Status-Feedback
        self.event_bus.publish("ui:statusbar:message", {
            "text": f"Verbindung gelöscht: {self.selected_connection_id[:8]}...",
            "timeout": 3000
        })
        
        # Clear selection
        self.selected_connection_id = None
        
    # ===== Event Handlers: Connection Selection =====
    
    def _on_connection_selected(self, data: Dict[str, Any]) -> None:
        """
        User selektiert Connection auf Canvas.
        
        Args:
            data: {"connection_id": str}
        """
        connection_id = data.get("connection_id")
        
        self.selected_connection_id = connection_id
        
        # Get connection
        connection = None
        if self.current_document and connection_id:
            connection = self.current_document.get_connection(connection_id)
        
        # Publish Event
        self.event_bus.publish("connection:selected", {
            "connection_id": connection_id,
            "connection": connection
        })
        
    # ===== Event Handlers: Connection Properties =====
    
    def _on_connection_properties_changed(self, data: Dict[str, Any]) -> None:
        """
        User ändert Connection Properties.
        
        Args:
            data: {"connection": VPBConnection, "values": dict}
        """
        connection = data.get("connection")
        values = data.get("values", {})
        
        if not connection:
            return
            
        # Track changes
        changes = {}
        
        # Update properties
        if "description" in values:
            old_desc = connection.description
            connection.description = values["description"]
            if old_desc != connection.description:
                changes["description"] = {"old": old_desc, "new": connection.description}
                
        if "connection_type" in values:
            old_type = connection.connection_type
            connection.connection_type = values["connection_type"]
            if old_type != connection.connection_type:
                changes["connection_type"] = {"old": old_type, "new": connection.connection_type}
                
        if "routing_mode" in values:
            old_mode = connection.routing_mode
            connection.routing_mode = values["routing_mode"]
            if old_mode != connection.routing_mode:
                changes["routing_mode"] = {"old": old_mode, "new": connection.routing_mode}
                
        if "arrow_style" in values:
            old_style = connection.arrow_style
            connection.arrow_style = values["arrow_style"]
            if old_style != connection.arrow_style:
                changes["arrow_style"] = {"old": old_style, "new": connection.arrow_style}
        
        # Publish Event if changes
        if changes:
            self.event_bus.publish("connection:modified", {
                "connection_id": connection.connection_id,
                "connection": connection,
                "changes": changes
            })
        
    # ===== Event Handlers: Document Lifecycle =====
    
    def _on_document_changed(self, data: Dict[str, Any]) -> None:
        """
        Neues Dokument erstellt oder geladen.
        
        Args:
            data: {"document": DocumentModel}
        """
        document = data.get("document")
        self.current_document = document
        
        # Clear state
        self.connection_start_element_id = None
        self.selected_connection_id = None
        
    def _on_document_closed(self, data: Dict[str, Any]) -> None:
        """
        Dokument geschlossen.
        
        Args:
            data: Event-Daten (leer)
        """
        self.current_document = None
        self.connection_start_element_id = None
        self.selected_connection_id = None
        
    # ===== Public API =====
    
    def set_document(self, document: Optional[DocumentModel]) -> None:
        """
        Setzt das aktuelle Dokument.
        
        Args:
            document: DocumentModel oder None
        """
        self.current_document = document
        self.connection_start_element_id = None
        self.selected_connection_id = None
        
    def get_selected_connection_id(self) -> Optional[str]:
        """
        Gibt die ID der selektierten Connection zurück.
        
        Returns:
            Connection ID oder None
        """
        return self.selected_connection_id
        
    def get_selected_connection(self) -> Optional[VPBConnection]:
        """
        Gibt die selektierte Connection zurück.
        
        Returns:
            VPBConnection oder None
        """
        if not self.selected_connection_id or not self.current_document:
            return None
            
        return self.current_document.get_connection(self.selected_connection_id)
        
    def cancel_connection_creation(self) -> None:
        """Bricht Connection-Creation ab."""
        self.connection_start_element_id = None
        
    def __repr__(self) -> str:
        """String-Repräsentation."""
        doc_status = "with document" if self.current_document else "no document"
        sel_status = f"selected={self.selected_connection_id[:8]}..." if self.selected_connection_id else "no selection"
        start_status = f"start={self.connection_start_element_id[:8]}..." if self.connection_start_element_id else "no start"
        return f"<ConnectionController({doc_status}, {sel_status}, {start_status})>"
