# vpb_app.py – Voller VPB Process Designer (UDS3/VERITAS)

WICHTIG: Umfangreicher Prototyp mit vielen UDS3/VERITAS-Abhängigkeiten. Der Minimal-Designer (`vpb_designer_min.py`) ist losgelöst und lauffähig ohne diese Module.

## Überblick
- Rich-UI (Tkinter) mit Sidebar-Karten, Tooltips, erweiterten Verbindungstypen
- Grid/Zoom/Pan, Drag&Drop, Verbindungspunkte, Routing-Varianten
- Logger, Konfig, Vorlagen, Export, Parser/Validator-Integrationen (BPMN/EPK)

## Warum getrennt?
- Für schnelle Tests und reine VPB-JSON-Bearbeitung ist der Minimal-Designer leichter zu starten und ohne externe Pakete nutzbar.
- `vpb_app.py` eignet sich als Blaupause/Roadmap für Features, die später in den Minimal-Designer migriert werden können.

## Hinweise
- Enthält „VERITAS Protected Module“-Header und Lizenz-Metadaten
- Viele Symbole/Unicode-Icons im UI

## Hierarchie-Management (UI)
- **Ansicht → Hierarchien verwalten…** öffnet den neuen `HierarchyManagerDialog` mit Listenansicht, Detailformular und Validierung. Aktionen:
	- *Neu* erzeugt ein vorberechnetes Band (Name, Farbe, Y-Bereich) – automatisch ohne Überschneidungen und mit sprechender Bezeichnung.
	- *Duplizieren* übernimmt Werte des aktuellen Eintrags mit neuem, eindeutigen Namen.
	- *Löschen* entfernt das markierte Band (mit Sicherheitsabfrage).
	- *Nach oben/unten* sortiert Bänder ohne zusätzliche Dialoge.
	- Detailfelder (Name, Farbe via Picker, Y-Beginn/Y-Ende) werden live validiert; Namen müssen eindeutig sein, Farbe verlangt das Muster `#RRGGBB`.
- Beim Bestätigen werden Canvas, Hierarchie-Leiste, Eigenschaftenpanel sowie Settings in einem Schritt synchronisiert; Undo (Ctrl+Z) bleibt möglich.
- Der bisherige JSON-Editor ist weiterhin über **Ansicht → Hierarchie JSON bearbeiten…** verfügbar (zuvor „Hierarchie konfigurieren…“).
- Das Eigenschaftenpanel reagiert sofort auf Änderungen und bietet die aktualisierten Hierarchie-Namen in allen Element-Dropdowns an.

## AI-gestützter Diagramm-Workflow: Replace vs. Merge

Seit der Einführung des erweiterten Chat-Postprocessings stehen nach einer erfolgreichen LLM-Antwort zwei Hauptaktionen für vollständige Diagramm-Vorschläge zur Verfügung:

1. Diagramm ersetzen (Replace)
2. Diagramm mergen (Merge / Additiv einfügen)

### 1. Diagramm ersetzen
Ersetzt den kompletten aktuellen Inhalt des Canvas durch das vom Modell gelieferte vollständige VPB JSON.

Eigenschaften:
- Vollständiger Austausch (Undo möglich via Ctrl+Z)
- Vorher: Validierung (Prompt-Core + Fallback Schema) – fatale Fehler brechen ab
- Warnungen/Hinweise erscheinen als zusätzlicher Chat-Block `[Validierung Hinweise]`
- Nach Übernahme Auto-Fit des Diagramms

Typische Nutzung:
- Frischer Start aus einer Textbeschreibung
- Radikale Neugestaltung, wenn existierender Stand verworfen werden soll

### 2. Diagramm mergen
Fügt alle neuen Elemente und Verbindungen eines vollständigen LLM-Diagramms additiv in das bestehende Diagramm ein, ohne vorhandene Objekte zu löschen oder deren Felder zu überschreiben.

Regeln & Ablauf (_siehe Implementierung `_merge_full_process_json` in `vpb_app.py`_):
1. Validierung identisch zum Replace-Pfad (Prompt-Core + Schema). Fatale Fehler → Abbruch.
2. Elemente werden in einer ersten Phase vorbereitet:
	- ID-Kollisionen mit bestehenden Elementen werden automatisch durch Suffix-Inkrement (`_1`, `_2`, …) aufgelöst.
	- Mapping der umbenannten IDs wird aufgezeichnet (`rename_map_e`).
3. Connections werden in einer zweiten Phase verarbeitet:
	- Quellen/Ziele werden anhand des Element-Rename-Mappings aktualisiert.
	- Verbindungen werden nur erzeugt, wenn beide Enden (entweder bestehend oder neu hinzukommend) vorhanden sind.
	- Kollisionen bei Connection-IDs werden analog per Suffix-Inkrement umbenannt (`rename_map_c`).
