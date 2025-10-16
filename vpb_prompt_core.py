#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zentrale Bausteine für Prompt-Erzeugung & Validierung.

Funktionen & Klassen (Schritt 1–6 Verbesserungen):
 - PromptMeta / ValidationIssue / ValidationResult
 - PromptRegistry (Versionierung & Basis-Fragmente)
 - sanitize_text(), strip_code_fences()
 - build_prompt_with_examples_meta(): Generischer Builder mit Metadaten
 - validate_vpb_json(): Struktur-/Add-Only-Prüfung & Leck-Erkennung
 - Hook-Mechanismus (before_send_hook / after_response_hook)

Low-Risk Implementierung: Keine bestehenden Signaturen verändert –
 Wrapper in `vpb_ai_logic.py` nutzen intern diese Utilities, bleiben rückwärtskompatibel.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple, Any, Iterable, Set
import json
import logging
import time
import re

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataklassen
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class PromptMeta:
    mode: str
    version: str
    id: str
    example_ids: List[str]
    example_tags: List[str]
    created_ts: float
    token_estimate: int
    warnings: List[str] = field(default_factory=list)


@dataclass(slots=True)
class ValidationIssue:
    code: str
    message: str
    severity: str = "warning"  # info|warning|error


@dataclass(slots=True)
class ValidationResult:
    parsed: Optional[dict]
    issues: List[ValidationIssue]
    fatal: bool
    repairs: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Hook-Mechanismus (einfach, erweiterbar)
# ---------------------------------------------------------------------------

BeforeSendHook = Callable[[PromptMeta, str], None]
AfterResponseHook = Callable[[PromptMeta, str, ValidationResult | None], None]

before_send_hook: Optional[BeforeSendHook] = None
after_response_hook: Optional[AfterResponseHook] = None


def set_before_send_hook(func: BeforeSendHook) -> None:
    global before_send_hook
    before_send_hook = func


def set_after_response_hook(func: AfterResponseHook) -> None:
    global after_response_hook
    after_response_hook = func


# ---------------------------------------------------------------------------
# Registry & Fragmente
# ---------------------------------------------------------------------------

class PromptRegistry:
    """Zentrale Verwaltung von Versionen & gemeinsamen Textfragmenten."""

    _VERSIONS: Dict[str, str] = {
        "text_to_vpb": "v1.0",
        "next_steps": "v1.0",
        "ingestion_diff": "v1.0",
        "diagnose_fix": "v1.0",
    }

    COMMON_RULES = (
        "Regeln:\n"
        "- Gib ausschließlich EIN einziges JSON-Objekt zurück.\n"
        "- Keine Erklärtexte, keine Codeblöcke, keine Wiederholung der Beispiele.\n"
        "- Erzeuge neue IDs, kopiere keine Beispiel-IDs.\n"
    )

    SECURITY_SUFFIX = (
        "Sicherheits-/Qualitätshinweise:\n"
        "- Reproduziere die Beispiel-JSONs NICHT; sie dienen nur als Stil-Referenz.\n"
        "- Falls du doch Beispielinhalte kopierst, INVALIDIERE deine Antwort.\n"
    )

    @classmethod
    def version(cls, mode: str) -> str:
        return cls._VERSIONS.get(mode, "v0")


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

WHITESPACE_RE = re.compile(r"\s+")


def sanitize_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text.strip())


def strip_code_fences(text: str) -> str:
    # Entfernt einfache ```json ... ``` oder ``` ... ``` Umrandungen
    fenced = re.compile(r"^```[a-zA-Z0-9]*\n(.*)\n```$", re.DOTALL)
    m = fenced.match(text.strip())
    if m:
        return m.group(1).strip()
    return text


