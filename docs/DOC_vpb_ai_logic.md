# vpb_ai_logic.py – Prompt-Orchestrierung mit Beispielen

Zweck: Fügt der Text→Diagramm- und Next‑Steps-Aufforderung kuratierte Default‑Prozessbeispiele (Few‑Shot) hinzu, um Qualität/Konsistenz zu steigern.

API:
- `build_prompt_with_examples_text_to_vpb(description, element_types, connection_types, example_tags=None, max_examples=3) -> str`
- `build_prompt_with_examples_next_steps(current_diagram_json, selected_element_id, element_types, connection_types, example_tags=None, max_examples=3) -> str`
- `validate_model_output(raw_output, *, mode, existing_ids=None, allow_element_types=None, allow_connection_types=None, tolerance="strict") -> dict`

`tolerance="lenient"` sorgt dafür, dass reparierbare Schema-Abweichungen (fehlende Arrays, optionale Felder) automatisch ergänzt werden. Das Ergebnis enthält zusätzlich `repairs` zur Anzeige im UI/Log. Empfohlen ist `lenient` für Add-Only-Diffs der Ingestion-Pipeline.

Beispiele werden aus `vpb_default_processes.get_all_examples()/find_examples_by_tags()` selektiert und mit `render_examples_snippet()` als nicht auszugebender Prompt‑Kontext injiziert.
