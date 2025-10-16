# VPB Visual Process Designer (Minimal)

Diese minimalistische Tkinter-App zeigt und bearbeitet VPB-Prozesse aus JSON – ohne Server/API.

Funktionen:
- VPB-JSON laden und speichern (*.vpb.json, *.json)
- Elemente anzeigen und per Drag & Drop verschieben
- Element auswählen, löschen (Entf) und duplizieren (Ctrl+D)
- Element-Namen per Doppelklick umbenennen
- Neue Elemente und Verbindungen hinzufügen (Dialog)
- Link-Modus (Taste L) für schnelles Verbinden: Quelle klicken, dann Ziel
- Snap-to-Grid (Menü Bearbeiten) inkl. Rasteranzeige
- Export als PDF, PNG oder PostScript inklusive Prozessübersicht
- Eigenschaften-Editor rechts (Typ, Name, Beschreibung, Zuständige Stelle, Rechtsgrundlage, Frist, Geo-Referenz)

Voraussetzungen:
- Python 3.8+ für Windows
- Tkinter ist Teil der Standard-Python-Installation unter Windows
- Optional/empfohlen: `pip install -r requirements.txt` (stellt u. a. `dirtyjson` für robustere AI-JSON-Parsing bereit)
- Für PDF/PNG-Export: Ghostscript-Binary im `PATH` (z. B. `gswin64c.exe` unter Windows) oder Umgebungsvariable `GHOSTSCRIPT_BINARY`

Starten (PowerShell):

```powershell
# In das Projektverzeichnis wechseln
cd y:\VPB

# Minimalen Designer starten (optional mit Datei als Argument)
python .\vpb_designer_min.py
# oder
python .\vpb_designer_min.py .\processes\beispielprozess_baugenehmigung_20250822_113305.vpb.json
```

Bedienung:
- Datei → Öffnen…: VPB-JSON laden
- Datei → Speichern / Speichern unter…
- Datei → Export als PDF…: erzeugt eine zweiseitige PDF (Diagramm + Detailübersicht)
- Datei → Export als PNG…: speichert eine Canvas-Rastergrafik (Ghostscript benötigt)
- Datei → Export als SVG…: generiert eine skalierbare Vektorzeichnung
- Bearbeiten → Element hinzufügen: Typ und Name wählen
- Bearbeiten → Verbindung hinzufügen: Quelle, Ziel und Typ wählen
- Bearbeiten → Snap-to-Grid: Raster aktivieren/deaktivieren
- Bearbeiten → Link-Modus (L): Quelle klicken, dann Ziel
- Doppelklick auf Element: Name ändern
- Ziehen mit linker Maustaste: Element verschieben
- Eigenschaften rechts bearbeiten und „Übernehmen“ klicken

Shortcuts:
- Ctrl+S: Speichern
- Ctrl+O: Öffnen
- Ctrl+N: Neu
- Ctrl+D: Duplizieren
- Entf: Löschen
- L: Link-Modus toggeln

Hinweise:
- Dieses Tool ist unabhängig von UDS3-/Backend-Modulen und konzentriert sich auf die Visualisierung.
- JSON-Felder wie `description`, `legal_basis` etc. werden erhalten, aber aktuell nicht separat bearbeitet.
- Die Darstellung nutzt einfache Standardformen/Farben je `element_type`.

Lizenz/Proprietäres Material:
- Einige Dateien im Projekt enthalten Schutz-Hinweise. Diese Minimal-App nutzt keine geschützten Backend-Module.

## Tests

Es existiert eine kleine Test-Suite (unittest) für:
- Prompt-Erzeugung & Validierung (`vpb_prompt_core.py`, `vpb_ai_logic.py`)
- Schema-Migrationen (`vpb_db_migrations.py`)

Ausführen (PowerShell):

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Validierungs-Pipeline (Empfehlung bei AI-Nutzung):
1. Prompt bauen: `build_prompt_with_examples_text_to_vpb(..., return_meta=True)`
2. Modell aufrufen
3. Ergebnis prüfen: `validate_model_output(raw, mode=meta.mode, allow_element_types=[...], allow_connection_types=[...])`
4. Bei `fatal=True` optional Retry (weniger Beispiele, strengerer Hinweis)

Die Tests lassen sich erweitern um zusätzliche Edge Cases (Raster, IDs, Add-Only Konflikte). PRs willkommen.