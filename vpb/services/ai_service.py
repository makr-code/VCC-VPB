#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIService - Verwaltung von KI-gestützter Prozessgenerierung und -analyse.

Dieser Service kapselt die Interaktion mit Ollama für VPB-spezifische Aufgaben:
- Prozessgenerierung aus Textbeschreibungen
- Vorschläge für nächste Schritte im Prozess
- Diagnose und Fehlerbehebung bestehender Prozesse
- Validierung von KI-generierten Ausgaben

Der Service verwendet:
- OllamaClient: HTTP-Client für Ollama API
- vpb_ai_logic: Prompt-Building mit Few-Shot Beispielen
- Event-Bus: Benachrichtigungen über KI-Operationen
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Iterator, Callable
import json
from pathlib import Path

# Ollama Client
from ollama_client import OllamaClient, OllamaOptions, OllamaJob

# AI Logic
from vpb_ai_logic import (
    build_prompt_with_examples_text_to_vpb,
    build_prompt_with_examples_next_steps,
    build_prompt_with_examples_diagnose_fix,
    build_prompt_for_ingestion,
    validate_model_output,
    finalize_response,
)

# Event-Bus
from vpb.infrastructure.event_bus import get_global_event_bus


# ============================
# Configuration & Result Classes
# ============================

@dataclass
class AIConfig:
    """Konfiguration für AI-Service."""
    
    # Ollama Verbindung
    endpoint: str = "http://localhost:11434"
    model: str = "llama3.2:latest"
    timeout: int = 120
    
    # Generierungsparameter
    temperature: float = 0.7
    num_predict: int = 2048
    
    # Few-Shot Beispiele
    max_examples: int = 3
    example_tags: List[str] = field(default_factory=list)
    
    # Validierung
    validation_tolerance: str = "strict"  # strict, lenient, permissive
    max_retries: int = 2
    
    # Verfügbare Element-/Verbindungstypen (aus Schema)
    element_types: List[str] = field(default_factory=lambda: [
        "StartEvent", "EndEvent", "Prozess", "Entscheidung", 
        "Parallelisierung", "Synchronisation", "Dokument", "Note"
    ])
    connection_types: List[str] = field(default_factory=lambda: [
        "SequenceFlow", "DataFlow", "Association"
    ])


