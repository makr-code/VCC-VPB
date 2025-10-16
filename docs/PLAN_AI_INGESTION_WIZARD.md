# AI-Ingestion Wizard – Implementierungsplan

## Zielsetzung
Der Wizard soll strukturierte VPB-Prozessfragmente aus frei formulierten Quellen (TXT/Markdown) sowie tabellarischen Daten (CSV) extrahieren und als Add-Only-Diffs ins bestehende Diagramm übertragen. Fokus: reproduzierbare, nachvollziehbare Importe bei minimalem Risiko für bestehende Prozesse.

### Akzeptanzkriterien (gemäß ToDo 6)
- Mindestens drei Beispielquellen (TXT, MD, CSV) lassen sich ohne Fehler einlesen.
- Der Wizard erzeugt valide VPB-JSON-Strukturen, die Schema-Check und `vpb_diff.validate_add_only_diff` bestehen.
- Anwender:innen können die vorgeschlagenen Änderungen in einer Review-Ansicht prüfen und als ein Undo-Element anwenden.

## Nutzerfluss (High Level)
1. **Trigger**: Menüeintrag „Datei → AI-Ingestion Wizard…“ oder Button in der AI-Konsole.
2. **Schritt 1 – Quelle wählen**:
   - Datei(en) auswählen (TXT, MD, CSV) oder freien Text einfügen.
   - Optional: Prompt-Kontext (z. B. gewünschter Prozessbereich, Zielgruppe).
3. **Schritt 2 – Parsing & Analyse**:
   - Pre-Checks: Dateigröße, Zeichensatz, CSV-Header-Erkennung.
   - Inhalte werden in `ingestion_request` gepackt und an Ollama-Service übergeben.
4. **Schritt 3 – AI-Vorschlag**:
   - Streaming-Status im Wizard-Dialog (Fortschritt, Tokenzählung).
   - Ergebnis: strukturierte JSON-Vorschläge (Elemente, Verbindungen, Metadaten).
5. **Schritt 4 – Review & Diff**:
   - Anzeige als Tabelle/Liste (Elemente mit Typ/Name/Beschreibung, Verbindungen).
   - Diff auf Basis von `vpb_diff` (Add-Only). Warnungen bei inkonsistenten IDs.
   - Optional: Quick-Fixes (Umbenennen, Entfernen einzelner Vorschläge).
6. **Schritt 5 – Apply**:
   - Anwenden erzeugt einen Undo-Punkt.
   - Erfolgs-/Fehlermeldung in Statusleiste + AI-Konsole.

## Komponenten & Verantwortlichkeiten
- **UI (Tk)**
  - `IngestionWizardDialog` (neuer Dialog mit `ttk.Notebook` für Schritte).
  - File Picker & Text-Eingabe, Fortschrittsbalken, Review-Listbox mit Checkboxen.
- **Service Layer**
  - `ingestion_service.py` (neu):
    - Pre-Processing für CSV (pandas optional?) oder reiner Python CSV.
    - Vorbereitung der Prompt-Struktur (Kontext, Format-Instruktionen).
    - Übergabe an bestehenden `AppController` (`ollama_chat_stream` oder neues Kommando).
  - Re-Use `vpb_diff` / `vpb_schema` für Validierung.
- **Datenstrukturen**
  - `IngestionRequest`: Quelle, Format, Optionen.
  - `IngestionResult`: `proposed_elements`, `proposed_connections`, `warnings`.
- **Persistenz**
  - Wizard merkt sich letzte Pfade (Settings Manager → neuer Abschnitt `ingestion`).
  - Optional: Log-Datei `logs/ingestion_<timestamp>.json` für Troubleshooting.

## Validierung & Safety
- **Pre-Checks**
  - Dateigröße (< 256 KB), UTF-8 Validität, CSV-Header.
  - Hinweismeldung bei verdächtig wenigen Spalten/Zeilen.
- **Schema & Diff**
  - `vpb_schema.validate_vpb_dict` auf AI-Output.
  - `vpb_diff.validate_add_only_diff` mit existierendem Diagramm.
- **Post-Checks**
  - Keine IDs werden überschrieben (Add-Only).
  - Undo-Stack enthält genau einen Eintrag pro Apply.

## UI-Spezifika
- Wizard als modaler Dialog mit `wait_window`.
- Schrittweises Fortschalten (`Weiter`, `Zurück`, `Abbrechen`).
- Review-Step mit Zwei-Spalten-Layout (Liste + Detailkarte).
- Integrationspunkt für AI-Konsole: Fortschritt & Log-Meldungen spiegeln.

## Offene Punkte / Risiken
- CSV-Parsing ohne pandas? → vorerst `csv`-Modul mit einfachen Heuristiken.
- Prompt-Optimierung für verschiedene Formate; Tests mit Beispieldateien erforderlich.
- Performance bei großen Dateien (ggf. Align auf 1000 Zeilen Limit).

## Next Steps
1. Wizard-Dialog scaffolden (`IngestionWizardDialog`).
2. Ingestion-Service & Controller-Routing definieren.
3. Beispiel-Prompts und Testdateien in `docs/examples/ingestion/` ablegen.
4. Integrations-Review & QA (Schema + Diff Tests).
