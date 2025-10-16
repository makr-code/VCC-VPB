"""MergeService kapselt MergeManager-Aufrufe für den Hintergrund-Controller.

Der Service arbeitet auf einem datenbasierten Canvas-Snapshot (ohne Tk-Abhängigkeit)
und liefert das aktualisierte Diagramm samt Zusammenfassung zurück. Dadurch bleibt
die UI-Thread-Sicherheit gewahrt – das Anwenden auf die echte Canvas erfolgt erst
im Hauptthread.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING
import copy

from merge_manager import MergeManager


if TYPE_CHECKING:  # pragma: no cover - nur zur Typprüfung
    from controller.app_controller import TaskContext


def _ctx_check(context: "TaskContext | None") -> None:
    if context is None:
        return
    check = getattr(context, "check_cancelled", None)
    if callable(check):
        check()


def _ctx_progress(context: "TaskContext | None", *, fraction: Optional[float] = None, message: Optional[str] = None, **fields: Any) -> None:
    if context is None:
        return
    publish = getattr(context, "publish_progress", None)
    if callable(publish):
        try:
            publish(fraction=fraction, message=message, **fields)
        except Exception:
            pass


class _DataElement:
    def __init__(self, element_id: str, element_type: str, name: str, x: int, y: int, source: Optional[dict] = None):
        self.element_id = element_id
        self.element_type = element_type
        self.name = name
        self.x = x
        self.y = y
        self.description = ""
        self.responsible_authority = ""
        self.legal_basis = ""
        self.deadline_days = 0
        # dynamische Felder aus dem Quell-Dict übernehmen
        if source:
            for key, value in source.items():
                setattr(self, key, copy.deepcopy(value))

    def to_dict(self) -> dict:
        return copy.deepcopy(self.__dict__)


class _DataConnection:
    def __init__(self, connection_id: str, source: str, target: str, connection_type: str, source_dict: Optional[dict] = None):
        self.connection_id = connection_id
        self.source_element = source
        self.target_element = target
        self.connection_type = connection_type
        self.description = ""
        if source_dict:
            for key, value in source_dict.items():
                setattr(self, key, copy.deepcopy(value))

    def to_dict(self) -> dict:
        return copy.deepcopy(self.__dict__)


class _DataCanvas:
    def __init__(self, base: Dict[str, Any]):
        self.elements: Dict[str, _DataElement] = {}
        self.connections: Dict[str, _DataConnection] = {}
        self.metadata: Dict[str, Any] = copy.deepcopy(base.get("metadata", {}))

        for elem in base.get("elements", []) or []:
            if not isinstance(elem, dict):
                continue
            eid = elem.get("element_id") or f"E{len(self.elements)+1}"
            element = _DataElement(
                eid,
                elem.get("element_type", "FUNCTION"),
                elem.get("name") or eid,
                int(elem.get("x", 0) or 0),
                int(elem.get("y", 0) or 0),
                source=elem,
            )
            self.elements[eid] = element

        for conn in base.get("connections", []) or []:
            if not isinstance(conn, dict):
                continue
            cid = conn.get("connection_id") or f"C{len(self.connections)+1}"
            connection = _DataConnection(
                cid,
                str(conn.get("source_element", "")),
                str(conn.get("target_element", "")),
                conn.get("connection_type", "SEQUENCE"),
                source_dict=conn,
            )
            self.connections[cid] = connection

    # MergeManager API -------------------------------------------------
    def add_element(self, element_type: str, name: str, at: tuple[int, int], element_id: Optional[str] = None, push_undo: bool = True):
        eid = element_id or self._next_id("E", self.elements.keys())
        el = _DataElement(eid, element_type, name, int(at[0]), int(at[1]))
        self.elements[eid] = el
        return el

    def add_connection(self, source_element: str, target_element: str, connection_type: str, name: str, connection_id: Optional[str] = None, push_undo: bool = True):
        if source_element not in self.elements or target_element not in self.elements:
            return None
        cid = connection_id or self._next_id("C", self.connections.keys())
        conn = _DataConnection(cid, source_element, target_element, connection_type, source_dict={"description": name})
        self.connections[cid] = conn
        return conn

    def push_undo(self):
        # Für den Daten-Snapshot nicht erforderlich
        pass

    def redraw_all(self):
        # Kein Tk-Canvas – daher nichts zu tun
        pass

    # Hilfen -----------------------------------------------------------
    @staticmethod
    def _next_id(prefix: str, taken: Iterable[str]) -> str:
        taken_set = set(taken)
        idx = 1
        while True:
            cand = f"{prefix}{idx}"
            if cand not in taken_set:
                return cand
            idx += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": copy.deepcopy(self.metadata),
            "elements": [elem.to_dict() for elem in self.elements.values()],
            "connections": [conn.to_dict() for conn in self.connections.values()],
        }


class MergeService:
    def __init__(self, telemetry=None):
        self._telemetry = telemetry

    def _build_manager(self, base: Dict[str, Any]) -> MergeManager:
        canvas = _DataCanvas(base)
        return MergeManager(canvas, telemetry=self._telemetry)

    def merge_full(self, payload: Dict[str, Any], context: "TaskContext | None" = None) -> Dict[str, Any]:
        base = payload.get("base") or {}
        data = payload.get("data") or {}
        update_mode = payload.get("update_mode", "none")
        snap = bool(payload.get("snap", False))
        auto_rename = bool(payload.get("auto_rename", True))
        conflict_strategy = payload.get("conflict_strategy", "skip")

        _ctx_progress(context, fraction=0.02, message="Merge gestartet")
        _ctx_check(context)
        manager = self._build_manager(base)
        _ctx_progress(context, fraction=0.08, message="Vorbereitung abgeschlossen")
        _ctx_check(context)
        res = manager.merge_full(
            data,
            update_mode=update_mode,
            snap=snap,
            auto_rename=auto_rename,
            conflict_strategy=conflict_strategy,
        )

        _ctx_check(context)
        result = {
            "diagram": manager.canvas.to_dict(),
            "added_elements": res.added_elements,
            "added_connections": res.added_connections,
            "element_renames": res.element_renames,
            "connection_renames": res.connection_renames,
            "warnings": res.warnings,
            "summary_lines": res.summary_lines(),
        }
        _ctx_progress(
            context,
            fraction=1.0,
            message="Merge abgeschlossen",
            added_elements=res.added_elements,
            added_connections=res.added_connections,
        )
        return result

    def patch_add_only(self, payload: Dict[str, Any], context: "TaskContext | None" = None) -> Dict[str, Any]:
        base = payload.get("base") or {}
        patch = payload.get("patch") or {}
        auto_rename = bool(payload.get("auto_rename", True))

        _ctx_progress(context, fraction=0.02, message="Patch gestartet")
        _ctx_check(context)
        manager = self._build_manager(base)
        _ctx_progress(context, fraction=0.08, message="Vorbereitung abgeschlossen")
        _ctx_check(context)
        res = manager.apply_add_only_patch(patch, auto_rename=auto_rename)

        _ctx_check(context)
        result = {
            "diagram": manager.canvas.to_dict(),
            "added_elements": res.added_elements,
            "added_connections": res.added_connections,
            "element_renames": res.element_renames,
            "connection_renames": res.connection_renames,
            "warnings": res.warnings,
            "summary_lines": res.summary_lines(),
        }
        _ctx_progress(
            context,
            fraction=1.0,
            message="Patch abgeschlossen",
            added_elements=res.added_elements,
            added_connections=res.added_connections,
        )
        return result
