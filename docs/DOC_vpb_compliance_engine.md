# vpb_compliance_engine.py – VBP-Compliance-Engine

WICHTIG: Teil der UDS3/VERITAS-Toolchain. Nicht erforderlich für den Minimal-Designer.

## Zweck
Validiert UDS3/VPB-Prozesse gegen behördliche Standards:
- BVA-Konventionenhandbuch V3
- FIM-Interoperabilität
- DSGVO-Anforderungen
- IT-Sicherheitsklassifikation

## Kernklassen
- `VBPComplianceEngine` – Lädt Regelsets, führt Validierungen aus, berechnet Scores/Level
- `VBPComplianceReport` – Aggregiert Ergebnisse in einen Report mit Action Items
- `VBPValidationRule` (dataclass) – Beschreibung einzelner Regeln
- `VBPComplianceResult` (dataclass) – Ergebnisstruktur

## API (Auszug)
- `validate_uds3_process(doc: Dict) -> VBPComplianceResult`
- `generate_compliance_report(doc: Dict) -> Dict`
- `get_vbp_compliance_engine()` / `get_vbp_compliance_report()`

## Output
- Gesamt-Score, Kategorie-Scores (bva, fim, dsgvo, security), Violations, Warnings, Recommendations, Certification-Status

## Hinweise
- Enthält „VERITAS Protected Module“-Sektion (nicht verändern)
- Eingabe: UDS3-Dokumentstruktur mit `content`, `verwaltungsattribute`
