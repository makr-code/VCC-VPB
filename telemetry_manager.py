from __future__ import annotations
from typing import Optional, List, Dict, Any, Callable
import json, threading, time, itertools

class TelemetryManager:
    """Sehr einfacher Telemetrie-/Logging-Sammelpunkt.

    Speichert Events im Speicher (FIFO Liste) und erlaubt optionales Flush
    in eine JSON-Lines Datei. Zusätzlich können Listener registriert werden,
    die bei jedem aufgezeichneten Event benachrichtigt werden. Kann später
    durch komplexere Infrastruktur ersetzt werden (OpenTelemetry, o.Ä.).
    """

    def __init__(self, max_events: int = 10000):
        self._max = max_events
        self._lock = threading.Lock()
        self._events: List[Dict[str, Any]] = []
        self._listeners: Dict[Optional[str], Dict[int, Callable[[Dict[str, Any]], None]]] = {}
        self._listener_ids = itertools.count(1)

    def record(self, event_type: str, **fields):
        ev = {
            "type": event_type,
            "ts": time.time(),
        }
        ev.update(fields)
        listeners: List[Callable[[Dict[str, Any]], None]] = []
        with self._lock:
            self._events.append(ev)
            if len(self._events) > self._max:
                # Älteste verwerfen
                overflow = len(self._events) - self._max
                if overflow > 0:
                    del self._events[0:overflow]
            listeners.extend(self._listeners.get(None, {}).values())
            listeners.extend(self._listeners.get(event_type, {}).values())
        if listeners:
            payload = dict(ev)
            for cb in listeners:
                try:
                    cb(payload)
                except Exception:
                    pass
        return ev

    def subscribe(self, callback: Callable[[Dict[str, Any]], None], *, event_type: Optional[str] = None) -> Callable[[], None]:
        """Registriert einen Listener und gibt eine Unsubscribe-Funktion zurück."""
        token = next(self._listener_ids)
        with self._lock:
            bucket = self._listeners.setdefault(event_type, {})
            bucket[token] = callback

        def unsubscribe() -> None:
            with self._lock:
                bucket = self._listeners.get(event_type)
                if not bucket:
                    return
                bucket.pop(token, None)
                if not bucket:
                    self._listeners.pop(event_type, None)

        return unsubscribe

    def clear_listeners(self, event_type: Optional[str] = None) -> None:
        """Entfernt alle Listener (optional gefiltert nach Event-Typ)."""
        with self._lock:
            if event_type is None:
                self._listeners.clear()
            else:
                self._listeners.pop(event_type, None)

    def events(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if event_type is None:
                return list(self._events)
            return [e for e in self._events if e.get("type") == event_type]

    def flush_jsonl(self, path: str):
        with self._lock:
            data = list(self._events)
        with open(path, "a", encoding="utf-8") as f:
            for ev in data:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    def clear(self):
        with self._lock:
            self._events.clear()

__all__ = ["TelemetryManager"]
