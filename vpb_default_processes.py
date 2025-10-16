#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kurzbibliothek: Basic/Default VPB-Prozesse als Few‑Shot‑Beispiele für LLMs

Zweck
- Kleine, saubere Referenzprozesse als Kontext für:
  - Text→Diagramm (Generierung)
  - Nächste Schritte (Erweiterung)
  - Diagnose/Fix (Erkennung typischer Fehler + Add‑only Vorschläge)

Nutzung
- Über vpb_ai_logic.select_examples_* auswählen und als Prompt-Beispiele injizieren.
"""
from __future__ import annotations
from typing import List, Dict, Any


# Minimale, konsistente JSON-Beispiele (x,y im 50er Raster, SEQUENCE-Fluss)
# Hinweis: Nur erlaubte Typ-Strings verwenden, die im Projekt verstanden werden.

DEFAULT_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "antrag_minimal",
        "name": "Antrag – Minimaler Ablauf",
        "tags": ["antrag", "standard", "sequence", "entscheidung"],
        "json": {
            "metadata": {"name": "Antrag – Minimal", "description": "Einreichen, prüfen, entscheiden, bescheiden"},
            "elements": [
                {"element_id": "S1", "element_type": "START_EVENT", "name": "Start", "x": 50, "y": 50, "description": "", "responsible_authority": "Bürgerbüro", "legal_basis": "§ 35 VwVfG", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "F1", "element_type": "FUNCTION", "name": "Antrag prüfen", "x": 200, "y": 50, "description": "Formale und materielle Prüfung", "responsible_authority": "Sachbearbeitung", "legal_basis": "§ 24 VwVfG", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "G1", "element_type": "GATEWAY", "name": "Voraussetzungen erfüllt?", "x": 350, "y": 50, "description": "Entscheidung", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "F2", "element_type": "FUNCTION", "name": "Bescheid erstellen", "x": 500, "y": 20, "description": "Positiver Bescheid", "responsible_authority": "Sachbearbeitung", "legal_basis": "§ 39 VwVfG", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "F3", "element_type": "FUNCTION", "name": "Ablehnungsbescheid erstellen", "x": 500, "y": 80, "description": "Negativer Bescheid", "responsible_authority": "Sachbearbeitung", "legal_basis": "§ 39 VwVfG", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "E1", "element_type": "END_EVENT", "name": "Ende", "x": 650, "y": 50, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""}
            ],
            "connections": [
                {"connection_id": "C1", "source_element": "S1", "target_element": "F1", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C2", "source_element": "F1", "target_element": "G1", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C3", "source_element": "G1", "target_element": "F2", "connection_type": "SEQUENCE", "description": "Ja"},
                {"connection_id": "C4", "source_element": "G1", "target_element": "F3", "connection_type": "SEQUENCE", "description": "Nein"},
                {"connection_id": "C5", "source_element": "F2", "target_element": "E1", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C6", "source_element": "F3", "target_element": "E1", "connection_type": "SEQUENCE", "description": ""}
            ]
        }
    },
    {
        "id": "widerspruch_basic",
        "name": "Widerspruch – Basis",
        "tags": ["widerspruch", "vwg0", "standard", "bescheid"],
        "json": {
            "metadata": {"name": "Widerspruch – Basis", "description": "Eingang, Prüfung, Entscheidung, Bescheid"},
            "elements": [
                {"element_id": "S1", "element_type": "START_EVENT", "name": "Widerspruch eingegangen", "x": 50, "y": 150, "description": "", "responsible_authority": "Rechtsbehelfsstelle", "legal_basis": "§ 68 VwGO", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "F1", "element_type": "FUNCTION", "name": "Zulässigkeit & Begründetheit prüfen", "x": 220, "y": 150, "description": "", "responsible_authority": "Rechtsbehelfsstelle", "legal_basis": "§ 70 VwGO", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "G1", "element_type": "GATEWAY", "name": "Abhilfe?", "x": 390, "y": 150, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "F2", "element_type": "FUNCTION", "name": "Abhilfebescheid", "x": 560, "y": 120, "description": "", "responsible_authority": "Ausgangsbehörde", "legal_basis": "§ 68 VwGO", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "F3", "element_type": "FUNCTION", "name": "Widerspruchsbescheid", "x": 560, "y": 180, "description": "", "responsible_authority": "Widerspruchsbehörde", "legal_basis": "§ 73 VwGO", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "E1", "element_type": "END_EVENT", "name": "Ende", "x": 730, "y": 150, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""}
            ],
            "connections": [
                {"connection_id": "C1", "source_element": "S1", "target_element": "F1", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C2", "source_element": "F1", "target_element": "G1", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C3", "source_element": "G1", "target_element": "F2", "connection_type": "SEQUENCE", "description": "Ja"},
                {"connection_id": "C4", "source_element": "G1", "target_element": "F3", "connection_type": "SEQUENCE", "description": "Nein"},
                {"connection_id": "C5", "source_element": "F2", "target_element": "E1", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C6", "source_element": "F3", "target_element": "E1", "connection_type": "SEQUENCE", "description": ""}
            ]
        }
    },
    {
        "id": "frist_escalation",
        "name": "Frist & Eskalation – Basis",
        "tags": ["frist", "deadline", "escalation"],
        "json": {
            "metadata": {"name": "Frist & Eskalation", "description": "Frist setzen, überwachen, eskalieren"},
            "elements": [
                {"element_id": "S1", "element_type": "START_EVENT", "name": "Start", "x": 50, "y": 250, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "F1", "element_type": "DEADLINE", "name": "Frist setzen (14 Tage)", "x": 200, "y": 250, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 14, "geo_reference": ""},
                {"element_id": "F2", "element_type": "FUNCTION", "name": "Frist überwachen", "x": 350, "y": 250, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "G1", "element_type": "GATEWAY", "name": "Frist abgelaufen?", "x": 500, "y": 250, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "F3", "element_type": "FUNCTION", "name": "Eskalation an Teamleitung", "x": 650, "y": 220, "description": "", "responsible_authority": "Teamleitung", "legal_basis": "", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "F4", "element_type": "FUNCTION", "name": "Bearbeitung fortsetzen", "x": 650, "y": 280, "description": "", "responsible_authority": "Sachbearbeitung", "legal_basis": "", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "E1", "element_type": "END_EVENT", "name": "Ende", "x": 800, "y": 250, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""}
            ],
            "connections": [
                {"connection_id": "C1", "source_element": "S1", "target_element": "F1", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C2", "source_element": "F1", "target_element": "F2", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C3", "source_element": "F2", "target_element": "G1", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C4", "source_element": "G1", "target_element": "F3", "connection_type": "SEQUENCE", "description": "Ja"},
                {"connection_id": "C5", "source_element": "G1", "target_element": "F4", "connection_type": "SEQUENCE", "description": "Nein"},
                {"connection_id": "C6", "source_element": "F3", "target_element": "E1", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C7", "source_element": "F4", "target_element": "E1", "connection_type": "SEQUENCE", "description": ""}
            ]
        }
    },
    {
        "id": "geo_context_basic",
        "name": "Geo‑Kontext – Basis",
        "tags": ["geo", "geodaten", "bau", "standort"],
        "json": {
            "metadata": {"name": "Geo‑Kontext – Basis", "description": "Geo‑Bezug prüfen"},
            "elements": [
                {"element_id": "S1", "element_type": "START_EVENT", "name": "Start", "x": 50, "y": 350, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "GEO1", "element_type": "GEO_CONTEXT", "name": "Geo‑Kontext erfassen", "x": 200, "y": 350, "description": "Koordinaten/Flurstück", "responsible_authority": "Vermessung", "legal_basis": "", "deadline_days": 0, "geo_reference": "EPSG:25832"},
                {"element_id": "F1", "element_type": "FUNCTION", "name": "Lage prüfen", "x": 350, "y": 350, "description": "B‑Plan/Umwelt", "responsible_authority": "Bauamt", "legal_basis": "§ 29 BauGB", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "E1", "element_type": "END_EVENT", "name": "Ende", "x": 500, "y": 350, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""}
            ],
            "connections": [
                {"connection_id": "C1", "source_element": "S1", "target_element": "GEO1", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C2", "source_element": "GEO1", "target_element": "F1", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C3", "source_element": "F1", "target_element": "E1", "connection_type": "SEQUENCE", "description": ""}
            ]
        }
    },
    {
        "id": "kommunikation_message",
        "name": "Kommunikation – Nachricht",
        "tags": ["kommunikation", "message", "schnittstelle"],
        "json": {
            "metadata": {"name": "Kommunikation – Nachricht", "description": "Nachricht an Beteiligte"},
            "elements": [
                {"element_id": "S1", "element_type": "START_EVENT", "name": "Start", "x": 50, "y": 450, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "F1", "element_type": "FUNCTION", "name": "Information versenden", "x": 250, "y": 450, "description": "E‑Mail/Brief/API", "responsible_authority": "Poststelle", "legal_basis": "", "deadline_days": 0, "geo_reference": ""},
                {"element_id": "E1", "element_type": "END_EVENT", "name": "Ende", "x": 450, "y": 450, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""}
            ],
            "connections": [
                {"connection_id": "C1", "source_element": "S1", "target_element": "F1", "connection_type": "SEQUENCE", "description": ""},
                {"connection_id": "C2", "source_element": "F1", "target_element": "E1", "connection_type": "SEQUENCE", "description": ""}
            ]
        }
    }
]


def get_all_examples() -> List[Dict[str, Any]]:
    return DEFAULT_PROCESSES.copy()


def find_examples_by_tags(tags: List[str], max_examples: int = 3) -> List[Dict[str, Any]]:
    if not tags:
        return DEFAULT_PROCESSES[:max_examples]
    tags_lower = {t.lower() for t in tags}
    scored = []
    for ex in DEFAULT_PROCESSES:
        ex_tags = {t.lower() for t in ex.get("tags", [])}
        score = len(tags_lower & ex_tags)
        scored.append((score, ex))
    scored.sort(key=lambda x: (-x[0], ex_order(x[1]['id'])))
    return [ex for score, ex in scored[:max_examples]]


def ex_order(ex_id: str) -> int:
    order = {ex["id"]: i for i, ex in enumerate(DEFAULT_PROCESSES)}
    return order.get(ex_id, 9999)


def render_examples_snippet(examples: List[Dict[str, Any]]) -> str:
    """Rendert Beispiele als Prompt-Abschnitt. NICHT als Ausgabe reproduzieren!"""
    parts = [
        "Beispiele (nur lesen, nicht ausgeben):\n"
    ]
    for i, ex in enumerate(examples, 1):
        parts.append(f"// Beispiel {i}: {ex['name']}\n")
        parts.append(json_dump_minified(ex["json"]))
        parts.append("\n")
    return "".join(parts)


def json_dump_minified(obj: Any) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
