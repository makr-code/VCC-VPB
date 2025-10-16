"""Merge- und Patch-Logik aus `vpb_app.py` extrahiert.

Ziel: Bessere Testbarkeit und Entkopplung von UI.
Der Manager arbeitet über eine einfache Canvas-Interface-Abstraktion, die nur
benötigte Methoden/Attribute bereitstellt.
"""
from __future__ import annotations
from typing import Any, Optional, Iterable
import json
import time

try:
    from vpb_schema import validate_vpb_dict  # type: ignore
except Exception:  # pragma: no cover
    validate_vpb_dict = None  # type: ignore

try:
    from vpb_prompt_core import validate_vpb_json  # type: ignore
except Exception:  # pragma: no cover
    validate_vpb_json = None  # type: ignore


class MergeResult:
    def __init__(self, added_elements: int, added_connections: int, element_renames: dict[str,str], connection_renames: dict[str,str], warnings: list[str]|None=None):
        self.added_elements = added_elements
        self.added_connections = added_connections
        self.element_renames = element_renames
        self.connection_renames = connection_renames
        self.warnings = warnings or []

    def summary_lines(self) -> list[str]:
        lines = [f"Merge: {self.added_elements} Elemente, {self.added_connections} Verbindungen hinzugefügt"]
        if self.element_renames:
            lines.append("Element-Renames:")
            for o,n in self.element_renames.items():
                lines.append(f"  {o} -> {n}")
        if self.connection_renames:
            lines.append("Connection-Renames:")
            for o,n in self.connection_renames.items():
                lines.append(f"  {o} -> {n}")
        if self.warnings:
            lines.append("Warnungen:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        return lines


class CanvasLike:
    """Minimale Schnittstelle, die `VPBDesignerApp.canvas` bereitstellen muss.
    Diese Klasse dient nur der Typdokumentation.
    """
    elements: dict
    connections: dict

    def add_element(self, element_type: str, name: str, at: tuple[int,int], element_id: Optional[str]=None, push_undo: bool=True): ...  # pragma: no cover
    def add_connection(self, source_element: str, target_element: str, connection_type: str, name: str, connection_id: Optional[str]=None, push_undo: bool=True): ...  # pragma: no cover
    def push_undo(self): ...  # pragma: no cover
    def redraw_all(self): ...  # pragma: no cover


class MergeManager:
    def __init__(self, canvas: CanvasLike, telemetry: Any = None):
        self.canvas = canvas
        self._telemetry = telemetry  # erwartet .record(event_type, **fields)

    # Felder, die (direkt) Element-ID-Referenzen enthalten können (Heuristik)
    _REFERENCE_KEYS = {
        "source_element", "target_element", "members", "children", "parent", "group",
        "replaces", "replaced_by", "next", "prev", "ref", "subprocess", "called_process",
        "linked_element", "linked_elements"
    }

    @classmethod
    def _deep_rename(cls, obj: Any, rename_map: dict[str, str]):  # pragma: no cover (wird über öffentliche Methoden getestet)
        """Ersetze alle String-Vorkommen, die exakt einem alten Key entsprechen, rekursiv.
        Listen von Strings werden elementweise behandelt. Dict-Werte werden rekursiv traversiert.
        """
        if not rename_map:
            return obj
        try:
            if isinstance(obj, str):
                return rename_map.get(obj, obj)
            if isinstance(obj, list):
                return [cls._deep_rename(v, rename_map) for v in obj]
            if isinstance(obj, tuple):
                return tuple(cls._deep_rename(list(obj), rename_map))
            if isinstance(obj, dict):
                new_d = {}
                for k, v in obj.items():
                    # Nur rekursiv, wenn Key potentiell Referenzen enthält oder der Wert ein Container ist
                    if isinstance(v, (list, dict, tuple)) or k in cls._REFERENCE_KEYS or isinstance(v, str):
                        new_d[k] = cls._deep_rename(v, rename_map)
                    else:
                        new_d[k] = v
                return new_d
        except Exception:
            return obj
        return obj

    # Helfer
    @staticmethod
    def _next_free(base: str, taken: set[str]) -> str:
        if not base:
            base = "ID"
        if base not in taken:
            return base
        import re
        m = re.match(r"^(.*?)(?:_(\d+))?$", base)
        stem = m.group(1) if m else base
        i = 1
        while True:
            cand = f"{stem}_{i}"
            if cand not in taken:
                return cand
            i += 1

    # --- Öffentliche API ---
    def merge_full(self, data: dict, update_mode: str = "none", snap: bool=False, auto_rename: bool=True, grid: int=50, conflict_strategy: str = "skip") -> MergeResult:
        t0 = time.perf_counter()
        elems_in = data.get("elements") or []
        conns_in = data.get("connections") or []
        if not isinstance(elems_in, list) or not isinstance(conns_in, list):
            raise ValueError("Ungültige Struktur: elements/connections fehlen oder falscher Typ")

        existing_eids = set(self.canvas.elements.keys())
        existing_cids = set(self.canvas.connections.keys())
        rename_map_e: dict[str,str] = {}
        rename_map_c: dict[str,str] = {}

        # Vorprüfung bei deaktiviertem Auto-Rename (nur doppelte neue IDs erkennen)
        if not auto_rename:
            seen_new = set()
            for e in elems_in:
                if not isinstance(e, dict):
                    continue
                eid = e.get("element_id") or ""
                if not eid or eid in existing_eids:
                    continue
                if eid in seen_new:
                    raise ValueError(f"ID-Konflikt: Element-ID '{eid}' doppelt (Auto-Rename aus)")
                seen_new.add(eid)
            seen_conn = set()
            for c in conns_in:
                if not isinstance(c, dict):
                    continue
                cid = c.get("connection_id") or ""
                if not cid:
                    continue
                if cid in existing_cids or cid in seen_conn:
                    raise ValueError(f"ID-Konflikt: Connection-ID '{cid}' Konflikt (Auto-Rename aus)")
                seen_conn.add(cid)

        # Phase 1: Elemente
        new_elements_prepared = []
        for e in elems_in:
            if not isinstance(e, dict):
                continue
            eid = e.get("element_id") or ""
            if eid and eid in existing_eids:
                if update_mode in ("fill-empty", "overwrite"):
                    cur = self.canvas.elements.get(eid)
                    if cur:
                        def _maybe(attr: str, key: str):
                            if key not in e:
                                return
                            val = e.get(key)
                            if update_mode == "overwrite" or getattr(cur, attr, None) in (None, "", 0):
                                setattr(cur, attr, val if not isinstance(val, dict) else json.dumps(val, ensure_ascii=False))
                        _maybe("name", "name")
                        _maybe("description", "description")
                        _maybe("responsible_authority", "responsible_authority")
                        _maybe("legal_basis", "legal_basis")
                        if "deadline_days" in e:
                            try:
                                if update_mode == "overwrite" or getattr(cur, "deadline_days", 0) in (0, None):
                                    cur.deadline_days = int(e.get("deadline_days") or 0)
                            except Exception:
                                pass
                    continue
                # conflict strategy
                if conflict_strategy == "skip":
                    continue
                elif conflict_strategy == "duplicate":
                    if auto_rename:
                        new_id = self._next_free(eid, existing_eids | set(rename_map_e.values()))
                        rename_map_e[eid] = new_id
                        e = dict(e)
                        e["element_id"] = new_id
                    else:
                        continue
                else:
                    continue
            if eid and (eid in existing_eids or eid in rename_map_e.values()):
                if auto_rename:
                    new_id = self._next_free(eid, existing_eids | set(rename_map_e.values()))
                    rename_map_e[eid] = new_id
                    e = dict(e)
                    e["element_id"] = new_id
                else:
                    raise ValueError(f"ID-Konflikt (Element) '{eid}' (Auto-Rename aus)")
            new_elements_prepared.append(e)

        # Nach der ersten Phase: Deep Reference Rename innerhalb der neuen Elemente anwenden
        if auto_rename and rename_map_e:
            tmp = []
            for e in new_elements_prepared:
                if isinstance(e, dict):
                    tmp.append(self._deep_rename(e, rename_map_e))
                else:
                    tmp.append(e)
            new_elements_prepared = tmp

        # Phase 2: Connections (inkl. Deep Rename für verschachtelte Referenzen)
        new_connections_prepared = []
        valid_eids = existing_eids | {e.get("element_id") for e in new_elements_prepared if isinstance(e, dict)}
        for c in conns_in:
            if not isinstance(c, dict):
                continue
            cdict = dict(c)
            if auto_rename and rename_map_e:
                # Rekursive Ersetzung aller tiefen Referenzen
                cdict = self._deep_rename(cdict, rename_map_e)
            else:
                se = cdict.get("source_element")
                te = cdict.get("target_element")
                if se in rename_map_e:
                    cdict["source_element"] = rename_map_e[se]
                if te in rename_map_e:
                    cdict["target_element"] = rename_map_e[te]
            if cdict.get("source_element") not in valid_eids or cdict.get("target_element") not in valid_eids:
                continue
            cid = cdict.get("connection_id") or ""
            if cid and (cid in existing_cids or cid in rename_map_c.values()):
                if auto_rename:
                    new_cid = self._next_free(cid, existing_cids | set(rename_map_c.values()))
                    rename_map_c[cid] = new_cid
                    cdict["connection_id"] = new_cid
                else:
                    raise ValueError(f"ID-Konflikt (Connection) '{cid}' (Auto-Rename aus)")
            new_connections_prepared.append(cdict)

        # Anwenden
        self.canvas.push_undo()
        added_e = 0
        for e in new_elements_prepared:
            try:
                el = self.canvas.add_element(
                    e.get("element_type", "FUNCTION"),
                    name=e.get("name") or e.get("element_id") or "Neu",
                    at=(int(e.get("x", 0)), int(e.get("y", 0))),
                    element_id=e.get("element_id"),
                    push_undo=False,
                )
                el.description = e.get("description", "")
                el.responsible_authority = e.get("responsible_authority", "")
                el.legal_basis = e.get("legal_basis", "")
                try:
                    el.deadline_days = int(e.get("deadline_days", 0) or 0)
                except Exception:
                    el.deadline_days = 0
                # Zusatzattribute (wenn vorhanden) übernehmen
                for extra_key in ("members","children","parent","group","replaces","replaced_by","linked_elements"):
                    if extra_key in e:
                        try:
                            setattr(el, extra_key, e[extra_key])
                        except Exception:
                            pass
                added_e += 1
            except Exception:
                continue
        added_c = 0
        for c in new_connections_prepared:
            try:
                res = self.canvas.add_connection(
                    source_element=c.get("source_element"),
                    target_element=c.get("target_element"),
                    connection_type=c.get("connection_type", "SEQUENCE"),
                    name=c.get("description", ""),
                    connection_id=c.get("connection_id"),
                    push_undo=False,
                )
                if res:
                    added_c += 1
            except Exception:
                continue

        # Optional Snap
        if snap and added_e > 0:
            try:
                for e in new_elements_prepared:
                    if not isinstance(e, dict):
                        continue
                    eid = e.get("element_id")
                    obj = self.canvas.elements.get(eid)
                    if not obj:
                        continue
                    obj.x = int(round(obj.x / grid) * grid)
                    obj.y = int(round(obj.y / grid) * grid)
            except Exception:
                pass

        self.canvas.redraw_all()
        res_obj = MergeResult(added_e, added_c, rename_map_e, rename_map_c)
        if self._telemetry:
            try:
                self._telemetry.record(
                    "merge_full",
                    duration_s=round(time.perf_counter() - t0, 6),
                    added_elements=added_e,
                    added_connections=added_c,
                    element_renames=len(rename_map_e),
                    connection_renames=len(rename_map_c),
                    update_mode=update_mode,
                    snap=bool(snap),
                    auto_rename=bool(auto_rename),
                )
            except Exception:
                pass
        return res_obj

    def apply_add_only_patch(self, patch: dict, auto_rename: bool=True) -> MergeResult:
        t0 = time.perf_counter()
        elements = patch.get("elements") or []
        connections = patch.get("connections") or []
        if not elements and not connections:
            return MergeResult(0,0,{}, {}, ["Patch leer"])
        existing_eids = set(self.canvas.elements.keys())
        existing_cids = set(self.canvas.connections.keys())
        rename_map_e: dict[str,str] = {}
        rename_map_c: dict[str,str] = {}

        def _next(base: str, taken: set[str]) -> str:
            return self._next_free(base, taken)

        if not auto_rename:
            seen_e = set()
            for e in elements:
                if not isinstance(e, dict):
                    continue
                eid = e.get("element_id") or ""
                if not eid:
                    continue
                if eid in existing_eids or eid in seen_e:
                    raise ValueError(f"ID-Konflikt (Element) '{eid}' (Auto-Rename aus)")
                seen_e.add(eid)
            seen_c = set()
            for c in connections:
                if not isinstance(c, dict):
                    continue
                cid = c.get("connection_id") or ""
                if not cid:
                    continue
                if cid in existing_cids or cid in seen_c:
                    raise ValueError(f"ID-Konflikt (Connection) '{cid}' (Auto-Rename aus)")
                seen_c.add(cid)

        for e in elements:
            if not isinstance(e, dict):
                continue
            eid = e.get("element_id") or ""
            if not eid:
                continue
            if eid in existing_eids or eid in rename_map_e.values():
                if auto_rename:
                    new_id = _next(eid, existing_eids | set(rename_map_e.values()))
                    rename_map_e[eid] = new_id
                    e["element_id"] = new_id
                else:
                    raise ValueError(f"ID-Konflikt (Element) '{eid}' (Auto-Rename aus)")

        for c in connections:
            if not isinstance(c, dict):
                continue
            cid = c.get("connection_id") or ""
            if cid and (cid in existing_cids or cid in rename_map_c.values()):
                if auto_rename:
                    new_cid = _next(cid, existing_cids | set(rename_map_c.values()))
                    rename_map_c[cid] = new_cid
                    c["connection_id"] = new_cid
                else:
                    raise ValueError(f"ID-Konflikt (Connection) '{cid}' (Auto-Rename aus)")
            # Quell/Ziel ggf. umbenennen
            se = c.get("source_element")
            te = c.get("target_element")
            if se in rename_map_e:
                c["source_element"] = rename_map_e[se]
            if te in rename_map_e:
                c["target_element"] = rename_map_e[te]

        # Anwenden
        self.canvas.push_undo()
        added_e = 0
        # Deep Rename für Elemente vor dem Anwenden
        if auto_rename and rename_map_e:
            tmp = []
            for e in elements:
                if isinstance(e, dict):
                    tmp.append(self._deep_rename(e, rename_map_e))
                else:
                    tmp.append(e)
            elements = tmp

        for e in elements:
            try:
                el = self.canvas.add_element(
                    e.get("element_type", "FUNCTION"),
                    name=e.get("name") or e.get("element_id") or "Neu",
                    at=(int(e.get("x", 0)), int(e.get("y", 0))),
                    push_undo=False,
                )
                el.element_id = e.get("element_id", el.element_id)
                el.description = e.get("description", "")
                el.responsible_authority = e.get("responsible_authority", "")
                el.legal_basis = e.get("legal_basis", "")
                try:
                    el.deadline_days = int(e.get("deadline_days", 0) or 0)
                except Exception:
                    el.deadline_days = 0
                for extra_key in ("members","children","parent","group","replaces","replaced_by","linked_elements"):
                    if extra_key in e:
                        try:
                            setattr(el, extra_key, e[extra_key])
                        except Exception:
                            pass
                added_e += 1
            except Exception:
                continue
        added_c = 0
        for c in connections:
            try:
                if self.canvas.add_connection(
                    source_element=c.get("source_element"),
                    target_element=c.get("target_element"),
                    connection_type=c.get("connection_type", "SEQUENCE"),
                    name=c.get("description", ""),
                    connection_id=c.get("connection_id"),
                    push_undo=False,
                ):
                    added_c += 1
            except Exception:
                continue
        self.canvas.redraw_all()
        res_obj = MergeResult(added_e, added_c, rename_map_e, rename_map_c)
        if self._telemetry:
            try:
                self._telemetry.record(
                    "patch_add_only",
                    duration_s=round(time.perf_counter() - t0, 6),
                    added_elements=added_e,
                    added_connections=added_c,
                    element_renames=len(rename_map_e),
                    connection_renames=len(rename_map_c),
                    auto_rename=bool(auto_rename),
                )
            except Exception:
                pass
        return res_obj