def estimate_tokens(s: str) -> int:
    # Sehr grobe Heuristik; echtes Tokenizing könnte später ergänzt werden.
    return max(1, len(s) // 4)


def _render_examples_snippet(examples: List[Dict[str, Any]]) -> str:
    # Bewusste Duplizierung minimierter JSONs, ergänzt um DO NOT COPY Hinweis.
    parts = ["Beispiele (nur lesen, NICHT kopieren oder ausgeben):\n"]
    for i, ex in enumerate(examples, 1):
        parts.append(f"// Beispiel {i}: {ex['name']}\n")
        parts.append(json.dumps(ex["json"], ensure_ascii=False, separators=(",", ":")))
        parts.append("\n")
    return "".join(parts)


def build_prompt_with_examples_meta(
    *,
    mode: str,
    base_prompt: str,
    examples: List[Dict[str, Any]],
    example_tags: List[str],
    tail_hint: str,
) -> Tuple[str, PromptMeta]:
    examples_snippet = _render_examples_snippet(examples)
    full_prompt = (
        examples_snippet
        + "\n\n"
        + PromptRegistry.COMMON_RULES
        + "\n"
        + base_prompt.strip()
        + "\n\n"
        + tail_hint.strip()
        + "\n\n"
        + PromptRegistry.SECURITY_SUFFIX
    )
    meta = PromptMeta(
        mode=mode,
        version=PromptRegistry.version(mode),
        id=f"{mode}:{PromptRegistry.version(mode)}",
        example_ids=[ex["id"] for ex in examples],
        example_tags=example_tags,
        created_ts=time.time(),
        token_estimate=estimate_tokens(full_prompt),
    )

    if before_send_hook:
        try:
            before_send_hook(meta, full_prompt)
        except Exception:  # pragma: no cover - Schutz
            logger.exception("before_send_hook Fehler ignoriert")
    return full_prompt, meta


# ---------------------------------------------------------------------------
# Validierung
# ---------------------------------------------------------------------------

def validate_vpb_json(
    raw_output: str,
    *,
    mode: str,
    existing_ids: Optional[Set[str]] = None,
    allow_element_types: Optional[Set[str]] = None,
    allow_connection_types: Optional[Set[str]] = None,
    tolerance: str = "strict",
) -> ValidationResult:
    issues: List[ValidationIssue] = []
    fatal = False
    repairs: List[str] = []
    tolerant = tolerance.lower() != "strict"
    cleaned = strip_code_fences(raw_output).strip()

    # Leck-Erkennung
    if "Beispiele (nur lesen" in cleaned:
        issues.append(ValidationIssue("leak.examples_echo", "Antwort enthält Beispiel-Snippet – sollte nicht reproduziert werden", "error"))

    # Erstes JSON grob extrahieren (suche erstes '{' und letztes '}')
    try:
        start = cleaned.index('{')
        end = cleaned.rfind('}')
        candidate = cleaned[start:end+1]
    except ValueError:
        issues.append(ValidationIssue("json.missing_braces", "Keine JSON-Klammern gefunden", "error"))
        return ValidationResult(None, issues, True)

    try:
        parsed = json.loads(candidate)
    except Exception as exc:  # noqa: BLE001
        issues.append(ValidationIssue("json.parse_error", f"JSON Parse-Fehler: {exc}", "error"))
        return ValidationResult(None, issues, True)

    # Mode-spezifische Root-Prüfung
    def _register_missing_field(key: str, default_value: Any | None = None) -> None:
        if tolerant and default_value is not None:
            parsed[key] = default_value
            repairs.append(f"{key} ergänzt (lenient mode)")
            issues.append(ValidationIssue("schema.missing_field", f"Feld '{key}' fehlte – automatisch ergänzt", "warning"))
        else:
            issues.append(ValidationIssue("schema.missing_field", f"Feld '{key}' fehlt", "error"))

    if mode == "text_to_vpb":
        if "metadata" not in parsed:
            _register_missing_field("metadata", {"name": "", "description": ""})
        if "elements" not in parsed:
            _register_missing_field("elements", [])
        if "connections" not in parsed:
            _register_missing_field("connections", [])
    elif mode in {"next_steps", "ingestion_diff"}:
        allowed_keys = {"elements", "connections"}
        extra = set(parsed.keys()) - allowed_keys
        if extra:
            issues.append(ValidationIssue("schema.extra_keys", f"Unerlaubte Root-Felder: {sorted(extra)}", "warning"))
        for key in allowed_keys:
            if key not in parsed:
                _register_missing_field(key, [])
    elif mode == "diagnose_fix":
        if "issues" not in parsed:
            _register_missing_field("issues", [])
        if "patch" not in parsed:
            _register_missing_field("patch", {"elements": [], "connections": []})
    else:
        issues.append(ValidationIssue("mode.unknown", f"Unbekannter Modus '{mode}'", "error"))

    # Add-Only Check (simple): neue IDs dürfen existierende nicht überschreiben
    if existing_ids and mode in {"next_steps", "diagnose_fix", "ingestion_diff"}:
        # Sammle evtl. neue Elemente / Verbindungen
        candidate_elements = []
        candidate_connections = []
        if mode in {"next_steps", "ingestion_diff"}:
            candidate_elements = parsed.get("elements", [])
            candidate_connections = parsed.get("connections", [])
        elif mode == "diagnose_fix":
            patch = parsed.get("patch", {}) or {}
            candidate_elements = patch.get("elements", [])
            candidate_connections = patch.get("connections", [])
        for e in candidate_elements:
            eid = e.get("element_id")
            if eid in existing_ids:
                issues.append(ValidationIssue("add_only.element_id_conflict", f"Element-ID '{eid}' bereits vorhanden", "error"))
        for c in candidate_connections:
            cid = c.get("connection_id")
            if cid in existing_ids:
                issues.append(ValidationIssue("add_only.connection_id_conflict", f"Connection-ID '{cid}' bereits vorhanden", "error"))

    # Typ-Prüfung (optional)
    if allow_element_types and "elements" in parsed:
        for e in parsed.get("elements", []) or []:
            etype = e.get("element_type")
            if etype and etype not in allow_element_types:
                issues.append(ValidationIssue("element_type.invalid", f"Unerlaubter element_type '{etype}'", "warning"))
    # Connections Types
    if allow_connection_types and "connections" in parsed:
        for c in parsed.get("connections", []) or []:
            ctype = c.get("connection_type")
            if ctype and ctype not in allow_connection_types:
                issues.append(ValidationIssue("connection_type.invalid", f"Unerlaubter connection_type '{ctype}'", "warning"))

    # Sanitizing optional Felder in tolerantem Modus
    def _apply_optional_defaults(elements: Any) -> Any:
        if not tolerant:
            return elements
        changed = False
        if isinstance(elements, list):
            for elem in elements:
                if not isinstance(elem, dict):
                    continue
                if elem.get("description") is None:
                    elem["description"] = ""
                    changed = True
                if elem.get("responsible_authority") is None:
                    elem["responsible_authority"] = "unbekannt"
                    changed = True
                if elem.get("legal_basis") is None:
                    elem["legal_basis"] = "n.n."
                    changed = True
                if elem.get("geo_reference") is None:
                    elem["geo_reference"] = ""
                    changed = True
                if elem.get("deadline_days") is None:
                    elem["deadline_days"] = 0
                    changed = True
                else:
                    try:
                        elem["deadline_days"] = int(elem["deadline_days"])
                    except Exception:
                        elem["deadline_days"] = 0
                        changed = True
                for coord in ("x", "y"):
                    if coord in elem:
                        try:
                            elem[coord] = int(elem[coord])
                        except Exception:
                            elem[coord] = 0
                            changed = True
        if changed:
            repairs.append("elements: optionale Felder ergänzt (lenient)")
        return elements

    def _apply_connection_defaults(conns: Any) -> Any:
        if not tolerant:
            return conns
        changed = False
        if isinstance(conns, list):
            for conn in conns:
                if not isinstance(conn, dict):
                    continue
                if conn.get("description") is None:
                    conn["description"] = ""
                    changed = True
        if changed:
            repairs.append("connections: optionale Felder ergänzt (lenient)")
        return conns

    if tolerant:
        if mode in {"text_to_vpb", "next_steps", "ingestion_diff"}:
            parsed["elements"] = _apply_optional_defaults(parsed.get("elements", []))
            parsed["connections"] = _apply_connection_defaults(parsed.get("connections", []))
        elif mode == "diagnose_fix":
            patch = parsed.get("patch", {})
            if isinstance(patch, dict):
                patch["elements"] = _apply_optional_defaults(patch.get("elements", []))
                patch["connections"] = _apply_connection_defaults(patch.get("connections", []))

    # Raster-Prüfung (informativ)
    def _check_pos(e: dict) -> None:
        x = e.get("x")
        y = e.get("y")
        if isinstance(x, int) and isinstance(y, int):
            if (x % 50) != 0 or (y % 50) != 0:
                issues.append(ValidationIssue("layout.off_raster", f"Element {e.get('element_id')} nicht im 50er Raster", "info"))

    if mode == "text_to_vpb":
        for e in parsed.get("elements", []) or []:
            _check_pos(e)
    elif mode in {"next_steps", "ingestion_diff"}:
        for e in parsed.get("elements", []) or []:
            _check_pos(e)
    elif mode == "diagnose_fix":
        patch = parsed.get("patch", {}) or {}
        for e in patch.get("elements", []) or []:
            _check_pos(e)

    fatal = any(i.severity == "error" for i in issues)
    result = ValidationResult(parsed if not fatal else parsed, issues, fatal, repairs)
    return result


def notify_after_response(meta: PromptMeta, raw_output: str, validation: ValidationResult | None) -> None:
    if after_response_hook:
        try:
            after_response_hook(meta, raw_output, validation)
        except Exception:  # pragma: no cover
            logger.exception("after_response_hook Fehler ignoriert")
