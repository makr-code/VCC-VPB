#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt-Vorlagen für AI-gestützte VPB-Generierung.
"""
from __future__ import annotations
from typing import Iterable

DEFAULT_FIELD_GUIDE = (
    "- Fülle alle Pflichtfelder vollständig aus. Wenn Informationen fehlen, nutze folgende Defaultwerte statt Felder zu entfernen oder null zu verwenden:\n"
    "  * Zeichenkettenfelder: \"\" (leerer String)\n"
    "  * responsible_authority: \"unbekannt\" falls keine Behörde genannt ist\n"
    "  * legal_basis: \"n.n.\" falls keine Angabe möglich ist\n"
    "  * deadline_days: 0\n"
    "  * geo_reference: \"\"\n"
)


def build_text_to_vpb_prompt(description: str, element_types: Iterable[str], connection_types: Iterable[str]) -> str:
    et = ", ".join(sorted(element_types))
    ct = ", ".join(sorted(connection_types))
    return (
        "Du bist ein Assistent, der aus einer kurzen deutschsprachigen Prozessbeschreibung eine strukturierte Darstellung "
        "in einem vereinbarten JSON-Format erzeugt. Verwende ausschließlich die erlaubten Typen.\n\n"
        "Anforderungen:\n"
        "- Gib NUR ein einziges gültiges JSON-Objekt zurück (keine Erklärungen, keine Kommentare, keine Codeblöcke).\n"
        "- Struktur:\n"
        "  {\n"
        "    \"metadata\": { \"name\": string, \"description\": string },\n"
        "    \"elements\": [\n"
        "      {\n"
        "        \"element_id\": string,\n"
        "        \"element_type\": string,\n"
        "        \"name\": string,\n"
        "        \"x\": integer,\n"
        "        \"y\": integer,\n"
        "        \"description\": string,\n"
        "        \"responsible_authority\": string,\n"
        "        \"legal_basis\": string,\n"
        "        \"deadline_days\": integer,\n"
        "        \"geo_reference\": string\n"
        "      }, ...\n"
        "    ],\n"
        "    \"connections\": [\n"
        "      {\n"
        "        \"connection_id\": string,\n"
        "        \"source_element\": string,\n"
        "        \"target_element\": string,\n"
        "        \"connection_type\": string,\n"
        "        \"description\": string\n"
        "      }, ...\n"
        "    ]\n"
        "  }\n\n"
        f"Erlaubte element_type-Werte: {et}.\n"
        f"Erlaubte connection_type-Werte: {ct}.\n"
        "Hinweise:\n"
        "- Vergib eindeutige IDs (z. B. E001, F001, G001 ...).\n"
        "- Platziere x,y in einem sinnvollen Raster (z. B. Vielfache von 50) für eine grobe Reihenfolge (links→rechts, oben→unten).\n"
    "- Nutze passende Verbindungstypen, typischer Standard ist SEQUENCE.\n"
    f"{DEFAULT_FIELD_GUIDE}"
    "- Liefere vollständig befüllte Objekte, keine fehlenden Felder oder null-Werte.\n\n"
        f"Prozessbeschreibung:\n{description.strip()}\n"
    )


def build_next_steps_prompt(current_diagram_json: str, selected_element_id: str | None,
                            element_types: Iterable[str], connection_types: Iterable[str]) -> str:
    et = ", ".join(sorted(element_types))
    ct = ", ".join(sorted(connection_types))
    sel = selected_element_id or ""
    return (
        "Du bist ein Assistent, der für ein bestehendes Prozessdiagramm (VPB-JSON) konkrete nächste Schritte vorschlägt.\n"
        "Gib NUR ein einziges JSON-Objekt mit genau diesen Feldern zurück: { \"elements\": [...], \"connections\": [...] }.\n"
        "Wenn keine Elemente nötig sind, gib leere Arrays zurück. Keine Erklärungen, keine Codeblöcke.\n\n"
        f"Erlaubte element_type-Werte: {et}.\n"
        f"Erlaubte connection_type-Werte: {ct}.\n"
        "Hinweise:\n"
        "- Vergib eindeutige IDs für neue Elemente/Kanten (z. B. E001/F001/G001 oder fortlaufend).\n"
        "- Nutze sinnvolle x,y-Positionen (Raster, links→rechts, oben→unten).\n"
    "- Nutze passende Verbindungstypen, Standard ist SEQUENCE.\n"
    "- Fülle alle Felder in neuen Elementen/Verbindungen vollständig aus.\n"
    f"{DEFAULT_FIELD_GUIDE}"
        "- Falls selected_element_id gesetzt ist, fokussiere Vorschläge darauf.\n\n"
        f"selected_element_id: {sel}\n"
        "current_diagram: \n"
        f"{current_diagram_json}\n"
    )


def build_diagnose_fix_prompt(current_diagram_json: str,
                              element_types: Iterable[str],
                              connection_types: Iterable[str]) -> str:
    et = ", ".join(sorted(element_types))
    ct = ", ".join(sorted(connection_types))
    return (
        "Du bist ein Assistent, der ein bestehendes VPB-JSON Diagramm analysiert, typische Fehler/Unsauberkeiten"
        " erkennt und ausschließlich einen JSON-Report mit optionalem Add-Only-Patch zurückgibt.\n"
        "Gib NUR ein einziges JSON-Objekt mit GENAU diesen Feldern zurück: {\n"
        "  \"issues\": [ {\n"
        "    \"id\": string,            // kurze Kennung (z.B. ISS001)\n"
        "    \"severity\": string,      // one of: info|warning|error\n"
        "    \"message\": string,       // Beschreibung des Problems\n"
        "    \"location\": {            // Bezug im Diagramm\n"
        "      \"element_id\": string|null,\n"
        "      \"connection_id\": string|null\n"
        "    },\n"
        "    \"suggestion\": string     // menschlich lesbare Empfehlung\n"
        "  } ... ],\n"
        "  \"patch\": {                  // optionaler Add-Only-Vorschlag\n"
        "    \"elements\": [ /* neue Elemente, gleiche Struktur wie in Text→Diagramm */ ],\n"
        "    \"connections\": [ /* neue Verbindungen */ ]\n"
        "  }\n"
        "}\n\n"
        f"Erlaubte element_type-Werte: {et}.\n"
        f"Erlaubte connection_type-Werte: {ct}.\n"
        "Regeln:\n"
        "- Ändere NICHT bestehende Objekte, liefere nur Add-Only Ergänzungen in patch.{elements,connections}.\n"
        "- IDs eindeutig vergeben (E/F/G/S... Zähler fortführen).\n"
        "- Positionen in 50er Raster setzen (links→rechts).\n"
    "- Wenn du neue Elemente/Verbindungen in patch vorschlägst, liefere sie vollständig mit allen Feldern.\n"
    f"{DEFAULT_FIELD_GUIDE}"
        "- Falls keine Probleme: issues = [] und patch = {\"elements\":[],\"connections\":[]}.\n\n"
        "current_diagram:\n"
        f"{current_diagram_json}\n"
    )


def build_ingestion_prompt(
    sources_text: str,
    element_types: Iterable[str],
    connection_types: Iterable[str],
    *,
    prompt_context: str = "",
    current_diagram_summary: str = "",
) -> str:
    """Erzeugt einen Prompt für AI-Ingestion.

    `sources_text` sollte eine bereits formatierte Übersicht der Eingangsdaten enthalten.
    """

    et = ", ".join(sorted(element_types))
    ct = ", ".join(sorted(connection_types))
    context_block = prompt_context.strip()
    diagram_block = current_diagram_summary.strip()

    parts = [
        "Du bist ein Assistent, der strukturierte Prozessfragmente (VPB JSON) aus bereitgestellten Quellen extrahiert.",
        "Liefere ausschließlich Add-Only-Ergänzungen zum bestehenden Diagramm.",
        "Ergebnisformat: EIN JSON-Objekt mit genau den Feldern {\"elements\": [...], \"connections\": [...]}.",
        "Keine zusätzlichen Kommentare, keine Codeblöcke, keine Erklärtexte.",
        "",
        "Erlaubte Element-Typen: " + et,
        "Erlaubte Verbindungstypen: " + ct,
        "",
        "Quellen (strukturiert, ggf. gekürzt):",
        sources_text.strip() or "(keine Quellen übergeben)",
    ]

    if context_block:
        parts.extend([
            "",
            "Zusätzlicher Prompt-Kontext:",
            context_block,
        ])

    if diagram_block:
        parts.extend([
            "",
            "Aktuelles Diagramm (Kurzfassung):",
            diagram_block,
        ])

    parts.extend([
        "",
        "Anforderungen:",
        "- Erzeuge nur neue Elemente/Verbindungen (Add-Only).",
        "- Verwende eindeutige IDs (Elemente: E/F/G…, Verbindungen: C/CON…).",
        "- Positioniere x/y auf dem 50er Raster (z. B. 100, 150, …).",
        "- Nutze sinnvolle Verbindungstypen (Standard: SEQUENCE).",
        "- Liefere vollständige Objekte mit allen Feldern.\n" + DEFAULT_FIELD_GUIDE.strip(),
        "- Wenn keine sinnvollen Ergänzungen möglich sind, gib leere Arrays zurück.",
    ])

    return "\n".join(parts)
