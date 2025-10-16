"""Kleiner Message/Task-Bus für Hintergrund-Services.

Thread-Kommunikation basiert auf queue.Queue.

Kernelemente:
- TaskRequest: beschreibende Einheit einer Arbeit (type, payload, id)
- TaskResult: Ergebnis oder Fehler (success, data, error)
- MessageBus: Einfache Hilfen zum Erzeugen von IDs
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
import time, itertools

_task_id_counter = itertools.count(1)

def next_task_id() -> str:
    return f"task-{next(_task_id_counter)}"

@dataclass(slots=True)
class TaskRequest:
    task_id: str
    task_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_ts: float = field(default_factory=time.time)

@dataclass(slots=True)
class TaskResult:
    task_id: str
    task_type: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    started_ts: float = field(default_factory=time.time)
    finished_ts: float = field(default_factory=time.time)

    @property
    def duration_s(self) -> float:
        return max(0.0, self.finished_ts - self.started_ts)
