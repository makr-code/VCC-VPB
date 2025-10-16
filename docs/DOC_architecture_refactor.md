# VPB Architektur-Refactor (OOP + Threading + Queue)

## Ziele
- Trennung von UI (Tk) und Geschäftslogik
- Hintergrundausführung (nicht-blockierend) für Chat, Validierung, Merge
- Erweiterbare Services (Validation, Merge, Ollama)
- Einheitliches Task/Message-Modell für künftige Funktionen (z.B. Undo/Redo Persistenz, Analysejobs)
- Telemetrie-Hooks auf Task-Ebene

## Schichten
1. UI Layer (`vpb_app.py`)
   - Präsentationslogik, Benutzerinteraktionen, Rendering
   - Keine direkte langlaufende Logik mehr (Chat/Merge/Validation → Tasks)
   - Polling der Ergebnis-Queue → `_handle_controller_result`
2. Controller Layer (`controller/app_controller.py`)
   - Worker-Thread verarbeitet `TaskRequest`
   - Handler-Registry (`task_type` → Funktion)
   - Streaming-Unterstützung (Iterator liefert Chunks → Tupel `(task_id,'chunk',data)`)
3. Service Layer (`services/*.py`)
   - `ValidationService`: Schema + Prompt-Validierung (optionale Module tolerant)
   - `OllamaService`: Chat-Streaming / vollständige Antwort
   - `MergeService`: Erstellt Daten-Snapshots über `_DataCanvas`, führt `MergeManager` im Worker-Thread aus und liefert aktualisierte Diagramme + Zusammenfassungen zurück
4. Core Layer (`core/message_bus.py`)
   - `TaskRequest`, `TaskResult`, ID-Generator

## Task Lifecycle
```mermaid
graph TD;
UI[UI Aktion]-->SUBMIT[submit(task_type,payload)];
SUBMIT-->INQUEUE[Input Queue];
INQUEUE-->WORKER[Worker Thread];
WORKER-->HANDLER[Handler];
HANDLER--Optional Chunks-->OUTQUEUE[Output Queue];
HANDLER-->RESULT[TaskResult];
RESULT-->OUTQUEUE;
OUTQUEUE-->UI_POLL[UI Polling after() 80ms];
UI_POLL-->UI_UPDATE[UI aktualisiert Status / Chat / Meldungen];
```

## Aktuell registrierte `task_type`
| task_type | Handler | Beschreibung |
|-----------|---------|--------------|
| `validate_process` | ValidationService.validate | Schema + (optional) Prompt-Validierung |
| `ollama_chat_stream` | OllamaService.chat_stream | Streaming LLM Chat |
| `merge_full` | MergeService.merge_full | Vollmerging eines Fremdprozesses |
| `patch_add_only` | MergeService.patch_add_only | Add-Only Patch anwenden |

## Streaming- & Result-Modell
- Streams: `(task_id,'stream_start',None)` → mehrere `(task_id,'chunk',text)` → Abschluss via `TaskResult`
- Nicht-streamende Tasks liefern komplette Payloads in `TaskResult.data`
- Merge-/Patch-Aufgaben geben `diagram`, `summary_lines`, `added_count`, `updated_count`, `warnings` zurück; UI wendet Diagramm im Hauptthread an und zeigt Feedback im Chat

## Telemetrie
- `task_event`: Dauer & Erfolg je Task
- `task_stream_summary`: Anzahl Chunks bei Streaming-Tasks
- Bestehende Merge Telemetrie bleibt unverändert (`merge_full`, `patch_add_only`)

## Erweiterbarkeit
Neue Funktion (z.B. "Analyse Diagramm"):
1. Service-Klasse oder Funktionshandler implementieren
2. In `vpb_app.__init__` nach Controller-Erzeugung: `self._app_controller.register('analyze_process', lambda p: analyze_fn(p))`
3. UI: `self._app_controller.submit('analyze_process', {...})`
4. Ergebnis in `_handle_controller_result` interpretieren

## Fehlerbehandlung
- Handler-Exceptions werden in `TaskResult.error` serialisiert (inkl. kurzer Traceback)
- UI zeigt derzeit verkürzt nur Status; zukünftige UX: Dialog / Log-Panel

## Thread-Sicherheit
- Nur Worker-Thread berührt Services
- UI greift ausschließlich auf Tk-Objekte im Hauptthread zu
- MergeService arbeitet auf isolierten Daten-Snapshots (keine direkten Canvas-Zugriffe) und liefert fertige Diagramme zurück; das UI übernimmt das Anwenden im Hauptthread

## TODO / Roadmap
- Controller: Gemeinsame Cancel-API & Fortschrittsmeldungen für lange Tasks (Merge, Ollama)
- UI: Merge/Patch Ergebnis-Diff visualisieren (Highlight neu/aktualisiert, Warn-Dialog)
- Undo/Redo als Task (für persistente Operationen)
- Validation detaillierter (Issues-Liste an UI zurückgeben statt nur Count / Message)
- Persistenz von `conflict_strategy` & UI-Schalter
- UI-Modularisierung (29.09.2025):
   - `vpb_app.py` umfasst derzeit ~4 844 Zeilen → Ziel: <2 000 Zeilen.
   - Geplante Module (siehe `docs/VPB_TODO.md` Phase-Aufteilung):
      - `vpb/ui/app_palette_integration.py`
      - `vpb/ui/app_properties_bridge.py`
      - `vpb/ui/app_actions.py`
      - `vpb/ui/app_shortcuts.py`
      - `vpb/ui/app_chat_integration.py`
      - `vpb/ui/app_task_dispatch.py`
      - `vpb/ui/app_menu.py`
      - `vpb/ui/app_export.py`
   - Abhängigkeiten dokumentieren (Canvas, Props, Controller), anschließend migrationsweise auslagern.

