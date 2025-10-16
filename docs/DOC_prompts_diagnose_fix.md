# Diagnose/Fix Prompt

Funktion: `build_diagnose_fix_prompt(diagram_json, element_types, connection_types)`
- Liefert einen strikten Prompt, der ausschließlich ein JSON mit `issues` und optionalem Add‑Only `patch` erzwingt.
- Für LLM‑Qualität mit Beispielen kombinieren via `build_prompt_with_examples_diagnose_fix(...)`.

Ausgabeform (vereinbart):
- `issues[]`: id, severity (info|warning|error), message, location {element_id|connection_id}, suggestion
- `patch`: { elements: [...], connections: [...] } (nur Add‑Only)
