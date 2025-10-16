# VPB – Aktuelle ToDos und Roadmap

Stand: 2025-09-29

Diese Datei bündelt Status, ToDos und Roadmap für den Editor (`vpb_app.py`).

## Kürzlich erledigt

- [x] SVG-Export dynamische Bounds & Routing (29.09.2025)
  - `render_process_svg` berechnet ViewBox/Offsets anhand realer Bounding-Boxes (inkl. Gruppen) und rendert Metadaten-Texte.
  - Verbindungen nutzen orthogonale Pfade mit Box-Kollisionen, Pfeilstile (einfach/doppelt) und getestete Regressionen (`tests/test_svg_exporter.py`).
- [x] Palette-Kategorien Reflow Fix (29.09.2025)
  - `_reflow` platziert Buttons auch bei kollabierten Containern vor; Auf-/Zuklappen zeigt sofort sichtbare Controls.
  - Manuelle Smoke-Checks der Palette-Filter & pytest-Run dokumentiert.
- [x] Review/Apply Diff UI für AI-Vorschläge
  - `_review_and_apply_diff(current, diff, element_types, connection_types)` inkl. Zählung, Pretty-JSON-Vorschau, Add-Only-Validierung (`vpb_diff.validate_add_only_diff`) und Anwendung mit Undo/Redraw.
- [x] Navigation ohne mittlere Maustaste (MMB)
  - Space+Linksklick-Ziehen = Hand-Tool/Pan, Alt+Linksklick-Ziehen = Pan, Shift/Alt+Mausrad = horizontales/vertikales Panning, konsistentes Cursor-Feedback; Selektion/Drag ist dabei sauber „geguardet“.
- [x] Tastaturkürzel nach Best Practice
  - Kontextsensitives Delete/Backspace, Pfeile = Nudge vs. Pan (mit Shift = größerer Schritt), Zoom/Center/Pan-Shortcuts, Gruppieren, Copy/Cut/Paste, Ctrl+Enter kontextuell.
- [x] Tools → „Prozess prüfen…“ Dialog
  - Toleranter Validator `_validate_vpb_data_safe` (optional Schema-Check via `vpb_schema.validate_vpb_dict`).
- [x] Start: Zeitachse vertikal zentrieren
- [x] Duplikat-Offset konfigurierbar; Ctrl+Alt-Duplizieren nur Container; Shift-Achsensperre beim Ziehen
- [x] Asynchrone Merge-/Patch-Pipeline über AppController
  - `MergeService` arbeitet auf Daten-Snapshots, liefert Diagramme + Zusammenfassungen zurück; UI verwaltet Pending-Tasks, Chat-Feedback und wendet Ergebnisse im Hauptthread an.
- [x] AI-Konsole unter Canvas
  - Chat-Bereich als eigenständige Konsole unter dem Diagramm eingebunden; vertikal zuschneidbar, dunkles Theme mit klaren Statusmeldungen.
  - Fokus (F2) und Send-Aktion sorgen dafür, dass die Konsole sichtbar bleibt; Dokumentation angepasst.
- [x] Referenz-Subprozesse als Gruppen dargestellt (2025-09-27)
  - `VPBCanvas` konvertiert SUBPROCESS-Referenzen automatisch in zugeklappte Gruppen mit gespeicherten Originaltypen.
  - Kontextmenü, Duplikat-Logik und Eigenschaften-Panel unterstützen die gruppierten Referenzen inklusive Inline-Vorschau.
- [x] XML-Viewer Tab im Mittel-Notebook (2025-09-28)
  - Neben dem Code-Tab zeigt der neue XML-Tab die ATOK-Übersetzung des aktuellen Prozessschemas (Button „Diagramm → XML“ + Auto-Refresh beim Tabwechsel).
- [x] XML-Export Mehrformat (2025-09-28)
  - XML-Renderer liefern jetzt eEPK- und BPMN 2.0-konforme Ausgaben (+ weiterhin ATOK) inklusive Layout-Koordinaten.
  - Der XML-Tab bietet eine Format-Auswahl (BPMN 2.0, eEPK, ATOK) und aktualisiert den Inhalt per Button oder direkte Auswahl.

