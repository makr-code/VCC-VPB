# VPB Process Designer – Entwicklungs‑Roadmap

Stand: 23.09.2025

## Überblick und Ziele

Der VPB Process Designer ist ein eigenständiger Tkinter‑Editor zum Modellieren von VPB‑Prozessen. Ziel ist ein schnelles, stabiles und nutzerfreundliches Tool mit:

- Zuverlässigem Editor (Pan/Zoom, Multi‑Select, Link‑Modus, Grid/Snap, Guides, Ruler)
- Palette mit Element‑ und Verbindungstypen inkl. Stil‑Presets
- Diagramm↔Code Synchronisierung mit optionaler JSON‑Validierung
- Optionaler AI‑Integration (Ollama) für Assists (Text→Diagramm, Diagnose)
- Gute UX (ttk Panes, persistente Einstellungen) und später Export/Minimap/Tooling

## Aktueller Stand (Kurz)

Umgesetzt (Done):
- Stabiler Start, PanedWindow/UX, Ruler, Rectangle‑Selection, Undo/Redo
- Palette → Link‑Modus (Verbindungen), diversifizierte Palette (inkl. arrow_style)
- Element‑Stile: Palette‑Defaults + Settings‑Overrides + Editor‑Dialog
- Diagramm↔Code‑Tab Sync, Fehler‑Highlighting, Schema‑Option
- Export als PDF (Diagrammseite + Detailübersicht) und PNG, PostScript weiterhin verfügbar; erste SVG-Ausgabe vorhanden

Offen (Highlights):
- Scrollbars an Content‑Extents koppeln
- Drag‑Performance (inkrementelles Redraw, Throttle)
- Guides skalieren (Spatial Index)
- UX-Polish (Tooltips, Zoom‑Anzeige, Shortcuts)
- Doku, Minimap, Exporte, QA

## Architektur‑Skizze

- `VPBCanvas`: Model‑View‑Transform, Zeichnung, Interaktion, Routing, Undo/Redo
- Palette: JSON‑basierte Kategorien/Items; Element‑/Verbindungstypen, Stil‑Presets
- Stile: Default (`ELEMENT_STYLES`) ← Palette‑Defaults ← Settings‑Overrides
- App‑Shell: ttk PanedWindow, Notebook (Diagramm/Code), Properties/Chat
- Persistenz: `settings.json` (Fenster, Panes, View, Stil‑Overrides)

## Meilensteine und Akzeptanzkriterien

### M1 – Editor Reifegrad (Core Polishing)
- Scrollbars: Thumb/Range auf Basis realer Diagramm‑Extents
- Drag‑Performance: inkrementelles Redraw + 60fps‑Throttle
- Guides: einfacher Spatial Index (Buckets) für Nachbarschaftssuche
- Akzeptanz:
  - Dragging >100 Knoten flüssig (keine merklichen Janks)
  - Scrollbars repräsentieren Umläufe korrekt (kein „5000“-Hack)

### M2 – UX‑Verbesserungen
- Tooltips für Palette (mit Mini‑Preview)
- Zoom‑Anzeige in Statusleiste, +/- Shortcuts
- Space+Drag als Pan, Ctrl+A Auswahl, Ctrl+1..4 Routing
- Akzeptanz:
  - Tooltip erscheint <300ms, zeigt Typ + Stil
  - Statusleiste aktualisiert Zoom live

### M3 – Navigation & Überblick
- Minimap rechts unten (Viewport‑Rechteck, Drag zur Navigation)
- Fit‑to‑Diagramm verbessert (auf Content‑Extents)
- Akzeptanz:
  - Minimap skaliert sinnvoll mit Diagramm und ist flüssig bewegbar

### M4 – Export & Sharing
- Export: PNG (Pillow) abgeschlossen, Basis-SVG liegt vor; langfristig SVG-Stile/Layering ausbauen
- PDF (Diagramm + Text) ist implementiert und dient als Referenz für weitere Formate
- Optional: PostScript bleibt bestehen
- Akzeptanz:
  - Exporte zeigen das Diagramm korrekt mit Labels/Arrows

### M5 – Internationalisierung & Themes
- Light/Dark Theme mit Laufzeit‑Switcher
- EN‑Lokalisierung für UI‑Texte (einfache i18n‑Schicht)
- Akzeptanz:
  - Umschaltung ohne Neustart, UI gut lesbar in beiden Themes

### M6 – Stabilität & Datenfluss
- Autosave & Recovery (Crash‑Recovery beim Start)
- Vorlagen‑Browser (links) aus `vpb_config.TEMPLATE_CATEGORIES`
- Akzeptanz:
  - Autosave‑Intervalle einstellbar; Recovery‑Prompt beim Start
  - Templates laden per Klick ins Diagramm

