# ai_prompts.py – Prompt-Bausteine für VPB-AI

## Zweck
Enthält Prompt-Generatoren, die VPB-spezifische Instruktionen formulieren, damit ein LLM konsistentes VPB-JSON erzeugt bzw. Diffs vorschlägt.

## Funktionen
- `build_text_to_vpb_prompt(description, element_types, connection_types)`
  - Liefert eine strikte Anweisung, nur ein einziges gültiges JSON-Objekt mit den Feldern `metadata`, `elements[]`, `connections[]` zurückzugeben.
  - Listet erlaubte `element_type`- und `connection_type`-Werte auf.
- `build_next_steps_prompt(current_diagram_json, selected_element_id, element_types, connection_types)`
  - Erzeugt eine Anweisung für Add-only-Diffs mit genau den Feldern `{ "elements": [...], "connections": [...] }`.
  - Unterstützt Fokussierung auf ein ausgewähltes Element.

## Hinweise
- Die Prompts sind auf deutschsprachige Antworten ausgelegt.
- In Kombination mit `ollama_client.generate_json(...)` wird zusätzlich eine Validierung (Schema/Diff) erzwungen.
- Standard-Instruktionen verlangen vollständig befüllte Objekte; bei fehlenden Informationen werden Defaultwerte (leere Strings, `deadline_days=0`, `responsible_authority="unbekannt"`, `legal_basis="n.n."`) eingefordert.