## Aktuelle ToDo-Liste (priorisiert)

### Fokus KW39 (28.09 – 04.10)

- [ ] SVG-Export Output-Polish
  - Status: Dynamische Größe, Labeling & Connection-Routing implementiert; Regressionstests aktualisiert.
  - Nächste Schritte:
    - Export-Dialog/CLI auf dynamische Abmessungen trimmen (PNG/PDF Bounds angleichen).
    - Beispiel-SVGs aktualisieren (`docs/examples/`) und README-Hinweis ergänzen.
    - Optional: Visual Diff Tests (z. B. `pytest-regressions`) für SVG-Ausgabe einführen.
- [x] Undo/Redo für AI-Diffs verfeinern (28.09.2025)
  - Status: `MergeManager.apply_add_only_patch` bündelt Add-Only-Diffs zu exakt einer Undo-Unit; `_review_and_apply_diff` liefert klaren Status „AI-Diff angewendet (+E/+C)“ inkl. Chat-Zusammenfassung.
  - Nächste Schritte:
    - Manuelle Smoke-Checks mit großen Diffs (Undo → Redo) durchführen und Ergebnis im `docs/DOC_prompts_diagnose_fix.md` ergänzen.
    - Optional: UI-Integrationstest hinzufügen, der die Undo-Historie nach AI-Apply prüft.
- [ ] Multi-Format XML Export Integration
  - Status: Renderer liefern BPMN 2.0 (inkl. BPMN-DI), eEPK und ATOK; XML-Tab erlaubt Formatwahl, Regressionstests (`tests/test_xml_export.py`) abgedeckt.
  - Nächste Schritte:
    - Export-Dialog/Datei-Menü auf mehrformatigen Renderer umstellen (inkl. Dateiendungen & Default aus `EXPORT_CONFIG`).
    - Schema-/Validator-Hooks ergänzen (BPMN 2.0 XSD, eEPK-Regeln) und Fehlermeldungen im Statusbar/Log verankern.
    - Dokumentation und Wizard/CLI-Exports auf neue Formate ausweiten (inkl. Beispielartefakte).
- [ ] Minimap/Ruler Feinschliff
  - Status: Minimap wird als eigenes Notebook oben in der rechten Sidebar angezeigt (`create_right_sidebar`); darunter sitzt das Settings-Notebook mit dem Eigenschaften-Tab. Ruler weiterhin aktiv, schnelle Pan-Events erzeugen noch gelegentliche Redraw-Spikes.
  - Nächste Schritte:
    - Redraw-Throttling für Pan/Zoom im Canvas-Event-Loop ergänzen.
    - Fokus-/Tastatursteuerung des neuen Minimap-Tabs & Settings-Stacks prüfen und in der Shortcut-Hilfe dokumentieren.
    - Smoke-Test/Profiling-Notizen im `docs/DOC_performance_benchmark.md` auf den neuen Aufbau aktualisieren.
- [ ] Palette UX & Testabdeckung
  - Status: Sofortige Button-Anzeige nach Aufklappen wiederhergestellt; Tooltip-Logik bleibt unverändert.
  - Nächste Schritte:
    - Automatisierte UI-Smoke-Tests (tkinter-mock oder Screenshot-basiert) prototypen, um Regressions zu vermeiden.
    - Layout-Caching evaluieren (Performance bei großen Paletten) und ggf. `after_idle`-Batches einsetzen.
    - Dokumentation (`docs/DOC_prompts_diagnose_fix.md` / Palette-README) um Troubleshooting-Hinweise ergänzen.
