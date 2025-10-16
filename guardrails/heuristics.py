from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

GridSize = 50
Severity = str
Scope = str

VALID_SEVERITIES: Set[str] = {"info", "warning", "error"}
VALID_SCOPES: Set[str] = {"diagram", "diff"}


@dataclass(slots=True)
class GuardrailIssue:
    """Describes a single guardrail finding."""

    code: str
    message: str
    severity: Severity = "warning"
    scope: Scope = "diagram"
    location: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(f"invalid severity '{self.severity}'")
        if self.scope not in VALID_SCOPES:
            raise ValueError(f"invalid scope '{self.scope}'")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "scope": self.scope,
            "location": self.location or {},
        }


def _normalize_name(name: Any) -> Optional[str]:
    if not isinstance(name, str):
        return None
    stripped = name.strip()
    if not stripped:
        return None
    return stripped.casefold()


def _is_function_like(element: Dict[str, Any]) -> bool:
    etype = element.get("element_type")
    if not isinstance(etype, str):
        return False
    etype_upper = etype.upper()
    return etype_upper in {"FUNCTION", "TASK", "PROCESS", "SUBPROCESS", "ACTIVITY"}


def _scope_for_id(item_id: str, diff_ids: Set[str]) -> Scope:
    return "diff" if item_id in diff_ids else "diagram"


