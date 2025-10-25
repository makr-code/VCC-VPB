"""
BackgroundTaskController
========================

Controller für Hintergrund-Tasks (z.B. Ollama Chat Streams).

Responsibilities:
- Submit & Cancel von Hintergrund-Tasks
- Task-Lifecycle Management
- Event-basierte Kommunikation mit UI

Event Publications:
- task:started (task_id, task_type)
- task:completed (task_id, result)
- task:failed (task_id, error)
- task:cancelled (task_id)
- task:progress (task_id, progress, message)
- task:stream_chunk (task_id, chunk)
"""

from __future__ import annotations
import threading
import uuid
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

if TYPE_CHECKING:
    from vpb.infrastructure.event_bus import EventBus

from ollama_client import OllamaClient, OllamaOptions, OllamaJob


class BackgroundTaskController:
    """
    Controller für Hintergrund-Tasks.
    
    Verwaltet asynchrone Tasks wie Ollama-Chat-Streams.
    """
    
    def __init__(self, event_bus: EventBus):
        """
        Initialisiert BackgroundTaskController.
        
        Args:
            event_bus: Event-Bus für Kommunikation
        """
        self.event_bus = event_bus
        self._tasks: Dict[str, OllamaJob] = {}
        self._task_locks = threading.Lock()
    
    def submit(self, task_type: str, payload: Dict[str, Any]) -> str:
        """
        Startet einen Hintergrund-Task.
        
        Args:
            task_type: Typ des Tasks (z.B. "ollama_chat_stream")
            payload: Task-spezifische Daten
            
        Returns:
            Task-ID für Tracking/Cancel
            
        Raises:
            ValueError: Wenn task_type unbekannt ist
        """
        task_id = str(uuid.uuid4())
        
        if task_type == "ollama_chat_stream":
            job = self._start_ollama_chat_stream(task_id, payload)
            with self._task_locks:
                self._tasks[task_id] = job
        else:
            raise ValueError(f"Unbekannter Task-Typ: {task_type}")
        
        self.event_bus.publish("task:started", {"task_id": task_id, "task_type": task_type})
        return task_id
    
    def cancel(self, task_id: str) -> bool:
        """
        Bricht einen laufenden Task ab.
        
        Args:
            task_id: ID des Tasks
            
        Returns:
            True wenn Task gefunden und abgebrochen wurde
        """
        with self._task_locks:
            job = self._tasks.get(task_id)
            if not job:
                return False
            
            job.cancel()
            del self._tasks[task_id]
        
        self.event_bus.publish("task:cancelled", {"task_id": task_id})
        return True
    
    def _start_ollama_chat_stream(self, task_id: str, payload: Dict[str, Any]) -> OllamaJob:
        """
        Startet Ollama Chat Stream.
        
        Args:
            task_id: Task-ID für Tracking
            payload: {"endpoint", "model", "temperature", "num_predict", "messages"}
            
        Returns:
            OllamaJob-Instanz
        """
        endpoint = payload.get("endpoint", "http://localhost:11434")
        model = payload.get("model", "llama3.2")
        temperature = payload.get("temperature", 0.7)
        num_predict = payload.get("num_predict", 2048)
        messages = payload.get("messages", [])
        
        client = OllamaClient(endpoint, model=model)
        options = OllamaOptions(
            temperature=temperature,
            num_predict=num_predict,
        )
        
        def run_stream():
            """Thread-Funktion für Streaming."""
            try:
                # Signalisiere Stream-Start (im Haupt-Thread)
                self.event_bus.publish("task:stream_chunk", {
                    "task_id": task_id,
                    "chunk": ""  # Leerer Chunk als Start-Signal
                })
                
                # Stream starten
                for chunk in client.chat_stream(messages=messages, options=options):
                    if chunk and chunk.strip():  # Nur nicht-leere Chunks senden
                        # Event-Publishing im Haupt-Thread
                        self.event_bus.publish("task:stream_chunk", {
                            "task_id": task_id,
                            "chunk": chunk
                        })
                
                # Stream abgeschlossen
                with self._task_locks:
                    if task_id in self._tasks:
                        del self._tasks[task_id]
                
                self.event_bus.publish("task:completed", {
                    "task_id": task_id,
                    "result": ""  # Vollständiger Text wird bereits über Chunks gesendet
                })
                
            except Exception as e:
                with self._task_locks:
                    if task_id in self._tasks:
                        del self._tasks[task_id]
                
                self.event_bus.publish("task:failed", {
                    "task_id": task_id,
                    "error": str(e)
                })
        
        # OllamaJob erstellen und starten
        job = OllamaJob(target=run_stream)
        job.start()
        
        return job
    
    def is_running(self, task_id: str) -> bool:
        """
        Prüft ob Task noch läuft.
        
        Args:
            task_id: ID des Tasks
            
        Returns:
            True wenn Task läuft
        """
        with self._task_locks:
            return task_id in self._tasks
    
    def shutdown(self) -> None:
        """Stoppt alle laufenden Tasks."""
        with self._task_locks:
            for job in list(self._tasks.values()):
                try:
                    job.cancel()
                except Exception:
                    pass
            self._tasks.clear()
    
    def __repr__(self) -> str:
        """String-Repräsentation."""
        with self._task_locks:
            task_count = len(self._tasks)
        return f"<BackgroundTaskController(tasks={task_count})>"
