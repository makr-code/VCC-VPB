"""
Document Controller für VPB Process Designer.

Orchestriert den Document-Lifecycle:
- Neues Dokument erstellen
- Dokument öffnen/laden
- Dokument speichern
- Dokument schließen
- Unsaved Changes Detection
- Recent Files Management

Subscribed Events:
- ui:menu:file:new, ui:toolbar:new
- ui:menu:file:open
- ui:menu:file:save, ui:toolbar:save
- ui:menu:file:save_as
- ui:menu:file:close
- ui:window:closing

Published Events:
- document:created
- document:loaded
- document:saved
- document:closed
- document:modified
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any
from pathlib import Path

from vpb.infrastructure.event_bus import EventBus
from vpb.services.document_service import DocumentService
from vpb.models import DocumentModel


class DocumentController:
    """
    Controller für Document-Lifecycle.
    
    Verantwortlich für:
    - Document CRUD Operationen
    - File I/O Koordination
    - Unsaved Changes Detection
    - Recent Files
    
    Attributes:
        event_bus (EventBus): Event-Bus für Kommunikation
        document_service (DocumentService): Service für Document-Operationen
        current_document (DocumentModel): Aktuell geöffnetes Dokument
        current_file_path (str): Pfad zur aktuellen Datei
        is_modified (bool): Unsaved Changes Flag
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        document_service: DocumentService
    ):
        """
        Initialisiert den DocumentController.
        
        Args:
            event_bus: Event-Bus für Kommunikation
            document_service: Service für Document-Operationen
        """
        self.event_bus = event_bus
        self.document_service = document_service
        
        self.current_document: Optional[DocumentModel] = None
        self.current_file_path: Optional[str] = None
        self.is_modified: bool = False
        self._canvas = None  # Legacy Canvas-Referenz
        
        # Subscribe to events
        self._subscribe_events()
    
    def set_canvas(self, canvas):
        """Setzt Canvas-Referenz für Legacy-Kompatibilität."""
        self._canvas = canvas
        
    def _subscribe_events(self):
        """Subscribed zu allen relevanten Events."""
        # File Menu Events
        self.event_bus.subscribe("ui:menu:file:new", self._on_new_document)
        self.event_bus.subscribe("ui:menu:file:open", self._on_open_document)
        self.event_bus.subscribe("ui:menu:file:save", self._on_save_document)
        self.event_bus.subscribe("ui:menu:file:save_as", self._on_save_document_as)
        self.event_bus.subscribe("ui:menu:file:close", self._on_close_document)
        
        # Toolbar Events
        self.event_bus.subscribe("ui:toolbar:new", self._on_new_document)
        self.event_bus.subscribe("ui:toolbar:open", self._on_open_document)
        self.event_bus.subscribe("ui:toolbar:save", self._on_save_document)
        
        # File Dialog Callbacks
        self.event_bus.subscribe("document:open_file_selected", self._on_open_document)
        self.event_bus.subscribe("document:save_file_selected", self._on_save_document_as)
        
        # Window Events
        self.event_bus.subscribe("ui:window:closing", self._on_window_closing)
        
        # Document Modification Events
        self.event_bus.subscribe("document:element_added", self._on_document_modified)
        self.event_bus.subscribe("document:element_removed", self._on_document_modified)
        self.event_bus.subscribe("document:element_modified", self._on_document_modified)
        self.event_bus.subscribe("document:connection_added", self._on_document_modified)
        self.event_bus.subscribe("document:connection_removed", self._on_document_modified)
        
    # ===== Event Handlers =====
    
    def _on_new_document(self, data: Dict[str, Any]):
        """
        Handler für New Document Event.
        
        Args:
            data: Event-Daten
        """
        # Check for unsaved changes
        if self.is_modified and not self._confirm_discard_changes():
            return
        
        # Legacy: Canvas direkt clearen
        if self._canvas and hasattr(self._canvas, 'clear_all'):
            self._canvas.clear_all()
        
        # Create new document (für Metadaten)
        self.current_document = self.document_service.create_new_document()
        self.current_file_path = None
        self.is_modified = False
        
        # Publish event
        self.event_bus.publish("document:created", {
            "document": self.current_document
        })
        
        # Update Status
        self.event_bus.publish("ui:statusbar:message", {
            "message": "Neues Dokument erstellt",
            "level": "info"
        })
        
    def _on_open_document(self, data: Dict[str, Any]):
        """
        Handler für Open Document Event.
        
        Args:
            data: Event-Daten (kann 'file_path' enthalten)
        """
        # Check for unsaved changes
        if self.is_modified and not self._confirm_discard_changes():
            return
            
        # Get file path
        file_path = data.get("file_path")
        
        if not file_path:
            # Request file path via dialog
            self.event_bus.publish("ui:request:file_path", {
                "mode": "open",
                "callback": "document:open_file_selected"
            })
            return
        
        # Legacy: Direkt in Canvas laden
        if self._canvas and hasattr(self._canvas, 'load_from_dict'):
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data_dict = json.load(f)
                
                self._canvas.load_from_dict(data_dict)
                self.current_file_path = file_path
                self.is_modified = False
                
                # Publish event
                self.event_bus.publish("document:loaded", {
                    "document": None,  # Legacy: Kein DocumentModel
                    "file_path": file_path
                })
                
                # Update Status
                self.event_bus.publish("ui:statusbar:message", {
                    "message": f"Geladen: {file_path}",
                    "level": "success"
                })
                
                # Add to recent files
                self._add_to_recent_files(file_path)
                
            except Exception as e:
                self.event_bus.publish("ui:error", {
                    "message": f"Fehler beim Laden: {str(e)}"
                })
                return
        
        # Fallback: DocumentService (refactored)
        try:
            self.current_document = self.document_service.load_document(file_path)
            self.current_file_path = file_path
            self.is_modified = False
            
            # Publish event
            self.event_bus.publish("document:loaded", {
                "document": self.current_document,
                "file_path": file_path
            })
            
            # Add to recent files
            self._add_to_recent_files(file_path)
            
        except Exception as e:
            self.event_bus.publish("ui:error", {
                "message": f"Fehler beim Laden: {str(e)}"
            })
            
    def _on_save_document(self, data: Dict[str, Any]):
        """
        Handler für Save Document Event.
        
        Args:
            data: Event-Daten
        """
        # If no file path, do Save As
        if not self.current_file_path:
            self._on_save_document_as(data)
            return
        
        # Legacy: Direkt aus Canvas speichern
        if self._canvas and hasattr(self._canvas, 'to_dict'):
            try:
                import json
                data_dict = self._canvas.to_dict()
                
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_dict, f, indent=2, ensure_ascii=False)
                
                self.is_modified = False
                
                # Publish event
                self.event_bus.publish("document:saved", {
                    "document": None,  # Legacy: Kein DocumentModel
                    "file_path": self.current_file_path
                })
                
                # Update Status
                self.event_bus.publish("ui:statusbar:message", {
                    "message": f"Gespeichert: {self.current_file_path}",
                    "level": "success"
                })
                
            except Exception as e:
                self.event_bus.publish("ui:error", {
                    "message": f"Fehler beim Speichern: {str(e)}"
                })
            return
        
        # Fallback: DocumentService (refactored)
        if not self.current_document:
            return
            
        try:
            self.document_service.save_document(
                self.current_document,
                self.current_file_path
            )
            self.is_modified = False
            
            # Publish event
            self.event_bus.publish("document:saved", {
                "document": self.current_document,
                "file_path": self.current_file_path
            })
            
        except Exception as e:
            self.event_bus.publish("ui:error", {
                "message": f"Fehler beim Speichern: {str(e)}"
            })
            
    def _on_save_document_as(self, data: Dict[str, Any]):
        """
        Handler für Save Document As Event.
        
        Args:
            data: Event-Daten (kann 'file_path' enthalten)
        """
        # Get file path
        file_path = data.get("file_path")
        
        if not file_path:
            # Request file path via dialog
            self.event_bus.publish("ui:request:file_path", {
                "mode": "save",
                "callback": "document:save_file_selected"
            })
            return
        
        # Legacy: Direkt aus Canvas speichern
        if self._canvas and hasattr(self._canvas, 'to_dict'):
            try:
                import json
                data_dict = self._canvas.to_dict()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_dict, f, indent=2, ensure_ascii=False)
                
                self.current_file_path = file_path
                self.is_modified = False
                
                # Publish event
                self.event_bus.publish("document:saved", {
                    "document": None,  # Legacy: Kein DocumentModel
                    "file_path": file_path
                })
                
                # Update Status
                self.event_bus.publish("ui:statusbar:message", {
                    "message": f"Gespeichert: {file_path}",
                    "level": "success"
                })
                
                # Add to recent files
                self._add_to_recent_files(file_path)
                
            except Exception as e:
                self.event_bus.publish("ui:error", {
                    "message": f"Fehler beim Speichern: {str(e)}"
                })
            return
        
        # Fallback: DocumentService (refactored)
        if not self.current_document:
            return
            
        # Save document
        try:
            self.document_service.save_document(
                self.current_document,
                file_path
            )
            self.current_file_path = file_path
            self.is_modified = False
            
            # Publish event
            self.event_bus.publish("document:saved", {
                "document": self.current_document,
                "file_path": file_path
            })
            
            # Add to recent files
            self._add_to_recent_files(file_path)
            
        except Exception as e:
            self.event_bus.publish("ui:error", {
                "message": f"Fehler beim Speichern: {str(e)}"
            })
            
    def _on_close_document(self, data: Dict[str, Any]):
        """
        Handler für Close Document Event.
        
        Args:
            data: Event-Daten
        """
        # Check for unsaved changes
        if self.is_modified and not self._confirm_discard_changes():
            return
            
        # Close document
        self.current_document = None
        self.current_file_path = None
        self.is_modified = False
        
        # Publish event
        self.event_bus.publish("document:closed", {})
        
    def _on_window_closing(self, data: Dict[str, Any]):
        """
        Handler für Window Closing Event.
        
        Args:
            data: Event-Daten
        """
        # Check for unsaved changes
        if self.is_modified and not self._confirm_discard_changes():
            # Cancel window close
            self.event_bus.publish("ui:cancel_close", {})
            
    def _on_document_modified(self, data: Dict[str, Any]):
        """
        Handler für Document Modified Events.
        
        Args:
            data: Event-Daten
        """
        if self.current_document:
            self.is_modified = True
            
            # Publish modified event
            self.event_bus.publish("document:modified", {
                "is_modified": True
            })
            
    # ===== Helper Methods =====
    
    def _confirm_discard_changes(self) -> bool:
        """
        Fragt Benutzer ob ungespeicherte Änderungen verworfen werden sollen.
        
        Returns:
            True wenn Änderungen verworfen werden sollen, False sonst
        """
        # Request confirmation via dialog
        # For now, return True (later: implement dialog)
        return True
        
    def _add_to_recent_files(self, file_path: str):
        """
        Fügt Datei zu Recent Files hinzu.
        
        Args:
            file_path: Pfad zur Datei
        """
        self.event_bus.publish("document:add_to_recent", {
            "file_path": file_path
        })
        
    # ===== Public API =====
    
    def get_current_document(self) -> Optional[DocumentModel]:
        """
        Gibt aktuelles Dokument zurück.
        
        Returns:
            Aktuelles DocumentModel oder None
        """
        return self.current_document
        
    def get_current_file_path(self) -> Optional[str]:
        """
        Gibt aktuellen Dateipfad zurück.
        
        Returns:
            Dateipfad oder None
        """
        return self.current_file_path
        
    def is_document_modified(self) -> bool:
        """
        Prüft ob Dokument ungespeicherte Änderungen hat.
        
        Returns:
            True wenn modifiziert, False sonst
        """
        return self.is_modified
        
    def __repr__(self) -> str:
        doc_name = Path(self.current_file_path).name if self.current_file_path else "Unbenannt"
        modified = "*" if self.is_modified else ""
        return f"<DocumentController document={doc_name}{modified}>"