def run_guardrail_checks(
    base_diagram: Dict[str, Any],
    *,
    diff: Optional[Dict[str, Any]] = None,
) -> List[GuardrailIssue]:
    """Run guardrail heuristics against the current diagram and optional diff.

    The diff is expected to be add-only.
    """

    base_elements = list(base_diagram.get("elements", []) or []) if isinstance(base_diagram, dict) else []
    base_connections = list(base_diagram.get("connections", []) or []) if isinstance(base_diagram, dict) else []

    diff_elements: List[Dict[str, Any]] = []
    diff_connections: List[Dict[str, Any]] = []
    if isinstance(diff, dict):
        diff_elements = [e for e in diff.get("elements", []) or [] if isinstance(e, dict)]
        diff_connections = [c for c in diff.get("connections", []) or [] if isinstance(c, dict)]

    combined_elements = base_elements + diff_elements
    combined_connections = base_connections + diff_connections

    diff_element_ids = {str(e.get("element_id")) for e in diff_elements if isinstance(e.get("element_id"), str)}
    diff_connection_ids = {str(c.get("connection_id")) for c in diff_connections if isinstance(c.get("connection_id"), str)}

    issues: List[GuardrailIssue] = []

    # Duplicate element IDs
    seen_element_ids: Dict[str, str] = {}
    for elem in combined_elements:
        eid = elem.get("element_id")
        if not isinstance(eid, str) or not eid:
            continue
        if eid in seen_element_ids:
            issues.append(
                GuardrailIssue(
                    code="element.id.duplicate",
                    message=f"Element-ID '{eid}' kommt mehrfach vor",
                    severity="error",
                    scope=_scope_for_id(eid, diff_element_ids),
                    location={"element_id": eid},
                )
            )
        else:
            seen_element_ids[eid] = eid

    # Duplicate connection IDs
    seen_connection_ids: Dict[str, str] = {}
    for con in combined_connections:
        cid = con.get("connection_id")
        if not isinstance(cid, str) or not cid:
            continue
        if cid in seen_connection_ids:
            issues.append(
                GuardrailIssue(
                    code="connection.id.duplicate",
                    message=f"Connection-ID '{cid}' kommt mehrfach vor",
                    severity="error",
                    scope=_scope_for_id(cid, diff_connection_ids),
                    location={"connection_id": cid},
                )
            )
        else:
            seen_connection_ids[cid] = cid

    # Duplicate element names (case insensitive)
    names: Dict[str, List[str]] = {}
    original_names: Dict[str, str] = {}
    for elem in combined_elements:
        eid = elem.get("element_id")
        if not isinstance(eid, str) or not eid:
            continue
        normalized = _normalize_name(elem.get("name"))
        if normalized is None:
            continue
        names.setdefault(normalized, []).append(eid)
        if normalized not in original_names and isinstance(elem.get("name"), str):
            original_names[normalized] = elem["name"].strip()

    for normalized, ids in names.items():
        if len(ids) <= 1:
            continue
        any_diff = any(item_id in diff_element_ids for item_id in ids)
        scope: Scope = "diff" if any_diff else "diagram"
        issues.append(
            GuardrailIssue(
                code="element.name.duplicate",
                message=f"Element-Name '{original_names.get(normalized, normalized)}' ist nicht eindeutig",
                severity="warning",
                scope=scope,
                location={"element_ids": ids,
                         "name": original_names.get(normalized, normalized)},
            )
        )

    # Missing element names
    for elem in combined_elements:
        eid = elem.get("element_id")
        if not isinstance(eid, str) or not eid:
            continue
        name_value = elem.get("name")
        if _normalize_name(name_value) is None:
            issues.append(
                GuardrailIssue(
                    code="element.name.missing",
                    message=f"Element '{eid}' hat keinen Namen",
                    severity="warning",
                    scope=_scope_for_id(eid, diff_element_ids),
                    location={"element_id": eid},
                )
            )

    # Off-grid positions
    for elem in combined_elements:
        eid = elem.get("element_id")
        if not isinstance(eid, str) or not eid:
            continue
        x = elem.get("x")
        y = elem.get("y")
        if isinstance(x, int) and isinstance(y, int):
            if (x % GridSize) != 0 or (y % GridSize) != 0:
                issues.append(
                    GuardrailIssue(
                        code="element.position.off_grid",
                        message=f"Element '{eid}' liegt nicht auf dem {GridSize}er Raster",
                        severity="info",
                        scope=_scope_for_id(eid, diff_element_ids),
                        location={"element_id": eid, "x": x, "y": y},
                    )
                )

    element_id_set = {elem.get("element_id") for elem in combined_elements if isinstance(elem.get("element_id"), str)}

    # Connection integrity checks
    pair_seen: Set[Tuple[str, str, Optional[str]]] = set()
    connection_touch_count: Dict[str, int] = {eid: 0 for eid in element_id_set}

    for con in combined_connections:
        cid = con.get("connection_id")
        src = con.get("source_element")
        tgt = con.get("target_element")
        ctype = con.get("connection_type")
        scope = _scope_for_id(str(cid) if isinstance(cid, str) else "", diff_connection_ids) if cid else "diagram"
        if not isinstance(src, str) or not isinstance(tgt, str):
            issues.append(
                GuardrailIssue(
                    code="connection.endpoint.invalid",
                    message=f"Verbindung '{cid or '(ohne ID)'}' hat ungültige Endpunkte",
                    severity="error",
                    scope=scope,
                    location={"connection_id": cid},
                )
            )
            continue
        if src not in element_id_set or tgt not in element_id_set:
            issues.append(
                GuardrailIssue(
                    code="connection.endpoint.missing",
                    message=f"Verbindung '{cid or '(ohne ID)'}' referenziert unbekannte Elemente",
                    severity="error",
                    scope=scope,
                    location={"connection_id": cid, "source": src, "target": tgt},
                )
            )
            continue
        connection_touch_count[src] = connection_touch_count.get(src, 0) + 1
        connection_touch_count[tgt] = connection_touch_count.get(tgt, 0) + 1
        if src == tgt:
            issues.append(
                GuardrailIssue(
                    code="connection.self_loop",
                    message=f"Verbindung '{cid or '(ohne ID)'}' bildet eine Schleife auf Element '{src}'",
                    severity="warning",
                    scope=scope,
                    location={"connection_id": cid, "element_id": src},
                )
            )
        pair_signature = (src, tgt, str(ctype) if isinstance(ctype, str) else None)
        if pair_signature in pair_seen:
            issues.append(
                GuardrailIssue(
                    code="connection.duplicate_pair",
                    message=f"Verbindung '{cid or '(ohne ID)'}' dupliziert eine bestehende Relation {src}->{tgt}",
                    severity="warning",
                    scope=scope,
                    location={"connection_id": cid, "source": src, "target": tgt},
                )
            )
        else:
            pair_seen.add(pair_signature)

    # Unconnected function-like elements
    for elem in combined_elements:
        eid = elem.get("element_id")
        if not isinstance(eid, str) or not eid:
            continue
        if not _is_function_like(elem):
            continue
        if connection_touch_count.get(eid, 0) == 0:
            issues.append(
                GuardrailIssue(
                    code="function.unconnected",
                    message=f"Funktionales Element '{eid}' ist weder verbunden noch erreichbar",
                    severity="warning",
                    scope=_scope_for_id(eid, diff_element_ids),
                    location={"element_id": eid},
                )
            )

    return issues


def summarize_guardrail_issues(issues: Iterable[GuardrailIssue]) -> Dict[str, int]:
    summary = {"error": 0, "warning": 0, "info": 0}
    for issue in issues:
        summary[issue.severity] = summary.get(issue.severity, 0) + 1
    summary["total"] = sum(summary.values())
    return summary
