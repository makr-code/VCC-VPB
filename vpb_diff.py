#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validierung und Anwendung kleiner Diffs (nur Hinzufügen) auf ein VPB-Diagramm.
Diff-Format:
{
  "elements": [ { ... neue Elemente ... } ],
  "connections": [ { ... neue Verbindungen ... } ]
}
Nur Append; existierende IDs dürfen nicht kollidieren.
"""
from __future__ import annotations
from typing import Any, Dict, Iterable, Optional, Tuple


def validate_add_only_diff(diff: Any, existing_element_ids: Iterable[str],
                           allowed_element_types: Iterable[str], allowed_connection_types: Iterable[str]) -> Tuple[bool, Optional[str]]:
    if not isinstance(diff, dict):
        return False, "Diff ist kein Objekt"
    els = diff.get("elements", [])
    cons = diff.get("connections", [])
    if not isinstance(els, list) or not isinstance(cons, list):
        return False, "elements/connections im Diff müssen Listen sein"
    existing = set(existing_element_ids)
    ae = set(allowed_element_types)
    ac = set(allowed_connection_types)
    # Elemente prüfen
    for i, e in enumerate(els):
        if not isinstance(e, dict):
            return False, f"elements[{i}] ist kein Objekt"
        eid = e.get("element_id")
        if not isinstance(eid, str) or not eid:
            return False, f"elements[{i}].element_id fehlt/kein string"
        if eid in existing:
            return False, f"elements[{i}].element_id kollidiert mit bestehendem Element"
        et = e.get("element_type")
        if not isinstance(et, str) or et not in ae:
            return False, f"elements[{i}].element_type '{et}' nicht erlaubt"
    # Verbindungen prüfen (nur Referenzen auf existierende oder neue Elemente)
    new_ids = existing.union({e.get("element_id") for e in els if isinstance(e, dict)})
    for i, c in enumerate(cons):
        if not isinstance(c, dict):
            return False, f"connections[{i}] ist kein Objekt"
        ctype = c.get("connection_type", "SEQUENCE")
        if not isinstance(ctype, str) or ctype not in ac:
            return False, f"connections[{i}].connection_type '{ctype}' nicht erlaubt"
        src = c.get("source_element")
        tgt = c.get("target_element")
        if not isinstance(src, str) or not isinstance(tgt, str):
            return False, f"connections[{i}].source/target müssen strings sein"
        if src not in new_ids or tgt not in new_ids:
            return False, f"connections[{i}] referenziert unbekannte Elemente"
    return True, None


def apply_add_only_diff(doc: Dict[str, Any], diff: Dict[str, Any]) -> Dict[str, Any]:
    out = {
        "metadata": dict(doc.get("metadata", {})),
        "elements": [*doc.get("elements", [])],
        "connections": [*doc.get("connections", [])],
    }
    out["elements"].extend(diff.get("elements", []))
    out["connections"].extend(diff.get("connections", []))
    return out
