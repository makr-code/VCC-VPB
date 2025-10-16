# vpb_data_preparation.py – Datenaufbereitung für LLMs (UDS3)

WICHTIG: Teil der UDS3/VERITAS-Toolchain. Nicht erforderlich für den Minimal-Designer.

## Zweck
Erzeugt aus VPB-Prozessdaten strukturierte, semantisch angereicherte Textkontexte für LLM-Analysen (Überblick, Struktur, Recht, Compliance, Behörden, Fluss, Engpässe, Optimierung, Details, Metriken).

## Hauptklassen
- `VPBLLMContext` – Container der aufbereiteten Abschnitte
- `VPBDataPreparator` – Pipelines zur Erzeugung des Kontexts inkl. Hilfsfunktionen

## Output
- Strings/Listen für Prompterstellung, z. B. für Analyse/Optimierung/Erklärung

## Abhängigkeiten
- `vpb_sqlite_db`, `uds3_vpb_schema` (externe Modelle)
