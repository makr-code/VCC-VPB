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
        document_service: DocumentService,
        recent_files_service=None,
        backup_service=None
    ):
        """
        Initialisiert den DocumentController.
        
        Args:
            event_bus: Event-Bus für Kommunikation
            document_service: Service für Document-Operationen
            recent_files_service: Service für Recent Files (optional)
            backup_service: Service für Backups (optional)
        """
        self.event_bus = event_bus
        self.document_service = document_service
        self.recent_files_service = recent_files_service
        self.backup_service = backup_service
        
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
        # Check for unsaved changes OR non-empty canvas
        has_unsaved_changes = self.is_modified or self._has_canvas_content()
        if has_unsaved_changes and not self._confirm_discard_changes():
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
        # Erstelle Backup des aktuellen Projekts, falls vorhanden und geändert
        if self.current_file_path and (self.is_modified or self._has_canvas_content()):
            self._create_backup_before_open()
        
        # Check for unsaved changes OR non-empty canvas
        has_unsaved_changes = self.is_modified or self._has_canvas_content()
        if has_unsaved_changes and not self._confirm_discard_changes():
            return

        # Get file path
        file_path = data.get("file_path")

        # Verhindere mehrfachen Dialog: Nur wenn kein file_path und kein Dialog bereits offen
        if not file_path:
            if getattr(self, '_open_dialog_active', False):
                return
            self._open_dialog_active = True
            self.event_bus.publish("ui:request:file_path", {
                "mode": "open",
                "callback": "document:open_file_selected"
            })
            return
        
        # Dialog wurde beantwortet, Flag zurücksetzen
        self._open_dialog_active = False
        
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
                
                # Validiere geladenes Projekt
                self._validate_loaded_document(data_dict)
                
                # Update window title
                self._update_window_title()
                
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
                
                # Update window title
                self._update_window_title()
                
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
        Fragt Benutzer, ob ungespeicherte Änderungen gespeichert werden sollen.
        Returns:
            True wenn Änderungen verworfen werden sollen, False sonst
        """
        try:
            from tkinter import messagebox
            result = messagebox.askyesnocancel(
                "Ungespeicherte Änderungen",
                "Das aktuelle Projekt wurde geändert. Möchten Sie die Änderungen speichern?"
            )
            if result is None:
                # Cancel - reset dialog flag
                self._open_dialog_active = False
                return False
            elif result:
                # Ja: Speichern
                self.event_bus.publish("ui:menu:file:save", {})
                return True
            else:
                # Nein: Verwerfen
                return True
        except Exception as e:
            print(f"⚠️ Fehler beim Anzeigen des Speichern-Dialogs: {e}")
            return True
    
    def _has_canvas_content(self) -> bool:
        """
        Prüft, ob das Canvas Inhalte hat (Elemente oder Verbindungen).
        Returns:
            True wenn Canvas nicht leer ist, False sonst
        """
        if not self._canvas:
            return False
        
        # Prüfe ob Canvas Elemente oder Verbindungen hat
        has_elements = (
            hasattr(self._canvas, 'elements') and 
            len(self._canvas.elements) > 0
        )
        has_connections = (
            hasattr(self._canvas, 'connections') and 
            len(self._canvas.connections) > 0
        )
        
        return has_elements or has_connections
    
    def _create_backup_before_open(self) -> None:
        """
        Erstellt ein Backup des aktuellen Projekts vor dem Öffnen eines neuen.
        """
        if not self.backup_service:
            return
        
        try:
            if self.current_file_path:
                # Backup der gespeicherten Datei
                self.backup_service.create_backup(self.current_file_path)
            elif self._canvas and hasattr(self._canvas, 'to_dict'):
                # Auto-Backup von ungespeicherten Änderungen
                canvas_data = self._canvas.to_dict()
                self.backup_service.create_auto_backup(None, canvas_data)
        except Exception as e:
            print(f"⚠️ Fehler beim Erstellen des Backups: {e}")
    
    def _validate_loaded_document(self, data_dict: dict) -> None:
        """
        Validiert ein geladenes Projekt und zeigt Warnungen/Fehler an.
        
        Args:
            data_dict: Geladene Projekt-Daten als Dictionary
        """
        try:
            issues = []
            
            # Prüfe ob erforderliche Felder vorhanden sind
            if "metadata" not in data_dict:
                issues.append("⚠️ Warnung: Keine Metadaten gefunden")
            
            if "elements" not in data_dict:
                issues.append("❌ Fehler: Keine Elemente gefunden")
            
            if "connections" not in data_dict:
                issues.append("⚠️ Warnung: Keine Verbindungen gefunden")
            
            # Prüfe Elementstruktur
            elements = data_dict.get("elements", [])
            if elements:
                for i, elem in enumerate(elements):
                    if not isinstance(elem, dict):
                        issues.append(f"❌ Fehler: Element {i} ist kein Dictionary")
                        continue
                    
                    # Prüfe erforderliche Element-Felder
                    required_fields = ["id", "type", "label"]
                    for field in required_fields:
                        if field not in elem:
                            issues.append(f"⚠️ Warnung: Element {i} fehlt Feld '{field}'")
            
            # Prüfe Verbindungsstruktur
            connections = data_dict.get("connections", [])
            if connections:
                element_ids = {elem.get("id") for elem in elements if isinstance(elem, dict)}
                for i, conn in enumerate(connections):
                    if not isinstance(conn, dict):
                        issues.append(f"❌ Fehler: Verbindung {i} ist kein Dictionary")
                        continue
                    
                    # Prüfe Verbindungs-Referenzen
                    from_id = conn.get("from")
                    to_id = conn.get("to")
                    
                    if from_id and from_id not in element_ids:
                        issues.append(f"⚠️ Warnung: Verbindung {i} referenziert unbekanntes Element '{from_id}'")
                    
                    if to_id and to_id not in element_ids:
                        issues.append(f"⚠️ Warnung: Verbindung {i} referenziert unbekanntes Element '{to_id}'")
            
            # Zeige Validierungsergebnisse
            if issues:
                self._show_validation_results(issues)
            else:
                print("✅ Projekt-Validierung: Keine Probleme gefunden")
                
        except Exception as e:
            print(f"⚠️ Fehler bei der Projekt-Validierung: {e}")
    
    def _show_validation_results(self, issues: list) -> None:
        """
        Zeigt Validierungsergebnisse in einem Dialog an.
        
        Args:
            issues: Liste der gefundenen Probleme
        """
        try:
            from tkinter import messagebox
            
            # Zähle Fehler und Warnungen
            errors = [issue for issue in issues if issue.startswith("❌")]
            warnings = [issue for issue in issues if issue.startswith("⚠️")]
            
            message = f"Projekt geladen, aber es wurden {len(issues)} Problem(e) gefunden:\n\n"
            
            if errors:
                message += f"Fehler ({len(errors)}):\n"
                for error in errors[:5]:  # Max 5 Fehler anzeigen
                    message += f"  • {error}\n"
                if len(errors) > 5:
                    message += f"  ... und {len(errors) - 5} weitere\n"
                message += "\n"
            
            if warnings:
                message += f"Warnungen ({len(warnings)}):\n"
                for warning in warnings[:5]:  # Max 5 Warnungen anzeigen
                    message += f"  • {warning}\n"
                if len(warnings) > 5:
                    message += f"  ... und {len(warnings) - 5} weitere\n"
            
            # Zeige Dialog
            if errors:
                messagebox.showwarning("Projekt-Validierung", message)
            else:
                messagebox.showinfo("Projekt-Validierung", message)
                
        except Exception as e:
            print(f"⚠️ Fehler beim Anzeigen der Validierungsergebnisse: {e}")
    
    def _update_window_title(self) -> None:
        """
        Aktualisiert den Fenstertitel mit dem aktuellen Dateinamen.
        """
        import os
        
        if self.current_file_path:
            filename = os.path.basename(self.current_file_path)
            modified_marker = " *" if self.is_modified else ""
            title = f"{filename}{modified_marker} - VPB Process Designer"
        else:
            modified_marker = " *" if self.is_modified else ""
            title = f"Unbenannt{modified_marker} - VPB Process Designer"
        
        # Publish event to update window title
        self.event_bus.publish("ui:window:title", {"title": title})
        
    def _add_to_recent_files(self, file_path: str):
        """
        Fügt Datei zu Recent Files hinzu.
        
        Args:
            file_path: Pfad zur Datei
        """
        if self.recent_files_service:
            self.recent_files_service.add_file(file_path)
            
        # Publish event für UI-Update
        self.event_bus.publish("document:recent_files_changed", {
            "recent_files": self.recent_files_service.get_recent_files() if self.recent_files_service else []
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