## Phase 4 Helper Design (Stand 2025-09-29)

### `AppMenuIntegration`

- **Ziel**: Menü-Definitionen zentral kapseln (Datei/Bearbeiten/Ansicht/AI/Tools etc.), so dass `VPBDesignerApp` nur noch Komposition und minimale Zustandsanbindung hält.
- **Contract**:
   - Eingabe: Referenz auf `VPBDesignerApp` (liefert Canvas, Actions, Shortcuts, Export-Helfer)
   - Ausgabe: `tk.Menu` Hauptmenü + optionale Toolbar-Factories (`create_menu()`, `create_toolbar()`)
   - Fehler: Menü-Bau darf UI nicht blockieren → Exceptions werden gefangen und via Status/Log gemeldet.
- **Edge-Cases**:
   - Lazy-Init von `BooleanVar`/`StringVar` (Grid, Snap, Merge-Optionen) muss funktionieren, auch wenn Preferences später geladen werden.
   - Menü-Rebuild nach Settings-Reload (Platz halten für `refresh()` API).
   - Headless/Tests: Menü darf ohne Tk-Root-Loop instanziiert werden (Mocks für `tk.Menu`).

### `AppExportIntegration`

- **Verantwortung**: Alle Export- und Metadaten-Dialoge bündeln (Metadaten bearbeiten, PNG/PDF/SVG/PS). Gemeinsame Canvas-Snapshot-Logik und Statusmeldungen zentralisieren.
- **Contract**:
   - `AppExportIntegration(app: VPBDesignerApp)` hält nur schwache Kopplung (keine eigenen Tk-Widgets).
   - Öffentliche Methoden: `edit_metadata()`, `export_png()`, `export_pdf()`, `export_svg()`, `export_ps()`, perspektivisch `export_process(format: str)` für XML/Mehrformate.
   - Rückgaben: Methoden arbeiten UI-seitig (Dialogs), liefern `None`, setzen Status/Textfeedback.
- **Interna**:
   - `_resolve_canvas_bounds()` → `(x0, y0, width, height)` mit Fallback auf `winfo_width/height`.
   - `_capture_postscript()` → ruft `canvas.postscript(...)`, bereitet `ps_data` auf.
   - `_ensure_ghostscript()` + `_postscript_to_image()` → gemeinsam für PNG/PDF genutzt; wiederverwendbare Utility, damit Tests Ghostscript-Paths injizieren können.
   - `_load_process_dict()` → kapselt `canvas.to_dict()` inkl. Fehlermeldung.
- **Edge-Cases**:
   1. Ghostscript fehlt → klare Fehlermeldung, keine Exceptions im Log.
   2. Canvas leer (`bbox(None)`) → Fallback auf Fenstergröße, damit Export nicht crasht.
   3. Pillow nicht installiert → Hinweis mit Installations-Tipp.
   4. Datei schreibgeschützt → `messagebox.showerror` + Status bleibt unverändert.
   5. `canvas.to_dict()` wirft Fehler → Export wird abgebrochen, Status/Telemetry anpassbar.
- **Zusammenspiel Menü**: Menü ruft nur noch `app.exports.export_*`. Tests können `AppExportIntegration` isoliert mit Fake-Canvas/Fake-Dialogs fahren.
- **Testplan**:
   - Utility-Funktionen via pytest mit Fake-Canvas prüfen (`_resolve_canvas_bounds`, `_load_process_dict`).
   - Ghostscript-Path Setter mit Monkeypatch validieren.
   - Export-Callbacks in `tests/ui` mit Tkinter-Mocks abdecken (kein echter File-Dialog).
   - Regression: bestehende `tests/test_pdf_exporter.py` & `tests/test_svg_exporter.py` unverändert weiterverwenden, ggf. Smoke-Test für PNG hinzufügen.

### Umsetzungsschritte

1. App erweitert `__init__` um `self._exports = AppExportIntegration(self)`; alte `_export_*` Methoden delegieren.
2. Menü-Helfer konsumiert `app.exports` für Commands, erhält optional Referenz im Konstruktor.
3. Gemeinsame Utilities in `app_export.py` so zuschneiden, dass sie auch CLI-/Wizard-Flows nutzen können (z. B. `export_process_to_path(format, path, *, bounds=None)`).
4. Tests/Doku aktualisieren (README Export, `docs/VPB_TODO.md` Phase 4).

## Migrationshinweise
Bestehende direkte Aufrufe (Chat, Validierung, Merge) wurden durch Submit ersetzt:
- Alt: `_on_chat_send` startete eigenen Thread/Job → Neu: `submit('ollama_chat_stream', payload)`
- Alt: `_validate_process_dialog` rief Validierung direkt auf → Neu: Task Submission
- Alt: Merge synchron → Neu: `_merge_full_process_json_task` (Submit)

## Kurzes Beispiel (neuer Task)
```python
# Registrierung
self._app_controller.register('compute_layout', lambda p: layout_service.compute(p['data']))
# Aufruf
self._app_controller.submit('compute_layout', {'data': diagram_dict})
# UI Result Handling in _handle_controller_result
```

## Nutzen
| Problem früher | Lösung jetzt |
|----------------|--------------|
| UI Freeze bei LLM Antwort | Streaming Chunks via Queue |
| Vermischte Logik in `vpb_app.py` | Services + Controller getrennt |
| Schwer erweiterbar | Einheitliches Task-Pattern |
| Kein strukturiertes Telemetrie-Modell | Task + Merge Events |

---
Stand: Async Merge/Patch über Data-Snapshots produktiv; nächste Schritte siehe Roadmap (Cancel, Diff-Visualisierung, Undo-Tasks).
