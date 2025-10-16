#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einfache Validierung für das VPB-JSON-Format.
- optional mit erlaubten Typen (Element/Connection) zur strikteren Prüfung
"""
from __future__ import annotations
from typing import Any, Dict, Iterable, Optional, Tuple


def _is_int(x: Any) -> bool:
    try:
        int(x)
        return True
    except Exception:
        return False


def validate_vpb_dict(
    data: Any,
    allowed_element_types: Optional[Iterable[str]] = None,
    allowed_connection_types: Optional[Iterable[str]] = None,
) -> Tuple[bool, Optional[str]]:
    if not isinstance(data, dict):
        return False, "Wurzel ist kein Objekt"

    # metadata
    md = data.get("metadata", {})
    if not isinstance(md, dict):
        return False, "metadata fehlt oder ist kein Objekt"
    if "name" in md and not isinstance(md.get("name"), str):
        return False, "metadata.name muss string sein"
    if "description" in md and not isinstance(md.get("description"), str):
        return False, "metadata.description muss string sein"

    # elements
    els = data.get("elements")
    if els is None or not isinstance(els, list):
        return False, "elements fehlt oder ist keine Liste"
    ids = set()

    ae = set(allowed_element_types) if allowed_element_types is not None else None

    for idx, e in enumerate(els):
        if not isinstance(e, dict):
            return False, f"elements[{idx}] ist kein Objekt"
        eid = e.get("element_id")
        if not isinstance(eid, str) or not eid:
            return False, f"elements[{idx}].element_id fehlt/kein string"
        if eid in ids:
            return False, f"elements[{idx}].element_id nicht eindeutig"
        ids.add(eid)
        et = e.get("element_type")
        if not isinstance(et, str) or not et:
            return False, f"elements[{idx}].element_type fehlt/kein string"
        if ae is not None and et not in ae:
            return False, f"elements[{idx}].element_type '{et}' ist nicht erlaubt"
        if not isinstance(e.get("name", ""), str):
            return False, f"elements[{idx}].name muss string sein"
        if not _is_int(e.get("x")) or not _is_int(e.get("y")):
            return False, f"elements[{idx}].x/y müssen integer sein"
        # optionale Felder: description, responsible_authority, legal_basis, deadline_days, geo_reference
        if "deadline_days" in e and not _is_int(e.get("deadline_days")):
            return False, f"elements[{idx}].deadline_days muss integer sein"

    # connections
    cons = data.get("connections")
    if cons is None or not isinstance(cons, list):
        return False, "connections fehlt oder ist keine Liste"

    ac = set(allowed_connection_types) if allowed_connection_types is not None else None

    for idx, c in enumerate(cons):
        if not isinstance(c, dict):
            return False, f"connections[{idx}] ist kein Objekt"
        cid = c.get("connection_id")
        if not isinstance(cid, str) or not cid:
            return False, f"connections[{idx}].connection_id fehlt/kein string"
        src = c.get("source_element")
        tgt = c.get("target_element")
        if not isinstance(src, str) or not isinstance(tgt, str):
            return False, f"connections[{idx}].source/target müssen strings sein"
        if src not in ids or tgt not in ids:
            return False, f"connections[{idx}] referenziert unbekannte Elemente"
        ctype = c.get("connection_type", "SEQUENCE")
        if not isinstance(ctype, str) or not ctype:
            return False, f"connections[{idx}].connection_type muss string sein"
        if ac is not None and ctype not in ac:
            return False, f"connections[{idx}].connection_type '{ctype}' ist nicht erlaubt"
    return True, None
