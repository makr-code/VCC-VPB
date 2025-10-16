# vpb_config.py – Zentrale Konfiguration

## Zweck
Sammelt Pfadkonfigurationen, UI/UX-Defaults, Export-Optionen, Compliance-Parameter und Hilfsfunktionen für Templates/Rechtsgrundlagen.

## Wichtige Inhalte
- Verzeichnisse: `DATA_DIR`, `TEMPLATES_DIR`, `EXPORT_DIR`, `LOGS_DIR`, `TEMP_DIR`
- `UDS3_CONFIG`, `VBP_CONFIG`, `UI_CONFIG`, `EXPORT_CONFIG`, `LOGGING_CONFIG`
- Enums: `VerwaltungsEbene`, `RechtsgebietKategorie`
- Templates: `STANDARD_TEMPLATES` (Beispiele), Filterfunktionen
- Logging-Setup, `validate_config()`

## Hinweise
- Erstellt benötigte Ordner automatisch
- Dient vorrangig dem Voll-Editor (`vpb_app.py`), der Minimal-Designer benötigt nur einen Bruchteil
