# vpb_designer_min.py – Minimaler VPB Process Designer

## Kurzüberblick
Ein eigenständiger, lauffähiger Tkinter-Editor für VPB-JSON-Prozesse (ohne Backend). Unterstützt Laden/Speichern, Pan/Zoom, Auswahl/Mehrfachauswahl, Drag&Drop, Verbindungserstellung, Eigenschaften-Panel, Undo/Redo sowie eine AI-Chat-Konsole unterhalb des Canvas (lokal über Ollama).

- GUI: Tkinter/ttk
- Dateiformat: vereinfachtes VPB-JSON mit `metadata`, `elements[]`, `connections[]`
- AI: Lokaler Ollama-Endpunkt (konfigurierbar) für Text→Diagramm, Vorschläge, Chat
- Persistenz: Einstellungen in `vpb_settings.json`, Chatverläufe unter `./chats/<user>@<host>/<model>/chat_YYYYMMDD[_N].json`

## Hauptklassen und Verantwortlichkeiten
- VPBCanvas (tk.Canvas)
  - Rendering von Elementen/Verbindungen inkl. Labels
  - Interaktionen: Auswahl, Mehrfachauswahl (Shift/Rect), Drag, Link-Modus, Kontextmenüs
  - View-Transform: Pan (MMB), Zoom (Ctrl+Mausrad), Reset, Fit-to-Diagram
  - Undo/Redo via Snapshot-Stacks (max 50)
  - Import/Export: `load_from_dict()`, `to_dict()`

- PropertiesPanel (tk.Frame)
  - Bearbeiten des aktuell gewählten Elements (Typ, Name, Beschreibung, Zuständigkeit, Rechtsgrundlage, Frist, Geo)
  - Callback `on_apply(values)` zur Anwendung auf Canvas-Model
  - Eigenes Formular für Hierarchie-Bänder (Name, Farbe, Y-Bereich) inklusive sofortigem Dropdown-Refresh bei Änderungen im Manager

- ChatPanel (tk.Frame)
  - Konsolenartiger Verlauf (read-only, dunkles Theme), Eingabefeld, Senden/Stop, Quick-Actions
  - Streaming-Append der Assistentenantwort

- VPBDesignerApp (tk.Tk)
  - Menü/Toolbar, Canvas, rechte Eigenschaften-Registerkarte, AI-Konsole unterhalb des Canvas, Statusbar
  - Dateioperationen: Neu/Öffnen/Speichern/Export (PostScript)
  - Einstellungen für Ollama (Endpoint/Model/Temperatur/Max Tokens)
  - AI-Flows: Text→Diagramm, „Nächster Schritt“-Vorschläge (mit Review/Apply-Dialog)
  - Chat: Streaming, Cancel, Autosave nach jeder Antwort, History-Rotation
  - Ansicht-Menü ergänzt um **Hierarchien verwalten…** (CRUD-Dialog mit Liste, Detailformular, Duplizieren/Löschen/Sortieren) sowie **Hierarchie JSON bearbeiten…** für Low-Level-Eingriffe
  - Arrangement-Leiste mit Ausrichten-/Verteilen-Befehlen sowie *Kreis anordnen* für ausgewählte Elemente

## Öffentliche API (Auszug)
- Laden/Speichern
  - `VPBCanvas.load_from_dict(data: dict)` – Diagramm laden
  - `VPBCanvas.to_dict() -> dict` – Diagramm exportieren

- Bearbeiten
  - `add_element(element_type, name, at)` → VPBElement
  - `add_connection(source_id, target_id, connection_type)` → VPBConnection
  - `delete_selected()`, `duplicate_selected()`
  - `undo()`, `redo()`

- Ansicht
  - `reset_view()`, `fit_to_diagram(padding=40)`

- Chat/AI (in App)
  - `_configure_ollama()`, `_ollama_health()`
  - `_text_to_diagram()` – generiert VPB-JSON und lädt es (Validierung über `vpb_schema.validate_vpb_dict`)
  - `_suggest_next_step()` – erzeugt Add-only-Diff (Validierung über `vpb_diff.validate_add_only_diff`)

## Datenformate
- Element:
  - `element_id: str`, `element_type: str`, `name: str`, `x: int`, `y: int`, optionale Felder wie `description`, `responsible_authority`, `legal_basis`, `deadline_days`, `geo_reference`
- Verbindung:
  - `connection_id: str`, `source_element: str`, `target_element: str`, `connection_type: str`, optional `description`

## Tastatur & Maus (Standard)
- Pan: Mittlere Maustaste ziehen
- Zoom: Strg + Mausrad (Cursor-Fokuspunkt)
- Reset/Fit: Strg+0 / Strg+9
- Auswahl: Klick, Mehrfachauswahl mit Shift-Klick oder Drag-Rechteck
- Link-Modus: Taste „L“, Abbruch: Esc
- Undo/Redo: Strg+Z / Strg+Y
- Datei: Strg+N/Strg+O/Strg+S
- Chatfokus: F2, Strg+Enter (kontextsensitiv)

## Abhängigkeiten
- Lokal: `ollama_client.py`, `ai_prompts.py`, `vpb_schema.py`, `vpb_diff.py`
- Standardbibliothek: tkinter, json, os, threading
- Keine externen Python-Pakete nötig

## Fehlermodi & Edge Cases
- Fehlende/inkonsistente IDs beim Laden werden ignoriert oder führen zu Validierungsfehlern (vor allem in AI-Flows)
- Chat: Bei Verbindungsfehlern zum Ollama-Endpunkt werden Fehler im Chat angezeigt; Autosave schützt vor Datenverlust
- Undo/Redo: Nur innerhalb der definierten Historie (50 Snapshots)

## Beispiele
- Start ohne Parameter: GUI öffnen, Elemente per Kontextmenü hinzufügen, Diagramm als `.vpb.json` speichern
- „AI → Text → Diagramm…“: Beschreibung eingeben, Modell generiert VPB-JSON; Validierung erfolgt vor dem Laden

## Hinweise
- Chatverläufe werden automatisch nach jeder Assistentenantwort geschrieben
- History-Dateiname rotiert pro Tag; mehrere Sessions am selben Tag werden hochgezählt (`_2`, `_3`, …)
- Das Modul ist lauffähig ohne die „VERITAS/UDS3“-geschützten Dateien in diesem Repository