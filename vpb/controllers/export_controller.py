"""
ExportController
================

Controller für Export Funktionalität.

Responsibilities:
- Export zu verschiedenen Formaten (PNG, SVG, PDF, XML)
- Export Dialog öffnen
- Export Optionen verwalten
- Export durchführen

Event Subscriptions:
- ui:menu:file:export
- ui:toolbar:export
- ui:dialog:export:confirmed (format, path, options)
- document:created, document:loaded, document:closed

Event Publications:
- export:started (format, path)
- export:completed (path)
- export:failed (error)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from vpb.infrastructure.event_bus import EventBus
    from vpb.models import DocumentModel


class ExportController:
    """
    Controller für Export-Funktionalität.
    
    Koordiniert Export zwischen UI und Export-Services.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        current_document: Optional[DocumentModel] = None
    ):
        """
        Initialisiert ExportController.
        
        Args:
            event_bus: Event-Bus für Kommunikation
            current_document: Aktuelles Dokument (optional)
        """
        self.event_bus = event_bus
        self.current_document = current_document
        
        # Export State
        self.last_export_path: Optional[str] = None
        self.last_export_format: Optional[str] = None
        
        # Subscribe to Events
        self._subscribe_to_events()
        
    def _subscribe_to_events(self) -> None:
        """Subscribe zu relevanten Events."""
        # Export Events
        self.event_bus.subscribe("ui:menu:file:export", self._on_export_menu)
        self.event_bus.subscribe("ui:toolbar:export", self._on_export_menu)
        self.event_bus.subscribe("ui:dialog:export:confirmed", self._on_export_confirmed)
        
        # Document Events
        self.event_bus.subscribe("document:created", self._on_document_changed)
        self.event_bus.subscribe("document:loaded", self._on_document_changed)
        self.event_bus.subscribe("document:closed", self._on_document_closed)
        
    # ===== Event Handlers: Export Menu =====
    
    def _on_export_menu(self, data: Dict[str, Any]) -> None:
        """
        User öffnet Export-Menu.
        
        Args:
            data: Event-Daten (leer)
        """
        if not self.current_document:
            self.event_bus.publish("export:failed", {
                "error": "Kein Dokument geladen"
            })
            
            self.event_bus.publish("ui:statusbar:message", {
                "text": "Kein Dokument zum Exportieren",
                "timeout": 3000
            })
            return
            
        # Open Export Dialog
        self.event_bus.publish("ui:dialog:export:open", {
            "document": self.current_document,
            "default_format": self.last_export_format or "PNG",
            "default_path": self.last_export_path or ""
        })
    
    # ===== Event Handlers: Export Confirmed =====
    
    def _on_export_confirmed(self, data: Dict[str, Any]) -> None:
        """
        User bestätigt Export.
        
        Args:
            data: {"format": str, "path": str, "options": dict}
        """
        export_format = data.get("format", "PNG")
        export_path = data.get("path", "")
        options = data.get("options", {})
        
        if not export_path:
            self.event_bus.publish("export:failed", {
                "error": "Kein Exportpfad angegeben"
            })
            return
            
        if not self.current_document:
            self.event_bus.publish("export:failed", {
                "error": "Kein Dokument geladen"
            })
            return
            
        # Remember last export settings
        self.last_export_format = export_format
        self.last_export_path = export_path
        
        # Status-Feedback
        self.event_bus.publish("ui:statusbar:message", {
            "text": f"Exportiere als {export_format}...",
            "timeout": 0
        })
        
        # Publish start event
        self.event_bus.publish("export:started", {
            "format": export_format,
            "path": export_path,
            "options": options
        })
        
        try:
            # Perform export
            self._export_document(export_format, export_path, options)
            
            # Publish success
            self.event_bus.publish("export:completed", {
                "format": export_format,
                "path": export_path
            })
            
            # Status-Feedback
            self.event_bus.publish("ui:statusbar:message", {
                "text": f"Export erfolgreich: {export_path}",
                "timeout": 5000
            })
            
        except Exception as e:
            # Publish error
            self.event_bus.publish("export:failed", {
                "error": str(e),
                "format": export_format,
                "path": export_path
            })
            
            # Status-Feedback
            self.event_bus.publish("ui:statusbar:message", {
                "text": f"Export fehlgeschlagen: {str(e)}",
                "timeout": 5000
            })
    
    def _export_document(
        self,
        export_format: str,
        export_path: str,
        options: Dict[str, Any]
    ) -> None:
        """
        Führt Export durch.
        
        Args:
            export_format: Export-Format (PNG, SVG, PDF, XML)
            export_path: Ziel-Pfad
            options: Export-Optionen
            
        Raises:
            ValueError: Bei ungültigem Format
            IOError: Bei Schreibfehler
        """
        if not self.current_document:
            raise ValueError("Kein Dokument geladen")
            
        # Validate format
        valid_formats = ["PNG", "SVG", "PDF", "XML", "JSON"]
        if export_format.upper() not in valid_formats:
            raise ValueError(f"Ungültiges Export-Format: {export_format}")
        
        # In real implementation: call appropriate export service
        # For now, just simulate success
        
        # Mock export logic
        if export_format.upper() == "XML":
            self._export_to_xml(export_path, options)
        elif export_format.upper() == "JSON":
            self._export_to_json(export_path, options)
        elif export_format.upper() == "PNG":
            self._export_to_png(export_path, options)
        elif export_format.upper() == "SVG":
            self._export_to_svg(export_path, options)
        elif export_format.upper() == "PDF":
            self._export_to_pdf(export_path, options)
    
    def _export_to_xml(self, path: str, options: Dict[str, Any]) -> None:
        """Export zu XML (Mock)."""
        # In real implementation: use DocumentService or ExportService
        pass
    
    def _export_to_json(self, path: str, options: Dict[str, Any]) -> None:
        """Export zu JSON (Mock)."""
        # In real implementation: use DocumentService or ExportService
        pass
    
    def _export_to_png(self, path: str, options: Dict[str, Any]) -> None:
        """Export zu PNG (Mock)."""
        # In real implementation: use Canvas rendering
        dpi = options.get("dpi", 300)
        pass
    
    def _export_to_svg(self, path: str, options: Dict[str, Any]) -> None:
        """Export zu SVG (Mock)."""
        # In real implementation: use SVG rendering
        pass
    
    def _export_to_pdf(self, path: str, options: Dict[str, Any]) -> None:
        """Export zu PDF (Mock)."""
        # In real implementation: use PDF library
        dpi = options.get("dpi", 300)
        pass
    
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
        
    def export(
        self,
        export_format: str,
        export_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Exportiert Dokument.
        
        Args:
            export_format: Export-Format
            export_path: Ziel-Pfad
            options: Export-Optionen (optional)
        """
        if options is None:
            options = {}
            
        self._export_document(export_format, export_path, options)
        
    def get_last_export_info(self) -> Dict[str, Optional[str]]:
        """
        Gibt Informationen zum letzten Export zurück.
        
        Returns:
            Dict mit format und path
        """
        return {
            "format": self.last_export_format,
            "path": self.last_export_path
        }
    
    def __repr__(self) -> str:
        """String-Repräsentation."""
        doc_status = "with document" if self.current_document else "no document"
        
        if self.last_export_format:
            last_export = f"last={self.last_export_format}"
            return f"<ExportController({doc_status}, {last_export})>"
        else:
            return f"<ExportController({doc_status})>"