4. Anwendung auf Canvas:
	- Für jedes neue Element wird `add_element` aufgerufen. Falls ein vorgefertigter `element_id` existiert (nach möglichem Rename), wird diese explizit gesetzt.
	- Attribute wie `description`, `responsible_authority`, `legal_basis`, `deadline_days` werden übernommen (nur für neue, nicht für bestehende Elemente).
5. Zusammenfassung im Chat als Block `[Merge Ergebnis]` mit:
	- Anzahl hinzugefügter Elemente / Verbindungen
	- Auflistung der vorgenommenen Umbenennungen (Elemente & Connections)

Wesentliche Eigenschaften:
- Nicht-destruktiv für vorhandenes Diagramm
- Deterministische, einfache ID-Rename-Strategie (kein Hash, gut lesbar)
- Undo vollständig möglich (ein einziger Undo-Step für gesamten Merge)

Einsatzszenarien:
- Erweiterung eines existierenden Prozesses um generierte Teilabläufe
- Schnelles Experimentieren mit alternativen Varianten einzelner Prozesssegmente

### Validierungsschichten
Beide Pfade nutzen – sofern Modul verfügbar – `validate_vpb_json` aus `vpb_prompt_core`:
- Modus: `text_to_vpb`
- Prüft Struktur, erlaubte Typen, ID-Fundamentalfehler, potentielle Leaks (Echo von Beispielen), Basis-Constraints
- Fällt bei Import-Fehler oder Ausnahme still auf Schema-Fallback `_validate_vpb_data_safe` zurück

### Unterschiede Replace vs. Merge (Kurzvergleich)
| Aspekt | Replace | Merge |
|--------|---------|-------|
| Wirkung | Vollständiger Austausch | Additives Hinzufügen |
| Bestehende Elemente | Werden entfernt/überschrieben | Bleiben unverändert (optional Feld-Updates) |
| ID-Konflikte | Irrelevant (altes Diagramm weg) | Auto-Rename (Suffix) |
| Verbindungsvalidität | Kopiert 1:1 | Nur wenn beide Enden existieren |
| Undo | 1 Schritt | 1 Schritt |
| Chat-Zusatz | Hinweise | Hinweise + Merge Ergebnis |

### Merge Update-Modus
Konfigurierbar über AI-Menü → "Merge: Update-Modus":

| Modus | Verhalten bestehende Elemente |
|-------|------------------------------|
| none | Keine Änderungen an vorhandenen Feldern |
| fill-empty | Nur leere / Default-Felder ("", 0, None) werden gefüllt (name, description, responsible_authority, legal_basis, deadline_days) |
| overwrite | Alle obigen Felder werden überschrieben |

Hinweis: Neue Elemente werden immer vollständig mit allen gelieferten Feldern angelegt. Updates betreffen nur Elemente, deren IDs bereits existieren (vor Auto-Rename).

### Geplante Erweiterungen (Backlog-Auszug)
- Konfigurierbarer Merge-Modus (Felder vorhandener Elemente selektiv aktualisieren)
- Toggle für Auto-Rename (Warnung statt automatischer Anpassung)
- Raster-Snap neu eingefügter Elemente (Option: "Merge: Raster-Snap (50)")
- Telemetrie/Logging-Hooks für Merge KPIs
- Verbesserte Undo/Redo UX (In-UI Rückgängig-Button nach Merge)

### Best Practices
- Vor Merge einen Undo-Punkt manuell (optional) setzen: nicht nötig, der Code macht es automatisch – aber bewusstes Arbeiten hilft bei komplexen Merges.
- Nach einem großen Merge: Diagramm kurz visuell prüfen (Layout), ggf. Auto-Layout gezielt auf neu hinzugefügte Elemente anwenden (Feature in Planung).
- IDs mit semantischer Bedeutung (z.B. domänenspezifische Kürzel) früh festlegen, um zu viele Suffix-Renames bei iterativen Merges zu vermeiden.

### Troubleshooting
- Fehlermeldung "Fataler Validierungsfehler": LLM-Ausgabe enthält strukturelle oder modusspezifische Verstöße – im Chat nachbessern (z.B. um präzisere Anweisung bitten) und erneut generieren.
- Verbindungen fehlen nach Merge: Wahrscheinlich fehlte ein End-Element im generierten Ausschnitt – LLM gezielt nach den fehlenden Elementen fragen oder Replace anwenden.
- Unerwartete Suffixe: Im `[Merge Ergebnis]`-Block steht die Mapping-Liste. Diese kann als Referenz in nachfolgenden Patch-Prompts genutzt werden.

---
_(Abschnitt zuletzt aktualisiert: Merge/Replace Feature Integration – Datum siehe Git-Historie)_

