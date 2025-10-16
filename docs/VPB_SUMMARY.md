# VPB Visual Process Builder – Zusammenfassung

Dieser Workspace enthält:
- Einen funktionsfähigen, eigenständigen Tkinter-Designer (Minimal‑App) zum Modellieren von VPB‑Prozessen mit Pan/Zoom, Grid, Selektion, Verbindungen, Eigenschaften-Panel, Import/Export (JSON/XML, PostScript) sowie Undo/Redo und Komfortfunktionen.
- Optionale UDS3/VERITAS‑Module (API‑Server, SQLite, Compliance, Data‑Prep) – für die Minimal‑App nicht erforderlich.
- AI‑Integration via lokalem LLM (Ollama): Text→Diagramm, „Nächster Schritt“-Vorschläge, Chat‑Seitenleiste inkl. Streaming, Abbruch und konfigurierbaren Parametern.
- Persistenz für Chat‑Verläufe pro Nutzer@Host/Modell/Tag mit automatischem Speichern nach jeder Assistant‑Antwort.

## Architektur (hochlevel)
- GUI: Python 3 + Tkinter (Single‑Window, Canvas zentriert, linke Toolbox, rechte Eigenschaften, optional Chat‑Panel)
- Datenformat: VPB‑JSON/VPB‑XML, Schema‑Validierung (vpb_schema), diffs für AI‑Vorschläge (vpb_diff)
- AI: `ollama_client.py` (HTTP‑Client, Streaming, Retries, JSON‑Extraktion) + `ai_prompts.py` (strikte Prompts)
- Konfig/Logging/Pfade: `vpb_config.py`
- Optionale Backend‑Bausteine: `vpb_sqlite_db.py`, `vpb_api_server.py`, `vpb_compliance_engine.py`, `vpb_data_preparation.py`

## Wichtige Features
- Canvas: Pan/Zoom, Grid mit Snap, Mehrfachauswahl, Rechteck‑Selektion, Fit‑to‑Diagram/Zoom‑Reset
- Verbindungen: intelligente/gerade/kurvige Routen, Label/Conditions, Kontextmenüs
- Eigenschaften: Editor‑Dialoge, Verwaltungsattribute (Rechtsgrundlage, Zuständigkeit, Fristen), Geo‑Kontext
- Hierarchie-Management: seitliche Hierarchie-Leiste, CRUD-Dialog (Hierarchien verwalten…) und unmittelbare Dropdown-Aktualisierung im Eigenschaften-Panel
- Anordnen: Toolbar/Panel mit Ausrichten-, Verteilen- und Kreis-Anordnen-Befehlen inklusive automatischer Neu-Routung betroffener Verbindungen
- Dateioperationen: Laden/Speichern VPB‑JSON/VPB‑XML, Export PostScript
- Undo/Redo: Snapshot‑Stacks
- Shortcuts + View‑Menü
- AI: Text→Diagramm, Add‑only‑Diff anwenden mit Review‑Dialog
- Chat: Streaming, Cancel, Konfiguration (Endpoint/Modell/Temperatur/Tokens), Autosave, History‑Rotation
- Merge/Patch: Asynchrone Controller-Tasks, datenbasierte MergeService-Pipeline, Chat-Zusammenfassungen

## Dateien & Doku
Siehe docs/DOC_*.md für modulgenaue Beschreibungen.

## Ausführung (Minimal‑Designer)
- Start der Tkinter‑App (ohne Backend). Hinweis: Datei‑ und Klassenname gemäß Workspace.
- Optional: Ollama lokal starten und in den Einstellungen Endpoint/Modell setzen.

## Status
- Minimal-Designer lauffähig, Chat-Persistenz implementiert, AI-Flows funktionsfähig
- Asynchrone Merge-/Patch-Pipeline liefert aktualisierte Diagramme + Warnungen zurück
- Umfangreiche Zusatzmodule vorhanden, aber separat einsetzbar
