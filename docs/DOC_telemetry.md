# TelemetryManager & Ereignisse

## Überblick
Der `TelemetryManager` bietet eine leichte, in‑Memory basierte Erfassung strukturierter Ereignisse für Analyse, Debugging und spätere Persistierung. Ereignisse werden als Dictionaries gespeichert und können optional nach Typ gefiltert abgefragt oder in eine JSONL-Datei exportiert werden.

## Architektur
- Ringpuffer (max_events, Standard: 1000) – verhindert ungebremstes Wachstum
- API:
  - `record(event_type: str, **fields)` – fügt Timestamp (`ts`) & Typ hinzu
  - `events(event_type: str | None = None)` – liefert Kopie (optional gefiltert)
  - `flush_jsonl(path)` – schreibt alle aktuellen Ereignisse (append)
  - `clear()` – leert den Puffer

## Aktuell instrumentierte Ereignisse
| Event-Typ        | Auslöser                      | Felder (Kern) |
|------------------|-------------------------------|---------------|
| `merge_full`     | `MergeManager.merge_full`     | `duration_s`, `added_elements`, `added_connections`, `element_renames`, `connection_renames`, `update_mode`, `auto_rename`, `snap` |
| `patch_add_only` | `MergeManager.apply_add_only_patch` | `duration_s`, `added_elements`, `added_connections`, `element_renames`, `connection_renames`, `auto_rename` |

## Beispiel
```python
from telemetry_manager import TelemetryManager
from merge_manager import MergeManager

tm = TelemetryManager(max_events=500)
mm = MergeManager(canvas, telemetry=tm)
mm.merge_full(payload, update_mode="fill-empty", snap=True)
print(tm.events("merge_full"))
```

Beispielausgabe (vereinfacht):
```json
[
  {
    "ts": 1727130635.123456,
    "type": "merge_full",
    "duration_s": 0.012345,
    "added_elements": 5,
    "added_connections": 4,
    "element_renames": 1,
    "connection_renames": 0,
    "update_mode": "fill-empty",
    "auto_rename": true,
    "snap": true
  }
]
```

## Verwendung in Tests
`tests/test_telemetry_merge.py` validiert die Felder und stellt sicher, dass genau ein Ereignis je Vorgang erfasst wird.

## Geplante Erweiterungen
- Feld `conflict_strategy` für `merge_full`
- Ereignisse für Validation (Schema/Prompt) mit counts (warnings, errors)
- Undo/Redo Aktivitäten (`undo`, `redo`) mit Stapelgrößen
- Benutzeraktionen (z. B. Gruppieren, Auto-Layout)
- Optionaler Persist-Thread (periodischer Flush)

## Best Practices
- Für Performance-kritische Pfade nur Kernmetrik-Felder loggen.
- Keine großen Payloads (Diagramm-JSON) direkt in Events ablegen → stattdessen IDs/Counts.
- Bei Export sensibler Daten (Behörden-/Personenbezug) vor Persistierung filtern oder anonymisieren.