- [ ] Referenz-Prozesspaletten
  - Status: `palettes/reference_palette.json` liefert farbcodierte Referenz-Snippets (inkl. Symbol/Textfarbe); Palette-Buttons übergeben nun `reference`-Payload, und das Canvas setzt Stil/Metadaten + Auto-Gruppierung & Preview beim Einfügen.
  - Nächste Schritte:
    - Dokumentation & Beispiele für weitere Fachdomänen ergänzen (Palette-README, Release Notes).
    - Zusätzliche Snippets kuratieren (z. B. Sozialleistungen, Sicherheit) und Test-Deckung für Edge-Cases erweitern.
    - Optional: Vorschau/Info-Panel für ausgewählte Referenzprozesse in der Palette anbieten.
- [ ] AI-Ingestion Wizard – Diff-UX Nachschärfen
  - Status: Review-Dialog steht (`_review_ingestion_diff`), Diff-Highlights gehen nach Schließen verloren und Logs sind im UI nicht verlinkt.
  - Nächste Schritte:
    - Persistente Highlights nach erfolgreichem Apply implementieren (`_highlight_merge_changes` erweitern).
    - Link zu `logs/ingestion_*.json` im Detail-Dialog (`_show_ingestion_details`) oder Chat-Feedback platzieren.
    - Optional Auto-Apply-Option mit Undo-Absicherung anbieten.

### Q4 2025 – Guardrails & Qualität

- [ ] Nächste Schritte Guardrails/Evaluation
  - Status: Guardrail-Heuristiken aktiv, Evaluation läuft manuell (`evaluation/guardrails/run_guardrail_evaluation.py`). Integration in Diagnose-/Patch-Flows fehlt.
  - Nächste Schritte:
    - Guardrail-Hooks für Diagnose-/Patch-Antworten im `TaskController` bzw. `chat_controller` aktivieren.
    - Nightly-Job oder CI-Workflow für die Evaluation aufsetzen und Ergebnisse in `docs/AI_Guardrails_Report.md` automatisiert aktualisieren.
    - Zusätzliche Realbeispiele kuratieren (mind. 5 Datenquellen) und als Fixtures ablegen.
- [ ] Chat-Anhang UX & Kontextgrenzen
  - Status: Chat-Konsole unterstützt Buttons/Progress, Dateiupload bietet noch keine Vorschau/Segmentierung.
  - Nächste Schritte:
    - Upload-Dialog in `vpb/ui/chat_console.py` erweitern (Preview, Abschnittsauswahl, Token-Schätzung).
    - Segmentierung/Chunking im `ollama_client.py` vorbereiten und Token-Limits pro Modell dokumentieren.
    - UX-Textbausteine im Chat anpassen (Kurz-Hinweis statt Volltext-Protokoll).
