# vpb_sqlite_db.py – SQLite-Persistenz für VPB

WICHTIG: Dieses Modul gehört zum umfangreicheren UDS3/VERITAS-Stack und wird vom Minimal-Designer nicht benötigt.

## Zweck
Persistente Speicherung von VPB-Prozessen in SQLite. Enthält Schema-Setup, CRUD, Statistiken und CLI.

## Haupt-API
- `VPBSQLiteDB(db_path)`
  - `save_process(process)`
  - `load_process(process_id)`
  - `list_processes(status=None, authority_level=None)`
  - `delete_process(process_id)`
  - `get_statistics()`

## Datenmodell (vereinfacht)
- Tabelle `vpb_processes`: Metadaten, Kennzahlen, Komplett-JSON
- Tabelle `vpb_elements`: Element-Attribute
- Tabelle `vpb_connections`: Verbindungs-Attribute

## Abhängigkeiten
- Externe Modelle aus `uds3_vpb_schema` u. a. (nicht im Minimal-Designer enthalten)

## CLI
- Init, List, Stats, Import, Export
