"""
AIController
============

Controller für AI Features.

Responsibilities:
- AI Wizard Integration
- Process Improvement Suggestions
- Text Extraction from Images
- AI-basierte Optimierung

Event Subscriptions:
- ui:menu:ai:wizard
- ui:menu:ai:improve
- ui:menu:ai:extract_text
- document:created, document:loaded, document:closed

Event Publications:
- ai:wizard:started
- ai:wizard:completed (process)
- ai:improvement:completed (suggestions)
- ai:text_extracted (text)
- ai:failed (error)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any, List

if TYPE_CHECKING:
    from vpb.infrastructure.event_bus import EventBus
    from vpb.models import DocumentModel


class AIController:
    """
    Controller für AI Features.
    
    Koordiniert AI-Funktionen zwischen UI und AI-Services.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        current_document: Optional[DocumentModel] = None
    ):
        """
        Initialisiert AIController.
        
        Args:
            event_bus: Event-Bus für Kommunikation
            current_document: Aktuelles Dokument (optional)
        """
        self.event_bus = event_bus
        self.current_document = current_document
        
        # AI State
        self.ai_enabled = True  # Can be configured
        self.last_suggestions: List[Dict[str, Any]] = []
        
        # Subscribe to Events
        self._subscribe_to_events()
        
    def _subscribe_to_events(self) -> None:
        """Subscribe zu relevanten Events."""
        # AI Events
        self.event_bus.subscribe("ui:menu:ai:wizard", self._on_ai_wizard)
        self.event_bus.subscribe("ui:menu:ai:improve", self._on_ai_improve)
        self.event_bus.subscribe("ui:menu:ai:extract_text", self._on_ai_extract_text)
        self.event_bus.subscribe("ui:menu:ai:settings", self._on_ai_settings)
        
        # Document Events
        self.event_bus.subscribe("document:created", self._on_document_changed)
        self.event_bus.subscribe("document:loaded", self._on_document_changed)
        self.event_bus.subscribe("document:closed", self._on_document_closed)
        
    # ===== Event Handlers: AI Wizard =====
    
    def _on_ai_wizard(self, data: Dict[str, Any]) -> None:
        """
        User startet AI Wizard.
        
        Args:
            data: {"prompt": str} (optional)
        """
        if not self.ai_enabled:
            self.event_bus.publish("ai:failed", {
                "error": "AI-Features sind deaktiviert"
            })
            return
            
        prompt = data.get("prompt", "")
        
        # Status-Feedback
        self.event_bus.publish("ui:statusbar:message", {
            "text": "AI Wizard läuft...",
            "timeout": 0
        })
        
        # Publish start event
        self.event_bus.publish("ai:wizard:started", {
            "prompt": prompt
        })
        
        try:
            # Simulate AI Wizard (in real implementation: call AI service)
            process_data = self._generate_process_from_prompt(prompt)
            
            # Publish results
            self.event_bus.publish("ai:wizard:completed", {
                "process": process_data,
                "prompt": prompt
            })
            
            # Status-Feedback
            self.event_bus.publish("ui:statusbar:message", {
                "text": f"AI Wizard: {len(process_data.get('elements', []))} Elemente erstellt",
                "timeout": 5000
            })
            
        except Exception as e:
            self.event_bus.publish("ai:failed", {
                "error": str(e),
                "operation": "wizard"
            })
            
            self.event_bus.publish("ui:statusbar:message", {
                "text": f"AI Wizard fehlgeschlagen: {str(e)}",
                "timeout": 5000
            })
    
    def _generate_process_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Generiert Prozess aus Prompt (Mock).
        
        Args:
            prompt: User-Prompt
            
        Returns:
            Process-Daten (elements, connections)
        """
        # This is a mock - in real implementation, call AI service
        elements = [
            {"type": "ACTIVITY", "name": "Start", "x": 100, "y": 100},
            {"type": "ACTIVITY", "name": "Process", "x": 300, "y": 100},
            {"type": "ACTIVITY", "name": "End", "x": 500, "y": 100},
        ]
        
        connections = [
            {"source": 0, "target": 1},
            {"source": 1, "target": 2},
        ]
        
        return {
            "elements": elements,
            "connections": connections,
            "prompt": prompt
        }
    
    # ===== Event Handlers: AI Improve =====
    
    def _on_ai_improve(self, data: Dict[str, Any]) -> None:
        """
        User fordert AI-Verbesserungen an.
        
        Args:
            data: Event-Daten (leer)
        """
        if not self.ai_enabled:
            self.event_bus.publish("ai:failed", {
                "error": "AI-Features sind deaktiviert"
            })
            return
            
        if not self.current_document:
            self.event_bus.publish("ai:failed", {
                "error": "Kein Dokument geladen"
            })
            return
            
        # Status-Feedback
        self.event_bus.publish("ui:statusbar:message", {
            "text": "AI analysiert Prozess...",
            "timeout": 0
        })
        
        try:
            # Generate improvement suggestions
            suggestions = self._generate_improvement_suggestions()
            self.last_suggestions = suggestions
            
            # Publish results
            self.event_bus.publish("ai:improvement:completed", {
                "suggestions": suggestions,
                "document": self.current_document
            })
            
            # Status-Feedback
            self.event_bus.publish("ui:statusbar:message", {
                "text": f"AI: {len(suggestions)} Verbesserungsvorschläge",
                "timeout": 5000
            })
            
        except Exception as e:
            self.event_bus.publish("ai:failed", {
                "error": str(e),
                "operation": "improve"
            })
            
            self.event_bus.publish("ui:statusbar:message", {
                "text": f"AI Analyse fehlgeschlagen: {str(e)}",
                "timeout": 5000
            })
    
    def _generate_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """
        Generiert Verbesserungsvorschläge (Mock).
        
        Returns:
            Liste von Suggestions
        """
        if not self.current_document:
            return []
            
        suggestions = []
        
        elements = self.current_document.get_all_elements()
        connections = self.current_document.get_all_connections()
        
        # Suggestion: Add missing connections
        if len(elements) > 1 and len(connections) == 0:
            suggestions.append({
                "type": "ADD_CONNECTIONS",
                "title": "Verbindungen hinzufügen",
                "description": "Prozess hat keine Verbindungen zwischen Elementen",
                "priority": "high"
            })
        
        # Suggestion: Add descriptions
        elements_without_desc = [e for e in elements if not e.description]
        if len(elements_without_desc) > 0:
            suggestions.append({
                "type": "ADD_DESCRIPTIONS",
                "title": "Beschreibungen hinzufügen",
                "description": f"{len(elements_without_desc)} Elemente haben keine Beschreibung",
                "priority": "medium",
                "affected_elements": [e.element_id for e in elements_without_desc]
            })
        
        # Suggestion: Optimize layout
        if len(elements) > 3:
            suggestions.append({
                "type": "OPTIMIZE_LAYOUT",
                "title": "Layout optimieren",
                "description": "Automatisches Layout kann die Übersichtlichkeit verbessern",
                "priority": "low"
            })
        
        return suggestions
    
    # ===== Event Handlers: Text Extraction =====
    
    def _on_ai_extract_text(self, data: Dict[str, Any]) -> None:
        """
        User fordert Text-Extraktion aus Bild an.
        
        Args:
            data: {"image_path": str}
        """
        if not self.ai_enabled:
            self.event_bus.publish("ai:failed", {
                "error": "AI-Features sind deaktiviert"
            })
            return
            
        image_path = data.get("image_path", "")
        
        if not image_path:
            self.event_bus.publish("ai:failed", {
                "error": "Kein Bild ausgewählt"
            })
            return
            
        # Status-Feedback
        self.event_bus.publish("ui:statusbar:message", {
            "text": "AI extrahiert Text...",
            "timeout": 0
        })
        
        try:
            # Extract text (mock)
            extracted_text = self._extract_text_from_image(image_path)
            
            # Publish results
            self.event_bus.publish("ai:text_extracted", {
                "text": extracted_text,
                "image_path": image_path
            })
            
            # Status-Feedback
            self.event_bus.publish("ui:statusbar:message", {
                "text": f"Text extrahiert ({len(extracted_text)} Zeichen)",
                "timeout": 5000
            })
            
        except Exception as e:
            self.event_bus.publish("ai:failed", {
                "error": str(e),
                "operation": "extract_text"
            })
            
            self.event_bus.publish("ui:statusbar:message", {
                "text": f"Text-Extraktion fehlgeschlagen: {str(e)}",
                "timeout": 5000
            })
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """
        Extrahiert Text aus Bild (Mock).
        
        Args:
            image_path: Pfad zum Bild
            
        Returns:
            Extrahierter Text
        """
        # This is a mock - in real implementation, use OCR/AI service
        return f"Extracted text from {image_path}"
    
    # ===== Event Handlers: AI Settings =====
    
    def _on_ai_settings(self, data: Dict[str, Any]) -> None:
        """
        AI Settings ändern.
        
        Args:
            data: {"enabled": bool} (optional)
        """
        if "enabled" in data:
            self.ai_enabled = data["enabled"]
            
            status = "aktiviert" if self.ai_enabled else "deaktiviert"
            self.event_bus.publish("ui:statusbar:message", {
                "text": f"AI-Features {status}",
                "timeout": 3000
            })
    
    # ===== Document Lifecycle =====
    
    def _on_document_changed(self, data: Dict[str, Any]) -> None:
        """
        Neues Dokument erstellt oder geladen.
        
        Args:
            data: {"document": DocumentModel}
        """
        document = data.get("document")
        self.current_document = document
        self.last_suggestions = []
        
    def _on_document_closed(self, data: Dict[str, Any]) -> None:
        """
        Dokument geschlossen.
        
        Args:
            data: Event-Daten (leer)
        """
        self.current_document = None
        self.last_suggestions = []
        
    # ===== Public API =====
    
    def set_document(self, document: Optional[DocumentModel]) -> None:
        """
        Setzt das aktuelle Dokument.
        
        Args:
            document: DocumentModel oder None
        """
        self.current_document = document
        self.last_suggestions = []
        
    def enable_ai(self, enabled: bool) -> None:
        """
        Aktiviert/Deaktiviert AI-Features.
        
        Args:
            enabled: True zum Aktivieren, False zum Deaktivieren
        """
        self.ai_enabled = enabled
        
    def get_last_suggestions(self) -> List[Dict[str, Any]]:
        """
        Gibt letzte Verbesserungsvorschläge zurück.
        
        Returns:
            Liste von Suggestions
        """
        return self.last_suggestions
    
    def __repr__(self) -> str:
        """String-Repräsentation."""
        doc_status = "with document" if self.current_document else "no document"
        ai_status = "enabled" if self.ai_enabled else "disabled"
        suggestions_count = len(self.last_suggestions)
        return f"<AIController({doc_status}, ai={ai_status}, suggestions={suggestions_count})>"