@dataclass
class AIResult:
    """Ergebnis einer KI-Operation."""
    
    success: bool
    data: Optional[Dict[str, Any]] = None  # Geparste JSON-Daten
    raw_output: str = ""  # Rohe Modell-Ausgabe
    validation_issues: List[Dict[str, Any]] = field(default_factory=list)
    fatal_errors: bool = False
    attempts: int = 1
    message: str = ""
    
    def __bool__(self) -> bool:
        return self.success and not self.fatal_errors
    
    def get_elements(self) -> List[Dict[str, Any]]:
        """Extrahiert Elements aus dem Ergebnis."""
        if not self.data:
            return []
        return self.data.get("elements", [])
    
    def get_connections(self) -> List[Dict[str, Any]]:
        """Extrahiert Connections aus dem Ergebnis."""
        if not self.data:
            return []
        return self.data.get("connections", [])
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Extrahiert Metadata aus dem Ergebnis."""
        if not self.data:
            return None
        return self.data.get("metadata")


# ============================
# Exceptions
# ============================

class AIServiceError(Exception):
    """Basisklasse für AI-Service Fehler."""
    pass


class OllamaConnectionError(AIServiceError):
    """Ollama ist nicht erreichbar."""
    pass


class ValidationError(AIServiceError):
    """KI-Ausgabe konnte nicht validiert werden."""
    pass


# ============================
# AIService
# ============================

class AIService:
    """
    Service für KI-gestützte Prozessgenerierung und -analyse.
    
    Dieser Service verwaltet die Kommunikation mit Ollama und stellt
    VPB-spezifische Methoden zur Verfügung:
    
    - generate_process_from_text: Erstellt Prozess aus Textbeschreibung
    - suggest_next_steps: Schlägt nächste Schritte für Prozess vor
    - diagnose_and_fix: Analysiert Prozess und schlägt Fixes vor
    - validate_output: Validiert KI-generierte Ausgaben
    
    Alle Methoden publizieren Events über den Event-Bus für Monitoring
    und UI-Feedback.
    """
    
    def __init__(self, config: Optional[AIConfig] = None):
        """
        Initialisiert den AI-Service.
        
        Args:
            config: Konfiguration (default: AIConfig mit Standardwerten)
        """
        self.config = config or AIConfig()
        self.event_bus = get_global_event_bus()
        
        # Ollama Client initialisieren
        self.client = OllamaClient(
            endpoint=self.config.endpoint,
            model=self.config.model,
            timeout=self.config.timeout
        )
        
        # Default Ollama Options
        self.default_options = OllamaOptions(
            temperature=self.config.temperature,
            num_predict=self.config.num_predict
        )
    
    def __repr__(self) -> str:
        return (
            f"AIService(model={self.config.model}, "
            f"endpoint={self.config.endpoint}, "
            f"temperature={self.config.temperature})"
        )
    
    # ============================
    # Health Check
    # ============================
    
    def health_check(self) -> Dict[str, Any]:
        """
        Prüft ob Ollama erreichbar ist und welche Modelle verfügbar sind.
        
        Returns:
            Dict mit Ollama-Status und verfügbaren Modellen
            
        Raises:
            OllamaConnectionError: Wenn Ollama nicht erreichbar ist
        """
        self.event_bus.publish('ai:health_check:started', {})
        
        try:
            result = self.client.health()
            self.event_bus.publish('ai:health_check:completed', {
                'models_available': len(result.get('models', [])),
                'current_model': self.config.model
            })
            return result
        except Exception as e:
            self.event_bus.publish('ai:health_check:failed', {
                'error': str(e),
                'endpoint': self.config.endpoint
            })
            raise OllamaConnectionError(f"Ollama nicht erreichbar: {e}") from e
    
    # ============================
    # Process Generation
    # ============================
    
    def generate_process_from_text(
        self,
        description: str,
        options: Optional[OllamaOptions] = None
    ) -> AIResult:
        """
        Generiert einen vollständigen Prozess aus einer Textbeschreibung.
        
        Args:
            description: Textuelle Beschreibung des Prozesses
            options: Optionale Ollama-Parameter (überschreibt defaults)
            
        Returns:
            AIResult mit generiertem Prozess (elements, connections, metadata)
            
        Example:
            >>> service = AIService()
            >>> result = service.generate_process_from_text(
            ...     "Ein Antragsprozess mit Prüfung und Genehmigung"
            ... )
            >>> if result:
            ...     print(f"{len(result.get_elements())} Elements generiert")
        """
        self.event_bus.publish('ai:generate_process:started', {
            'description_length': len(description),
            'model': self.config.model
        })
        
        try:
            # Prompt mit Few-Shot Beispielen erstellen
            prompt, meta = build_prompt_with_examples_text_to_vpb(
                description=description,
                element_types=self.config.element_types,
                connection_types=self.config.connection_types,
                example_tags=self.config.example_tags,
                max_examples=self.config.max_examples,
                return_meta=True
            )
            
            # KI-Generierung mit Validierung
            raw_output = self.client.generate(
                prompt=prompt,
                options=options or self.default_options,
                stream=False
            )
            
            # Validierung
            validation = validate_model_output(
                raw_output,
                mode="text_to_vpb",
                existing_ids=[],
                allow_element_types=self.config.element_types,
                allow_connection_types=self.config.connection_types,
                tolerance=self.config.validation_tolerance
            )
            
            # Finalize (Hook für Telemetrie)
            finalize_response(meta, raw_output, validation)
            
            # Ergebnis zusammenstellen
            parsed_data = validation.get("parsed")
            is_fatal = validation.get("fatal", False)
            
            # Message basierend auf Status
            if is_fatal or parsed_data is None:
                message = f"Prozessgenerierung fehlgeschlagen: {len(validation.get('issues', []))} fatale Fehler"
            else:
                element_count = len(parsed_data.get('elements', []))
                message = f"Prozess generiert mit {element_count} Elements"
            
            result = AIResult(
                success=parsed_data is not None and not is_fatal,
                data=parsed_data,
                raw_output=raw_output,
                validation_issues=validation.get("issues", []),
                fatal_errors=is_fatal,
                attempts=1,
                message=message
            )
            
            self.event_bus.publish('ai:generate_process:completed', {
                'success': result.success,
                'elements_count': len(result.get_elements()),
                'connections_count': len(result.get_connections()),
                'validation_issues': len(result.validation_issues)
            })
            
            return result
            
        except Exception as e:
            self.event_bus.publish('ai:generate_process:failed', {
                'error': str(e)
            })
            return AIResult(
                success=False,
                message=f"Fehler bei Prozessgenerierung: {e}"
            )
    
    # ============================
    # Next Steps Suggestion
    # ============================
    
    def suggest_next_steps(
        self,
        current_diagram_json: str,
        selected_element_id: Optional[str] = None,
        options: Optional[OllamaOptions] = None
    ) -> AIResult:
        """
        Schlägt nächste Schritte für einen bestehenden Prozess vor.
        
        Args:
            current_diagram_json: Aktuelles Diagramm als JSON-String
            selected_element_id: ID des ausgewählten Elements (optional)
            options: Optionale Ollama-Parameter
            
        Returns:
            AIResult mit vorgeschlagenen Elements/Connections (Add-Only)
            
        Example:
            >>> current = json.dumps({"elements": [...], "connections": [...]})
            >>> result = service.suggest_next_steps(current, selected_element_id="e1")
            >>> if result:
            ...     new_elements = result.get_elements()
        """
        self.event_bus.publish('ai:suggest_next_steps:started', {
            'selected_element': selected_element_id,
            'model': self.config.model
        })
        
        try:
            # Parse current diagram to extract existing IDs
            try:
                current_data = json.loads(current_diagram_json)
                existing_ids = [el.get("element_id", "") for el in current_data.get("elements", [])]
            except:
                existing_ids = []
            
            # Prompt erstellen
            prompt, meta = build_prompt_with_examples_next_steps(
                current_diagram_json=current_diagram_json,
                selected_element_id=selected_element_id,
                element_types=self.config.element_types,
                connection_types=self.config.connection_types,
                example_tags=self.config.example_tags,
                max_examples=self.config.max_examples,
                return_meta=True
            )
            
            # KI-Generierung
            raw_output = self.client.generate(
                prompt=prompt,
                options=options or self.default_options,
                stream=False
            )
            
            # Validierung
            validation = validate_model_output(
                raw_output,
                mode="next_steps",
                existing_ids=existing_ids,
                allow_element_types=self.config.element_types,
                allow_connection_types=self.config.connection_types,
                tolerance=self.config.validation_tolerance
            )
            
            finalize_response(meta, raw_output, validation)
            
            result = AIResult(
                success=validation.get("parsed") is not None,
                data=validation.get("parsed"),
                raw_output=raw_output,
                validation_issues=validation.get("issues", []),
                fatal_errors=validation.get("fatal", False),
                attempts=1,
                message=f"Vorschlag mit {len(validation.get('parsed', {}).get('elements', []))} neuen Elements"
            )
            
            self.event_bus.publish('ai:suggest_next_steps:completed', {
                'success': result.success,
                'new_elements': len(result.get_elements()),
                'new_connections': len(result.get_connections())
            })
            
            return result
            
        except Exception as e:
            self.event_bus.publish('ai:suggest_next_steps:failed', {
                'error': str(e)
            })
            return AIResult(
                success=False,
                message=f"Fehler bei Next Steps: {e}"
            )
    
    # ============================
    # Diagnose & Fix
    # ============================
    
    def diagnose_and_fix(
        self,
        current_diagram_json: str,
        options: Optional[OllamaOptions] = None
    ) -> AIResult:
        """
        Analysiert einen Prozess auf Probleme und schlägt Fixes vor.
        
        Args:
            current_diagram_json: Aktuelles Diagramm als JSON-String
            options: Optionale Ollama-Parameter
            
        Returns:
            AIResult mit issues[] und optionalem patch
            
        Example:
            >>> current = json.dumps({"elements": [...], "connections": [...]})
            >>> result = service.diagnose_and_fix(current)
            >>> if result and result.data:
            ...     issues = result.data.get("issues", [])
            ...     patch = result.data.get("patch", {})
        """
        self.event_bus.publish('ai:diagnose_fix:started', {
            'model': self.config.model
        })
        
        try:
            # Parse for existing IDs
            try:
                current_data = json.loads(current_diagram_json)
                existing_ids = [el.get("element_id", "") for el in current_data.get("elements", [])]
            except:
                existing_ids = []
            
            # Prompt erstellen
            prompt, meta = build_prompt_with_examples_diagnose_fix(
                current_diagram_json=current_diagram_json,
                element_types=self.config.element_types,
                connection_types=self.config.connection_types,
                example_tags=self.config.example_tags,
                max_examples=self.config.max_examples,
                return_meta=True
            )
            
            # KI-Generierung
            raw_output = self.client.generate(
                prompt=prompt,
                options=options or self.default_options,
                stream=False
            )
            
            # Validierung
            validation = validate_model_output(
                raw_output,
                mode="diagnose_fix",
                existing_ids=existing_ids,
                allow_element_types=self.config.element_types,
                allow_connection_types=self.config.connection_types,
                tolerance=self.config.validation_tolerance
            )
            
            finalize_response(meta, raw_output, validation)
            
            result = AIResult(
                success=validation.get("parsed") is not None,
                data=validation.get("parsed"),
                raw_output=raw_output,
                validation_issues=validation.get("issues", []),
                fatal_errors=validation.get("fatal", False),
                attempts=1,
                message=f"Diagnose mit {len(validation.get('parsed', {}).get('issues', []))} gefundenen Problemen"
            )
            
            self.event_bus.publish('ai:diagnose_fix:completed', {
                'success': result.success,
                'issues_found': len(result.data.get("issues", []) if result.data else [])
            })
            
            return result
            
        except Exception as e:
            self.event_bus.publish('ai:diagnose_fix:failed', {
                'error': str(e)
            })
            return AIResult(
                success=False,
                message=f"Fehler bei Diagnose: {e}"
            )
    
    # ============================
    # Ingestion (Optional)
    # ============================
    
    def ingest_from_sources(
        self,
        sources_text: str,
        prompt_context: str = "",
        current_diagram_summary: str = "",
        options: Optional[OllamaOptions] = None
    ) -> AIResult:
        """
        Extrahiert Prozessinformationen aus externen Quellen (PDFs, Websites, etc.).
        
        Args:
            sources_text: Text aus externen Quellen
            prompt_context: Zusätzlicher Kontext für Prompt
            current_diagram_summary: Zusammenfassung des aktuellen Diagramms
            options: Optionale Ollama-Parameter
            
        Returns:
            AIResult mit extrahierten Elements/Connections
        """
        self.event_bus.publish('ai:ingest:started', {
            'sources_length': len(sources_text),
            'model': self.config.model
        })
        
        try:
            prompt, meta = build_prompt_for_ingestion(
                sources_text=sources_text,
                element_types=self.config.element_types,
                connection_types=self.config.connection_types,
                prompt_context=prompt_context,
                current_diagram_summary=current_diagram_summary,
                example_tags=self.config.example_tags,
                return_meta=True
            )
            
            raw_output = self.client.generate(
                prompt=prompt,
                options=options or self.default_options,
                stream=False
            )
            
            validation = validate_model_output(
                raw_output,
                mode="ingestion_diff",
                existing_ids=[],
                allow_element_types=self.config.element_types,
                allow_connection_types=self.config.connection_types,
                tolerance=self.config.validation_tolerance
            )
            
            finalize_response(meta, raw_output, validation)
            
            result = AIResult(
                success=validation.get("parsed") is not None,
                data=validation.get("parsed"),
                raw_output=raw_output,
                validation_issues=validation.get("issues", []),
                fatal_errors=validation.get("fatal", False),
                attempts=1,
                message=f"Ingestion: {len(validation.get('parsed', {}).get('elements', []))} Elements extrahiert"
            )
            
            self.event_bus.publish('ai:ingest:completed', {
                'success': result.success,
                'elements_extracted': len(result.get_elements())
            })
            
            return result
            
        except Exception as e:
            self.event_bus.publish('ai:ingest:failed', {
                'error': str(e)
            })
            return AIResult(
                success=False,
                message=f"Fehler bei Ingestion: {e}"
            )
    
    # ============================
    # Streaming Support
    # ============================
    
    def generate_process_stream(
        self,
        description: str,
        callback: Callable[[str], None],
        options: Optional[OllamaOptions] = None
    ) -> OllamaJob:
        """
        Generiert Prozess im Streaming-Modus mit Callback für Chunks.
        
        Args:
            description: Textuelle Beschreibung
            callback: Funktion die für jeden Text-Chunk aufgerufen wird
            options: Optionale Ollama-Parameter
            
        Returns:
            OllamaJob für asynchrone Verarbeitung
            
        Example:
            >>> def on_chunk(text):
            ...     print(text, end='', flush=True)
            >>> job = service.generate_process_stream("Ein Prozess...", on_chunk)
            >>> job.start()
            >>> job.join()  # Warten bis fertig
        """
        prompt, _ = build_prompt_with_examples_text_to_vpb(
            description=description,
            element_types=self.config.element_types,
            connection_types=self.config.connection_types,
            example_tags=self.config.example_tags,
            max_examples=self.config.max_examples,
            return_meta=True
        )
        
        def stream_wrapper():
            for chunk in self.client.generate_stream(
                prompt=prompt,
                options=options or self.default_options
            ):
                callback(chunk)
        
        return OllamaJob(stream_wrapper)
    
    def suggest_next_steps_stream(
        self,
        current_diagram_json: str,
        selected_element_id: Optional[str],
        callback: Callable[[str], None],
        options: Optional[OllamaOptions] = None
    ) -> OllamaJob:
        """
        Schlägt nächste Schritte im Streaming-Modus vor.
        
        Args:
            current_diagram_json: Aktuelles Diagramm
            selected_element_id: Ausgewähltes Element
            callback: Funktion für Text-Chunks
            options: Optionale Ollama-Parameter
            
        Returns:
            OllamaJob für asynchrone Verarbeitung
        """
        prompt, _ = build_prompt_with_examples_next_steps(
            current_diagram_json=current_diagram_json,
            selected_element_id=selected_element_id,
            element_types=self.config.element_types,
            connection_types=self.config.connection_types,
            example_tags=self.config.example_tags,
            max_examples=self.config.max_examples,
            return_meta=True
        )
        
        def stream_wrapper():
            for chunk in self.client.generate_stream(
                prompt=prompt,
                options=options or self.default_options
            ):
                callback(chunk)
        
        return OllamaJob(stream_wrapper)
    
    # ============================
    # Validation Helper
    # ============================
    
    def validate_output(
        self,
        raw_output: str,
        mode: str,
        existing_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validiert eine KI-Ausgabe ohne neue Generierung.
        
        Args:
            raw_output: Rohe Modell-Ausgabe
            mode: Validierungsmodus (text_to_vpb, next_steps, diagnose_fix, etc.)
            existing_ids: Liste existierender Element-IDs
            
        Returns:
            Dict mit parsed, issues, fatal, repairs
            
        Example:
            >>> validation = service.validate_output(
            ...     raw_output='{"elements": [...]}',
            ...     mode="text_to_vpb"
            ... )
            >>> if not validation["fatal"]:
            ...     data = validation["parsed"]
        """
        return validate_model_output(
            raw_output,
            mode=mode,
            existing_ids=existing_ids or [],
            allow_element_types=self.config.element_types,
            allow_connection_types=self.config.connection_types,
            tolerance=self.config.validation_tolerance
        )
