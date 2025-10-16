# GROUP/Container in VPB – Bedienung und Verhalten

Diese Seite beschreibt die visuelle Gruppierung (Elementtyp `GROUP`) im VPB-Designer. Gruppen dienen ausschließlich der Übersicht; sie haben keine prozessuale Semantik und beeinflussen die Ausführung nicht.

## Überblick
- Elementtyp: `GROUP`
- Zweck: Visuelles Zusammenfassen mehrerer Elemente in einem gestrichelten Containerrahmen
- Persistenz in JSON: optionale Felder `members: string[]` und `collapsed: boolean`
- Darstellung: 
  - Expandiert: gestrichelter Rahmen um alle Mitglieder
  - Zugeklappt: kompaktes Rechteck (wie ein normales Element)
  - Auto-Kompakt: bei starker Verkleinerung (Zoom ≤ 0,5) wird die Gruppe temporär kompakt gerendert, ohne `collapsed` zu ändern

## Anlegen und Auflösen
- „Gruppe aus Auswahl bilden“ (Bearbeiten-Menü):
  - Erst Elemente im Diagramm markieren, dann den Menüpunkt nutzen
  - Die Gruppe wird am Schwerpunkt der Auswahl erstellt und die markierten Elemente als Mitglieder übernommen
- „Gruppe auflösen“:
  - Löscht die Gruppe selbst samt ihrer eingehenden/ausgehenden Verbindungen
  - Mitglieder bleiben unverändert im Diagramm
  - Falls andere Gruppen diese Gruppe als Mitglied führten, werden deren Mitgliederlisten bereinigt

## Eigenschaften-Panel (rechte Seitenleiste)
Wenn eine Gruppe selektiert ist, erscheint der Abschnitt „Gruppe“:
- „Zugeklappt“: Checkbox, die das persistierte `collapsed`-Flag steuert
- „Mitglieder“: Liste der Mitglieder (Anzeige „ID — Name“). Doppelklick selektiert das Element im Diagramm
- Buttons:
  - „Aus Auswahl hinzufügen“: Fügt die aktuell im Diagramm ausgewählten Elemente zur Gruppe hinzu
  - „Aus Auswahl entfernen“: Entfernt die aktuell ausgewählten Elemente aus der Gruppe

Hinweis: Änderungen an den Mitgliedern wirken sofort; die Mitgliederliste aktualisiert sich automatisch.

## Kontextmenü der Gruppe
Bei Rechtsklick auf eine Gruppe:
- „Aufklappen/Zuklappen“: toggelt `collapsed`
- „Auswahl zu Gruppe hinzufügen“
- „Aus Auswahl aus Gruppe entfernen“

## Verhalten beim Zeichnen
- Zeichenreihenfolge: Gruppen werden zuerst gezeichnet, dann andere Elemente. Mitglieder expandierter Gruppen werden einzeln nicht gezeichnet (der Container repräsentiert sie visuell)
- Label-Position: 
  - Expandiert: Beschriftung oben links am Rahmen
  - Zugeklappt/kompakt: Beschriftung zentriert
- Zusatzanzeigen:
  - `[n]` – Anzahl der Mitglieder
  - `(zu)` – wenn `collapsed == true`
  - `(kompakt)` – wenn Auto-Kompakt aufgrund kleiner Zoomstufe aktiv ist

## JSON-Felder
Beispiel (Ausschnitt):
```json
{
  "element_id": "G001",
  "element_type": "GROUP",
  "name": "Gruppe A",
  "x": 400,
  "y": 300,
  "members": ["F001", "E002", "D010"],
  "collapsed": false
}
```
- `members`: Liste der Element-IDs, die visuell zur Gruppe gehören
- `collapsed`: Steuert, ob die Gruppe kompakt gespeichert dargestellt wird

## Grenzen & Hinweise
- Gruppen sind rein visuell; sie ändern keine Verbindungstypen und keine Prozesslogik
- Verbindungen zwischen Innen- und Außenelementen werden normal geroutet
- Verschieben einer Gruppe verschiebt ihre Mitglieder mit
- Rechteckauswahl: Wenn eine Gruppe mit selektiert wird, werden ihre Kinder nicht zusätzlich ausgewählt (reduziert Auswahlrauschen)
- Verschachtelte Gruppen: aktuell nicht speziell behandelt; pragmatisches Verhalten (Container innerhalb Container) funktioniert, aber ohne besondere Regeln

## Palette
- In der Standard-Palette ist `GROUP` als Element verfügbar (gestricheltes Rechteck, Outline #666, Dash [6,4])

## Tastatur/Shortcuts (Auszug)
- Entf: ausgewähltes Element/Verbindung löschen
- Strg+D: duplizieren
- L: Link-Modus umschalten
- F2: Fokus in Chat-Panel
- Ansicht: Zoom-Shortcuts (Strg+0 für Reset, Strg+9 für Fit)

## FAQ
- „Warum sehe ich meine Gruppen plötzlich als kleine Kacheln?“ – Vermutlich greift die Auto-Kompaktansicht bei kleiner Zoomstufe. Zoome näher heran, um die expandierten Rahmen zu sehen.
- „Wirken sich Gruppen auf Validierungen oder Exporte aus?“ – Nein; Gruppen sind nur visuell und werden als reguläre Elemente mit optionalen Feldern gespeichert.