## Backlog (priorisiert)

Must (hohe Priorität):
- Scrollbars korrekt an Inhalt koppeln
- Drag‑Performance: inkrementelles Redraw + Throttle
- Guides skalieren (Spatial Index)

Should (mittlere Priorität):
- Palette‑Tooltips mit Preview
- Zoom‑Anzeige Statusleiste, zusätzliche Shortcuts
- Mini‑Map Navigationsfenster
- PNG/SVG Export

Could (niedrige Priorität):
- Light/Dark Theme, EN‑Lokalisierung
- Autosave & Recovery
- Vorlagen‑Browser UI
- Validierungs‑Badges/Heatmap
- Manuelles Routing/Waypoints
- Snap/Align/Distribute Buttons
- Gruppieren & Mehrfachaktion
- Suche/Filter im Diagramm
- Undo‑Historie‑Viewer

## Qualitätsstrategie

- Build/Lint: Syntaxcheck (CI), optionale Formatierung (Black) – später
- Unit‑Tests (schrittweise):
  - JSON‑Load/Save Roundtrip
  - Routing‑Punktberechnung (Edge‑Cases)
  - Stil‑Auflösung (Default/Palette/Overrides)
- Manuelle Smoke‑Tests pro Release:
  - Start/Beenden, Laden/Speichern
  - Pan/Zoom, Multi‑Select, Link‑Modus
  - Diagramm↔Code Sync + Fehlerhighlight
- Performance‑Checks:
  - 100/200/500 Knoten Szenarien (Drag/Zoom)

## Risiken & Abhängigkeiten

- Tkinter Rendering: Performance‑Grenzen bei vielen Canvas‑Items
- Exporte (SVG/PNG) erfordern externe Pakete (Pillow/cairosvg)
- AI‑Integration (Ollama): lokale Verfügbarkeit/Modelle variieren

## Umsetzungsplan (Sprint‑Skizze)

1. M1 Core Polishing (1–2 Wochen)
   - Scrollbars, Drag‑Perf, Guides‑Index
2. M2 UX (1 Woche)
   - Tooltips, Zoom‑Anzeige, Shortcuts
3. M3 Navigation (0.5–1 Woche)
   - Minimap, Fit‑to‑Diagramm
4. M4 Export (0.5–1 Woche)
   - PNG/SVG, QA
5. M5 Theme & i18n (0.5–1 Woche)
6. M6 Stabilität & Templates (1 Woche)

Hinweise: Zeitangaben sind grobe Richtwerte für Einzelentwickler.

## Akzeptanzkriterien (Detail)

- Scrollbars: Bounds aus tatsächlichen Element/Connection‑Bboxen abgeleitet; Zoom/Pan wirken korrekt auf Thumb
- Performance: Drag‑Operationen nutzen coords‑Updates statt Full‑Redraw; Redraw‑Throttle ~16ms
- Tooltips: Anzeigename, Typ, Stilfelder (fill/outline/shape/arrow/…) + Mini‑Symbol
- Minimap: Viewport verschiebbar; kein spürbarer CPU‑Spike
- Exporte: Datei‑Dialog, Fehler‑Dialoge, Erfolgsmeldung; Farben/Arrows/Labels erhalten

## Tracking & Pflege

- Roadmap wird in `docs/DEV_ROADMAP.md` gepflegt
- Kurzfristige Aufgaben im integrierten ToDo‑Board (Menü/Kommentare)
- Wichtige Entscheidungen/Änderungen in `CHANGELOG.md` (später)

---

Anhang A – Mapping aktueller Todos

- Scrollbars korrekt an Inhalt koppeln → M1
- Drag‑Performance (inkrementelles Redraw + Throttle) → M1
- Guides skalieren (Spatial Index) → M1
- Palette‑Tooltips mit Preview → M2
- Zoom‑Anzeige Statusleiste → M2
- Zusätzliche Shortcuts → M2
- Mini‑Map Navigationsfenster → M3
- PNG/SVG Export → M4
- Light/Dark Theme → M5
- EN‑Lokalisierung → M5
- Autosave & Recovery → M6
- Vorlagen‑Browser UI → M6
- Validierungs‑Badges/Heatmap → Backlog (Could)
- Manuelles Routing/Waypoints → Backlog (Could)
- Snap/Align/Distribute → Backlog (Could)
- Gruppieren & Mehrfachaktion → Backlog (Could)
- Suche/Filter im Diagramm → Backlog (Could)
- Undo‑Historie‑Viewer → Backlog (Could)
