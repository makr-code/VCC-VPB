#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Orchestrierung: Auswahl und Injection von Default-Prozessbeispielen in Prompts

Funktionen
- build_prompt_with_examples_text_to_vpb: fügt Few‑Shot Beispiele der Text→Diagramm-Aufforderung hinzu
- build_prompt_with_examples_next_steps: fügt Beispiele in die Next‑Steps-Aufforderung ein

Einsatz
- Wird von der GUI/CLI vor dem Aufruf des Ollama‑Clients genutzt.
"""
from __future__ import annotations
from typing import Iterable, List, Dict

from ai_prompts import (
    build_text_to_vpb_prompt,
    build_next_steps_prompt,
    build_diagnose_fix_prompt,
    build_ingestion_prompt,
)
from vpb_default_processes import find_examples_by_tags, render_examples_snippet
from vpb_prompt_core import (
    build_prompt_with_examples_meta,
    validate_vpb_json,
    PromptMeta,
    notify_after_response,
)
from dataclasses import asdict


def build_prompt_with_examples_text_to_vpb(
    description: str,
    element_types: Iterable[str],
    connection_types: Iterable[str],
    example_tags: List[str] | None = None,
    max_examples: int = 3,
    return_meta: bool = False,
) -> str | tuple[str, PromptMeta]:
    """Erstellt Prompt für Text→VPB inkl. Few-Shot Beispiele.

    Rückwärtskompatibel: Standard-Rückgabe ist nur der Prompt-String.
    Bei return_meta=True wird (prompt, meta) zurückgegeben.
    """
    base = build_text_to_vpb_prompt(description, element_types, connection_types)
    examples = find_examples_by_tags(example_tags or [], max_examples=max_examples)
    prompt, meta = build_prompt_with_examples_meta(
        mode="text_to_vpb",
        base_prompt=base,
        examples=examples,
        example_tags=example_tags or [],
        tail_hint=(
            "Hinweis: Erzeuge ein vollständiges Prozess-JSON. Nutze neue IDs, halte das 50er Raster ein, verwende Defaultwerte statt Felder wegzulassen und kopiere nichts aus den Beispielen."
        ),
    )
    return (prompt, meta) if return_meta else prompt


def build_prompt_with_examples_next_steps(
    current_diagram_json: str,
    selected_element_id: str | None,
    element_types: Iterable[str],
    connection_types: Iterable[str],
    example_tags: List[str] | None = None,
    max_examples: int = 3,
    return_meta: bool = False,
) -> str | tuple[str, PromptMeta]:
    base = build_next_steps_prompt(current_diagram_json, selected_element_id, element_types, connection_types)
    examples = find_examples_by_tags(example_tags or [], max_examples=max_examples)
    prompt, meta = build_prompt_with_examples_meta(
        mode="next_steps",
        base_prompt=base,
        examples=examples,
        example_tags=example_tags or [],
        tail_hint=(
            "Hinweis: Liefere ausschließlich Add-Only Ergänzungen (elements/connections). Keine Modifikationen bestehender IDs und alle neuen Objekte vollständig befüllen."
        ),
    )
    return (prompt, meta) if return_meta else prompt


def build_prompt_with_examples_diagnose_fix(
    current_diagram_json: str,
    element_types: Iterable[str],
    connection_types: Iterable[str],
    example_tags: List[str] | None = None,
    max_examples: int = 3,
    return_meta: bool = False,
) -> str | tuple[str, PromptMeta]:
    base = build_diagnose_fix_prompt(current_diagram_json, element_types, connection_types)
    examples = find_examples_by_tags(example_tags or [], max_examples=max_examples)
    prompt, meta = build_prompt_with_examples_meta(
        mode="diagnose_fix",
        base_prompt=base,
        examples=examples,
        example_tags=example_tags or [],
        tail_hint=(
            "Hinweis: issues[] + optional patch (Add-Only). Keine Änderungen bestehender Objekte und vorgeschlagene Ergänzungen vollständig mit Defaultwerten ausstatten."
        ),
    )
    return (prompt, meta) if return_meta else prompt


def build_prompt_for_ingestion(
    sources_text: str,
    element_types: Iterable[str],
    connection_types: Iterable[str],
    *,
    prompt_context: str = "",
    current_diagram_summary: str = "",
    example_tags: List[str] | None = None,
    return_meta: bool = False,
) -> str | tuple[str, PromptMeta]:
    base = build_ingestion_prompt(
        sources_text,
        element_types,
        connection_types,
        prompt_context=prompt_context,
        current_diagram_summary=current_diagram_summary,
    )
    prompt, meta = build_prompt_with_examples_meta(
        mode="ingestion_diff",
        base_prompt=base,
        examples=[],
        example_tags=example_tags or [],
        tail_hint=(
            "Hinweis: Gib ausschließlich {\"elements\": [...], \"connections\": [...]} zurück."
            " Keine Änderungen an bestehenden IDs, keine Freitexterklärungen und alle Felder vollständig befüllen."
        ),
    )
    return (prompt, meta) if return_meta else prompt


# ---------------------------------------------------------------------------
# Hilfsfunktion für nachgelagerte Validierung von Modellantworten
# ---------------------------------------------------------------------------

def validate_model_output(
    raw_output: str,
    *,
    mode: str,
    existing_ids: Iterable[str] | None = None,
    allow_element_types: Iterable[str] | None = None,
    allow_connection_types: Iterable[str] | None = None,
    tolerance: str = "strict",
) -> dict:
    """Validiert eine Modellantwort & liefert strukturierte Issues.

    Rückgabe: dict mit keys: parsed (oder None), issues (Liste), fatal(bool)
    """
    result = validate_vpb_json(
        raw_output,
        mode=mode,
        existing_ids=set(existing_ids or []),
        allow_element_types=set(allow_element_types or []),
        allow_connection_types=set(allow_connection_types or []),
        tolerance=tolerance,
    )
    # ValidationIssue ist mit slots deklariert → kein __dict__; deshalb manuell/mit asdict serialisieren
    issues_serialised = []
    for i in result.issues:
        try:
            issues_serialised.append(asdict(i))  # dataclasses.asdict unterstützt slots
        except Exception:
            issues_serialised.append({"code": getattr(i, "code", "unknown"), "message": getattr(i, "message", ""), "severity": getattr(i, "severity", "warning")})
    return {"parsed": result.parsed, "issues": issues_serialised, "fatal": result.fatal, "repairs": result.repairs}


def finalize_response(meta: PromptMeta, raw_output: str, validation: dict | None) -> None:
    """Optionaler Convenience Wrapper für Hook-Notification."""
    if validation is not None:
        from vpb_prompt_core import ValidationResult, ValidationIssue  # Lazy import to avoid circular
        val_obj = ValidationResult(
            parsed=validation.get("parsed"),
            issues=[ValidationIssue(**iss) for iss in validation.get("issues", [])],
            fatal=validation.get("fatal", False),
            repairs=validation.get("repairs", []),
        )
    else:
        val_obj = None
    notify_after_response(meta, raw_output, val_obj)
