"""
ValidationController
====================

Controller für Process Validation.

Responsibilities:
- Prozess-Validierung durchführen
- Compliance Checks
- Validierungsergebnisse anzeigen
- Fehler und Warnungen kommunizieren

Event Subscriptions:
- ui:menu:tools:validate
- ui:toolbar:validate
- document:created, document:loaded, document:closed

Event Publications:
- validation:started
- validation:completed (results)
- validation:failed (error)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from vpb.infrastructure.event_bus import EventBus
    from vpb.models import DocumentModel
    from vpb.services import ValidationService


class ValidationController:
    """
    Controller für Process Validation.
    
    Koordiniert Validierung zwischen UI und ValidationService.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        validation_service: Optional[ValidationService] = None,
        current_document: Optional[DocumentModel] = None
    ):
        """
        Initialisiert ValidationController.
        
        Args:
            event_bus: Event-Bus für Kommunikation
            validation_service: ValidationService (optional, wird lazy erstellt)
            current_document: Aktuelles Dokument (optional)
        """
        self.event_bus = event_bus
        self.validation_service = validation_service
        self.current_document = current_document
        
        # Subscribe to Events
        self._subscribe_to_events()
        
    def _subscribe_to_events(self) -> None:
        """Subscribe zu relevanten Events."""
        # Validation Events
        self.event_bus.subscribe("ui:menu:tools:validate", self._on_validate)
        self.event_bus.subscribe("ui:toolbar:validate", self._on_validate)
        
        # Document Events
        self.event_bus.subscribe("document:created", self._on_document_changed)
        self.event_bus.subscribe("document:loaded", self._on_document_changed)
        self.event_bus.subscribe("document:closed", self._on_document_closed)
        
    # ===== Event Handlers: Validation =====
    
    def _on_validate(self, data: Dict[str, Any]) -> None:
        """
        User startet Validierung.
        
        Args:
            data: Event-Daten (leer oder mit options)
        """
        if not self.current_document:
            self.event_bus.publish("validation:failed", {
                "error": "Kein Dokument geladen"
            })
            return
            
        # Status-Feedback
        self.event_bus.publish("ui:statusbar:message", {
            "text": "Validierung läuft...",
            "timeout": 0  # Stays until cleared
        })
        
        # Publish start event
        self.event_bus.publish("validation:started", {
            "document": self.current_document
        })
        
        try:
            # Perform validation
            results = self._validate_document()
            
            # Publish results
            self.event_bus.publish("validation:completed", {
                "results": results,
                "document": self.current_document
            })
            
            # Status-Feedback
            error_count = len(results.get("errors", []))
            warning_count = len(results.get("warnings", []))
            
            if error_count > 0:
                status_text = f"Validierung: {error_count} Fehler, {warning_count} Warnungen"
            elif warning_count > 0:
                status_text = f"Validierung: {warning_count} Warnungen"
            else:
                status_text = "Validierung erfolgreich ✓"
                
            self.event_bus.publish("ui:statusbar:message", {
                "text": status_text,
                "timeout": 5000
            })
            
        except Exception as e:
            # Publish error
            self.event_bus.publish("validation:failed", {
                "error": str(e)
            })
            
            # Status-Feedback
            self.event_bus.publish("ui:statusbar:message", {
                "text": f"Validierung fehlgeschlagen: {str(e)}",
                "timeout": 5000
            })
    
    def _validate_document(self) -> Dict[str, Any]:
        """
        Führt Validierung durch.
        
        Returns:
            Validierungsergebnisse mit errors, warnings, info
        """
        if not self.current_document:
            return {"errors": [], "warnings": [], "info": []}
        
        errors = []
        warnings = []
        info = []
        
        # Check: Mindestens 1 Element
        elements = self.current_document.get_all_elements()
        if len(elements) == 0:
            errors.append({
                "type": "NO_ELEMENTS",
                "message": "Prozess enthält keine Elemente",
                "severity": "error"
            })
        
        # Check: Mindestens 1 Connection (wenn mehr als 1 Element)
        connections = self.current_document.get_all_connections()
        if len(elements) > 1 and len(connections) == 0:
            warnings.append({
                "type": "NO_CONNECTIONS",
                "message": "Prozess enthält keine Verbindungen",
                "severity": "warning"
            })
        
        # Check: Element Names
        for elem in elements:
            if not elem.name or elem.name.strip() == "":
                warnings.append({
                    "type": "EMPTY_NAME",
                    "message": f"Element {elem.element_id[:8]}... hat keinen Namen",
                    "element_id": elem.element_id,
                    "severity": "warning"
                })
        
        # Check: Duplicate Names
        element_names = [e.name for e in elements if e.name]
        duplicate_names = [name for name in element_names if element_names.count(name) > 1]
        if duplicate_names:
            for name in set(duplicate_names):
                warnings.append({
                    "type": "DUPLICATE_NAME",
                    "message": f"Mehrere Elemente mit Name '{name}'",
                    "severity": "warning"
                })
        
        # Check: Disconnected Elements
        for elem in elements:
            # Check if element has any connections
            has_connection = any(
                c.source_element == elem.element_id or c.target_element == elem.element_id
                for c in connections
            )
            if not has_connection and len(elements) > 1:
                info.append({
                    "type": "DISCONNECTED",
                    "message": f"Element '{elem.name}' ist nicht verbunden",
                    "element_id": elem.element_id,
                    "severity": "info"
                })
        
        # Check: Invalid Connections (source/target not found)
        for conn in connections:
            source_elem = self.current_document.get_element(conn.source_element)
            target_elem = self.current_document.get_element(conn.target_element)
            
            if not source_elem:
                errors.append({
                    "type": "INVALID_CONNECTION",
                    "message": f"Verbindung {conn.connection_id[:8]}... hat ungültiges Quell-Element",
                    "connection_id": conn.connection_id,
                    "severity": "error"
                })
            
            if not target_elem:
                errors.append({
                    "type": "INVALID_CONNECTION",
                    "message": f"Verbindung {conn.connection_id[:8]}... hat ungültiges Ziel-Element",
                    "connection_id": conn.connection_id,
                    "severity": "error"
                })
        
        return {
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "element_count": len(elements),
            "connection_count": len(connections)
        }
    
    # ===== Document Lifecycle =====
    
    def _on_document_changed(self, data: Dict[str, Any]) -> None:
        """
        Neues Dokument erstellt oder geladen.
        
        Args:
            data: {"document": DocumentModel}
        """
        document = data.get("document")
        self.current_document = document
        
    def _on_document_closed(self, data: Dict[str, Any]) -> None:
        """
        Dokument geschlossen.
        
        Args:
            data: Event-Daten (leer)
        """
        self.current_document = None
        
    # ===== Public API =====
    
    def set_document(self, document: Optional[DocumentModel]) -> None:
        """
        Setzt das aktuelle Dokument.
        
        Args:
            document: DocumentModel oder None
        """
        self.current_document = document
        
    def validate(self) -> Dict[str, Any]:
        """
        Führt Validierung durch.
        
        Returns:
            Validierungsergebnisse
        """
        return self._validate_document()
        
    def get_validation_status(self) -> str:
        """
        Gibt Validierungsstatus zurück.
        
        Returns:
            Status-String ("valid", "warnings", "errors", "no_document")
        """
        if not self.current_document:
            return "no_document"
            
        results = self._validate_document()
        
        if len(results.get("errors", [])) > 0:
            return "errors"
        elif len(results.get("warnings", [])) > 0:
            return "warnings"
        else:
            return "valid"
    
    def __repr__(self) -> str:
        """String-Repräsentation."""
        doc_status = "with document" if self.current_document else "no document"
        
        if self.current_document:
            validation_status = self.get_validation_status()
            return f"<ValidationController({doc_status}, status={validation_status})>"
        else:
            return f"<ValidationController({doc_status})>"
