# vpb_diff.py – Add-only Diff für VPB-Diagramme

## Zweck
Validiert und wendet kleine additive Änderungen (nur „Append“) auf ein VPB-JSON an, ohne bestehende Elemente/Verbindungen zu verändern.

## API
- `validate_add_only_diff(diff, existing_element_ids, allowed_element_types, allowed_connection_types) -> (ok, msg)`
  - Stellt sicher: neue IDs, erlaubte Typen, gültige Referenzen
- `apply_add_only_diff(doc, diff) -> doc` 
  - Kopiert Original und hängt neue `elements`/`connections` an

## Einsatz
- Im Designer für „Nächster Schritt vorschlagen…“: Das LLM liefert ein Diff, das zunächst validiert und dann optional angewendet wird.

## Hinweise
- Kein Löschen/Ändern, nur Hinzufügen
- Verhindert Kollisionen mit existierenden Element-IDs