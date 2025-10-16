# vpb_default_processes.py – Default‑/Beispielprozesse für LLMs

Enthält eine kleine, saubere Bibliothek von VPB‑JSON‑Beispielen (im 50er Raster, SEQUENCE‑Flows), u. a.:
- antrag_minimal – Antrag prüfen, Entscheidung, Bescheid
- widerspruch_basic – Widerspruch, Abhilfe/Widerspruchsbescheid
- frist_escalation – Frist setzen/überwachen, Eskalation
- geo_context_basic – Geo‑Kontext erfassen, Lage prüfen
- kommunikation_message – Nachricht an Beteiligte

Nutzung:
- Per `find_examples_by_tags(["antrag"])` die relevantesten Beispiele auswählen
- Mit `render_examples_snippet(examples)` als Few‑Shot‑Prompt‑Abschnitt injizieren (nicht ausgeben lassen)