- [ ] UI-Modularisierung `vpb_app.py`
  - Status: Kernmodule ausgelagert, ChatPanel/Canvas-Tools und Tests fehlen weiterhin.
  - Nächste Schritte:
    - **Phase 0 (Scoping, 29.09.2025)**
      - [ ] Ist-Analyse abschließen: `vpb_app.py` zählt aktuell ~4 844 Zeilen, kommentierte Blöcke identifizieren.
      - [ ] Abhängigkeitsgraph (Imports, Zugriff auf `canvas_controller`, `props`, `task_controller`) skizzieren.
      - [ ] Öffentliche API (Methoden, die extern genutzt werden) in `docs/DOC_architecture_refactor.md` ergänzen.
    - **Phase 1 – Panel/Sidebar-Logik trennen**
  - [x] Palette/Hiearchie-Helfer (`_reload_palettes`, `_on_palette_pick`, `_apply_hierarchy_categories`, `_open_hierarchy_dialog`) in neues Modul `vpb/ui/app_palette_integration.py` überführen.
  - [x] Eigenschaften-/Properties-Brücke (`_apply_properties`, `_on_selection_changed`) in `vpb/ui/app_properties_bridge.py` kapseln.
  - [x] Unit-Smoke-Tests für neue Module (`tests/ui/test_app_palette_integration.py`, `tests/ui/test_app_properties_bridge.py`) anlegen.
    - **Phase 2 – App-Actions & Shortcuts**
  - [x] View-/Edit-Actions (`_toggle_grid`, `_toggle_snap`, `_undo`, `_redo`, `_fit_to_diagram`, `_reset_view`) in `vpb/ui/app_actions.py` auslagern; `VPBApp` bindet sie via Komposition.
      - [x] Shortcut-Bindings in separater Helferklasse (`vpb/ui/app_shortcuts.py`) bündeln; Dokumentation aktualisieren.
        - Helper integriert (`VPBApp._shortcuts.register`) und neue Tests (`tests/ui/test_app_shortcuts.py`) laufen grün.
      - [ ] Regressionstest: Laden der App im Headless-Modus (`tests/ui/test_app_import.py`).
    - **Phase 3 – Chat/AI-Integration**
      - [x] Chat-spezifische Methoden (`_focus_chat`, `_handle_ctrl_enter`, `_ensure_chat_visible`) in `vpb/ui/app_chat_integration.py` verschieben.
        - Helper eingeführt (`AppChatIntegration`) inkl. Tests (`tests/ui/test_app_chat_integration.py`).
      - [x] Controller-Polling `_handle_controller_result` in neues Modul (`vpb/ui/app_task_dispatch.py`) mit klarer Schnittstelle auslagern.
        - Neuer Helper `AppTaskDispatch` kapselt Polling/Dispatch, Telemetrie-Logging für unhandled Events und eigene Tests (`tests/ui/test_app_task_dispatch.py`).
      - [x] Telemetrie-Hooks in `telemetry_manager.py` prüfen und anpassen.
        - `TelemetryManager.subscribe`/`clear_listeners` ermöglichen Live-Listener; `AppTaskDispatch` protokolliert jetzt Poll-Zusammenfassungen.
    - **Phase 4 – Menü-/Export-Routinen**
      - [ ] Menüaufbau (`_create_menu_bar`) plus Dateiexport (`_export_process_*`) in `vpb/ui/app_menu.py` & `vpb/ui/app_export.py` kapseln.
      - [ ] Tests: `pytest tests/test_pdf_exporter.py` & neue Smoke-Cases für Menü-Helfer.
        - [ ] `VPBDesignerApp` instanziiert `AppMenuIntegration`/`AppExportIntegration` und delegiert bestehende `_export_*`-Methoden.
        - [ ] Menü-Kommandos rufen nur noch Helper-APIs auf (`app.menu.bind_exports(app.exports)`).
        - [ ] Gemeinsame Canvas-Snapshot-Hilfen (`_resolve_canvas_bounds`, `_capture_postscript`) in `app_export.py` implementieren + Unit-Tests hinzufügen.
        - [ ] Headless-Test-Doubles für File-Dialoge vorbereiten (Fixtures in `tests/ui`).
    - **Phase 5 – Aufräumen & Limits**
      - [ ] Restliche Utility-Methoden kategorisieren (Dialoge, Statusmeldungen) → ggf. `vpb/ui/app_dialogs.py`.
      - [ ] `vpb_app.py` auf < 2 000 Zeilen trimmen; Modul-Diagramm in `docs/DOC_architecture_refactor.md` ergänzen.
      - [ ] Abschließenden Refactor-Check (Import, Flake/ruff, pytest) automatisieren.
- [ ] Automatisierte Qualitätskontrollen
  - Status: Pytest-Basissetup vorhanden (`tests/test_vpb_validation.py`), CI/Linting fehlen.
  - Nächste Schritte:
    - `requirements.txt` um `ruff`, `mypy` erweitern und Konfigurationen (`pyproject.toml`/`ruff.toml`) hinzufügen.
    - GitHub Actions (oder Alternative) für Lint, Tests, Guardrail-Evaluation definieren.
    - README Quality-Gates und Troubleshooting ergänzen.
- [ ] LLM-Härtung & Validierung vereinheitlichen
  - Status: `validate_model_output` verfügbar (`vpb_ai_logic.py`), UI-Flows nutzen teils noch direkte JSON-Generierung.
  - Nächste Schritte:
    - Aufrufe in `vpb_app.py` auf den Validierungs-Wrapper umstellen und konsistente Fehlermeldungen im Chat (`chat_controller`) einführen.
    - Hook-Logging aktivieren, um Validierungswarnungen/Repairs zu protokollieren.
    - Regressionstests für Diagnose-/Next-Steps-Flows erstellen.
