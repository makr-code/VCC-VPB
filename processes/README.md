# Default-Pipelines (VPB)

Kleine, saubere Startbeispiele zum schnellen Testen im VPB‑Designer.

Enthaltene Dateien:
- `default_hello_world.vpb.json` – Start → Hello → Ende
- `default_two_steps.vpb.json` – Zwei aufeinander folgende Schritte
- `default_decision.vpb.json` – Entscheidung mit zwei Enden (Ja/Nein)
- `default_parallel.vpb.json` – Parallele Pfade mit Join
- `default_loop.vpb.json` – Wiederholungsschleife bis OK

Weitere domänenspezifische Beispiele:
- `antrag_basic_low.vpb.json` – Einfacher Antragsprozess (low)
- `antrag_extended_medium.vpb.json` – Erweiterter Antragsprozess mit Entscheidung (medium)
- `widerspruch_basic_low.vpb.json` – Abhilfe oder Widerspruchsbescheid (low)
- `gewerbeanmeldung_medium.vpb.json` – Gebühren, Registrierung, Bescheid (medium)
- `baugenehmigung_high.vpb.json` – Fachprüfungen, Entscheidung, Bescheide (high)
- `melderegister_auskunft_low.vpb.json` – Auskunft/ablehnen (low)
- `umzug_ummeldung_medium.vpb.json` – Ummeldung mit Bescheinigung (medium)
- `dsgvo_auskunft_medium.vpb.json` – DSGVO‑Auskunft oder Ablehnung (medium)

Inline‑Subprozess Beispiel:
- `inline_subprocess_example_main.vpb.json` – Enthält zwei Elemente vom Typ `SUBPROCESS` mit `ref_file` auf vorhandene Default‑Pipelines.
  - Kontextmenü auf dem SUBPROCESS: „Subprozess expandieren (inline)“ oder „Referenz öffnen (ersetzen)“

Format
- JSON mit folgenden Top‑Level‑Feldern:
  - `metadata`: `{ name, description }`
  - `elements[]`: Objekte mit `element_id`, `element_type` (z. B. START_EVENT, FUNCTION, GATEWAY, END_EVENT), `name`, `x`, `y`, `description`, `responsible_authority`, `legal_basis`, `deadline_days`, `geo_reference`
  - `connections[]`: Objekte mit `connection_id`, `source_element`, `target_element`, `connection_type` (z. B. SEQUENCE), `description`
- Koordinaten sind grob im 50‑Pixel‑Raster angeordnet.

Verwendung im Designer
1) Datei → Öffnen → eine der `.vpb.json` Dateien auswählen
2) Diagramm ansehen/verschieben/zoomen
3) Bei Bedarf unter neuem Namen speichern

Ausblick: Inline‑Pipelines
- Realisiert: Elementtyp `SUBPROCESS` mit Feldern: `element_id`, `element_type`="SUBPROCESS", `name`, `x`, `y`, `ref_file`.
- Designer‑Unterstützung:
  - Label zeigt Dateiname der Referenz an.
  - Kontextmenü: inline expandieren (IDs werden mit Präfix versehen, Position wird passend verschoben), oder Referenzdatei direkt öffnen.
  - Relative Pfade beziehen sich auf das Verzeichnis der geöffneten Hauptdatei.
