# vpb_schema.py – VPB-JSON Validierung

## Zweck
Leichte Validierung eines vereinfachten VPB-JSON-Dokuments. Optional können erlaubte Element- und Verbindungstypen vorgegeben werden.

## API
- `validate_vpb_dict(data, allowed_element_types=None, allowed_connection_types=None) -> (ok: bool, msg: Optional[str])`
  - Prüft Struktur: `metadata{}`, `elements[]`, `connections[]`
  - Elemente: eindeutige `element_id`, `element_type`, `name`, `x/y` ganzzahlig
  - Verbindungen: `connection_id`, `source_element`/`target_element` referenzieren existierende Elemente, `connection_type`

## Edge Cases
- `deadline_days` darf fehlen oder muss integer sein
- Unbekannte Felder werden toleriert

## Einsatz
- Validierung von AI-generierten Diagrammen in `vpb_designer_min._text_to_diagram()`

## Datenbankschema & Migration (Ergänzung)
Für die persistente Speicherung existiert `vpb_sqlite_db.py`.

### Migrationen
Das modulare Migrationssystem (`vpb_db_migrations.py`) führt additive Änderungen aus:
- Tabelle `schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT)`
- Version 1.1: Index auf `vpb_processes.updated_at` für schnellere Delta-/Sortierabfragen

Aufruf erfolgt automatisch in `VPBSQLiteDB.init_database()` nach Grundschema.

### Normalisierung
Beim Speichern werden `connection_type` Werte auf UPPERCASE normalisiert, um Domain-Konsistenz zu halten (Prompt-Seite nutzt z. B. `SEQUENCE`).

### Erweiterungspotenzial (zukünftig)
- FTS5 für Volltextsuche (name, description, tags)
- Snapshot-Tabelle statt Feld `process_data`
- CHECK Constraints (Score-Bereiche, Enumerationen)
- Separierung wiederkehrender JSON-Arrays (z. B. legal_basis) in relationale Tabellen

### Validierungs-Pipeline
1. AI-Output → `validate_vpb_json()` (Prompt Core)
2. Optional zusätzlich → `validate_vpb_dict()` (strikt, frühzeitige Fehler)
3. Persistenz über `VPBSQLiteDB.save_process()`

Diese Kaskade reduziert Dateninkonsistenzen und erleichtert spätere Migrationen.