- [ ] Schema-Härtung End-to-End
  - Status: Strenges Schema aktiv, Toleranzmodus/Repair-Hooks fehlen.
  - Nächste Schritte:
    - Dirty-JSON-Fallback & Sanitizer im `ollama_client.py` evaluieren.
    - Validierungs-Toleranzen (Warnings statt Abbruch) im Service-Layer ergänzen.
    - Prompts in `ai_prompts.py` überarbeiten (Pflichtfelder/Defaults betonen) und Beispiele prüfen.

### Forschung & Experimente

- [ ] Routing Smart+ Iterationen
  - Status: Smart+-Routing stabil, diagonale Wege & Heatmap-Penalties noch offen.
  - Nächste Schritte:
    - Raster-Logik um adaptive Schrittgrößen erweitern (`vpb/ui/canvas_interactions.py`).
    - Heatmap-Backtracking prototypisch implementieren und Performance <150 ms messen.
    - Ergebnisse im `docs/DOC_performance_benchmark.md` festhalten.

## Archiv – Abgeschlossene Prioritäten (bis 27.09.2025)

- [x] Merge/Patch Ergebnis-Diff visualisieren (25.09.2025)
  - Canvas zeigt neue/aktualisierte Elemente/Verbindungen, Warnungen erscheinen dialogisch, Chat fasst Merge/Patch-Ergebnisse strukturiert zusammen.
- [x] Controller-Cancel & Fortschrittsmeldungen (25.09.2025)
  - Einheitliche Cancel-API für Merge/Ollama/Validation-Tasks, UI zeigt Fortschritts- und Abbruchstatus.
- [x] Pan/Nudge Schrittgrößen konfigurierbar (25.09.2025)
- [x] Mausrad-Verhalten umschaltbar (25.09.2025a)
- [x] Shortcut-Help & Onboarding-Hinweis (25.09.2025)
- [x] AI-Ingestion Wizard Grundfunktion (25.09.2025)
- [x] AI-Guardrails & Evaluation (25.09.2025)
- [x] Tests für Validator & Diff (27.09.2025)
- [x] Autosave & Recovery (25.09.2025)
- [x] Arrange/Distribute Werkzeuge (25.09.2025)
- [x] Fokus- & Zoom-Shortcuts (25.09.2025)
- [x] Referenz-Gruppen UI-Feinschliff (27.09.2025)


## Roadmap Q4/2025

- Oktober 2025
  - Fokus: Undo/Redo für AI-Diffs, Minimap/Ruler-Polish, AI-Ingestion Diff-UX.
- November 2025
  - Fokus: Guardrails/Evaluation, Chat-Anhang UX, UI-Modularisierung, Automatisierte QA.
- Dezember 2025
  - Fokus: LLM-/Schema-Härtung und Routing Smart+ Iterationen.

## Hinweise zur Bedienung (Kurz)

- Pan ohne MMB:
  - Space gedrückt halten + Linksklick-Ziehen → Pan (Hand-Tool)
  - Alt + Linksklick-Ziehen → Pan
  - Mausrad mit Shift/Alt → horizontales/vertikales Panning
- Zoom: Strg + Mausrad (je nach Einstellung umschaltbar)
- Achsensperre: Shift beim Ziehen → Bewegung entlang dominanter Achse
- Duplizieren: Strg + Ziehen; mit Alt (Typ GROUP) → nur Container kopieren
- Duplikat-Offset: `canvas.duplicate_offset` (Standard 30)

## Nachverfolgung

- App startet fehlerfrei; neue Navigation ist mit Selektion/Drag sauber integriert.
- Bitte bei Auffälligkeiten konkrete Stelle/Schritte melden (Repro), dann ergänzen wir zielgerichtete Fixes.
