# Paletten-Format

- Datei: JSON, Root: { "categories": [ ... ] }
- Kategorie: { "id": string, "title": string, "items": [ ... ] }
- Item:
  - type: Element- oder Verbindungstyp (z. B. FUNCTION, START_EVENT, SEQUENCE, MESSAGE, ...)
  - name: Anzeigename
  - optional symbol (wird vor dem Namen angezeigt)
  - optional arrow_style (nur für Verbindungen): "none" | "single" | "double"
  - optionale Stilfelder (nur für Elemente):
    - shape: "rect" | "rectangle" | "oval" | "circle" | "diamond" | "hex"
    - fill: Hex-Farbe wie "#E6F3FF"
    - outline: Hex-Farbe
    - dash: Array z. B. [4,4] oder String "4,4"
    - text_color: Hex-Farbe für die Beschriftung

  - optionale Referenz-Metadaten (für wiederverwendbare Prozessschnipsel):
    ```json
    "reference": {
      "id": "ref-terminvereinbarung",
      "snippet": "processes/terminvereinbarung_einfach.vpb.json",
      "name": "Terminvereinbarung – Bürgerbüro",
      "default_name": "Terminvereinbarung – Bürgerbüro",
      "element_type": "SUBPROCESS",
      "auto_group": true,
      "category": "Bürgerdienste",
      "label": "Terminvereinbarung",
      "description": "Standardprozess für Online- und Telefon-Terminbuchungen",
      "responsible_authority": "Bürgeramt",
      "legal_basis": "§ 39 VwVfG",
      "deadline_days": 3,
      "geo_reference": "Landkreis Potsdam-Mittelmark"
    }
    ```
    - `snippet`/`snippet_file`/`path`: Relativer oder absoluter Pfad zur `.vpb.json`-Datei.
    - `auto_group` (Standard `true`): Legt das referenzierte Diagramm automatisch als Gruppe an.
    - Weitere Felder (`description`, `responsible_authority`, `legal_basis`, `deadline_days`, `geo_reference`) werden nach dem Einfügen direkt in die Eigenschaften übernommen.
  - Für Verwaltungsverfahren empfiehlt sich, `legal_basis` mit konkreten Paragrafen (z. B. §§ 22–41 VwVfG, §§ 68–73 VwGO) zu hinterlegen und `deadline_days` an typischen Fristen auszurichten.

Die Anwendung erkennt Verbindungstypen daran, dass `type` ein Schlüssel in `CONNECTION_STYLES` ist. In diesem Fall startet ein Klick auf das Item den Link-Modus für diesen Verbindungstyp.

Für Element-Items werden die optionalen Stilfelder als "Palette-Defaults" übernommen und mit den globalen Defaults sowie etwaigen Benutzereinstellungen (settings.json → element_styles) zusammengeführt.
