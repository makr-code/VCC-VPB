# Feature: Intelligentes Fenster-Resize-Verhalten

## Übersicht

Das Hauptfenster wurde so konfiguriert, dass beim Vergrößern des Fensters der **Content-Bereich (mittlere Spalte)** maximiert wird, während die **Sidebars (links/rechts) eine feste Mindestbreite** von 250px behalten.

## Änderungen

### PanedWindow Stretch-Konfiguration

**Datei:** `vpb_app.py`

```python
# Linke Sidebar (Palette)
self.paned_window.add(
    self.palette_view, 
    minsize=250,        # Mindestbreite: 250px
    width=250,          # Initiale Breite: 250px
    stretch='never'     # Nicht beim Resize expandieren
)

# Mittlere Spalte (Content - Canvas/Code/XML)
self.paned_window.add(
    self.mid_notebook, 
    minsize=400,        # Mindestbreite: 400px
    stretch='always'    # IMMER beim Resize expandieren
)

# Rechte Sidebar (Properties/MiniMap)
self.paned_window.add(
    self.right_paned, 
    minsize=250,        # Mindestbreite: 250px
    width=300,          # Initiale Breite: 300px
    stretch='never'     # Nicht beim Resize expandieren
)
```

## Verhalten

### Vor der Änderung
- ❌ Alle drei Spalten vergrößerten sich proportional
- ❌ Sidebars wurden zu breit bei großen Fenstern
- ❌ Content bekam nicht den gesamten zusätzlichen Platz

### Nach der Änderung
- ✅ Sidebars behalten feste Breite (250px links, 300px rechts)
- ✅ Content (mittlere Spalte) erhält **gesamten zusätzlichen Platz**
- ✅ Beim Verkleinern: Sidebars schrumpfen bis min 250px, dann Content

## Resize-Szenarien

### 1. Fenster vergrößern (z.B. 1200px → 1600px)
```
Vorher (1200px):
┌─────────┬──────────────┬─────────┐
│ Palette │   Content    │Properties│
│  250px  │    650px     │  300px   │
└─────────┴──────────────┴─────────┘

Nachher (1600px):
┌─────────┬────────────────────┬─────────┐
│ Palette │      Content       │Properties│
│  250px  │      1050px        │  300px   │
└─────────┴────────────────────┴─────────┘
         +400px zusätzlicher Platz →  ✓
```

### 2. Fenster verkleinern (z.B. 1200px → 900px)
```
Vorher (1200px):
┌─────────┬──────────────┬─────────┐
│ Palette │   Content    │Properties│
│  250px  │    650px     │  300px   │
└─────────┴──────────────┴─────────┘

Nachher (900px):
┌─────────┬─────────┬─────────┐
│ Palette │ Content │Properties│
│  250px  │  350px  │  300px   │
└─────────┴─────────┴─────────┘
      Content schrumpft →  ✓
```

### 3. Extremes Verkleinern (< 800px)
```
Bei 800px (Minimum):
┌─────────┬─────────┬─────────┐
│ Palette │ Content │Properties│
│  250px  │  300px  │  250px   │
└─────────┴─────────┴─────────┘
    Beide Sidebars bei 250px Minimum →  ✓
```

## Technische Details

### Tkinter PanedWindow `stretch` Option

**Parameter:**
- `stretch='always'` - Pane expandiert immer beim Resize
- `stretch='never'` - Pane behält feste Größe (bis minsize)
- `stretch='first'` - Nur erste Pane expandiert (Standard bei erstem Pane)
- `stretch='last'` - Nur letzte Pane expandiert

**Unsere Konfiguration:**
```python
# 3-Spalten-Layout mit mittlerem Content-Expand
Palette    → stretch='never'   # Links: Fest
Content    → stretch='always'  # Mitte: Expandiert
Properties → stretch='never'   # Rechts: Fest
```

### Mindestbreiten

| Bereich | Mindestbreite | Initiale Breite | Stretch |
|---------|---------------|-----------------|---------|
| Palette (links) | 250px | 250px | never |
| Content (mitte) | 400px | flexibel | always |
| Properties (rechts) | 250px | 300px | never |
| **Gesamt (minimum)** | **900px** | - | - |

## Vorteile

### Benutzererfahrung
- ✅ **Mehr Canvas-Platz** - Bei großen Monitoren maximaler Arbeitsbereich
- ✅ **Stabile Sidebars** - Werkzeuge/Properties bleiben übersichtlich
- ✅ **Vorhersehbares Verhalten** - Sidebars "kleben" an Fensterkanten
- ✅ **Responsive Design** - Funktioniert auf allen Bildschirmgrößen

### Entwicklung
- ✅ **Einfache Konfiguration** - Nur `stretch`-Parameter
- ✅ **Native Tkinter** - Keine externe Bibliothek
- ✅ **Konsistent** - Gleiche Logik für alle PanedWindows

## Best Practices

### Empfohlene Fenstergrößen
- **Minimum:** 900px × 600px (alle Bereiche bei Mindestbreite)
- **Optimal:** 1400px × 800px (Content hat genug Platz)
- **Groß:** 1920px × 1080px (Content nutzt vollen Monitor)

### Manual Resize (Sash ziehen)
User können dennoch manuell die Sash-Trennlinien ziehen:
- Palette breiter machen → Content schrumpft
- Properties breiter machen → Content schrumpft
- `stretch='never'` verhindert nur automatisches Resize

## Testing

### Getestet
✅ Fenster horizontal vergrößern → Content expandiert
✅ Fenster horizontal verkleinern → Content schrumpft
✅ Minimum-Breiten respektiert (250px Sidebars)
✅ Manuelle Sash-Anpassung funktioniert weiterhin
✅ App startet ohne Fehler

### Test-Command
```bash
python vpb_app.py --load test_process.vpb.json
# → Fenster vergrößern/verkleinern
# → Content-Bereich passt sich an
# → Sidebars bleiben bei fester Breite
```

## Zusammenfassung

**Problem:**
Beim Fenster-Resize wurden alle Bereiche proportional vergrößert, was zu unnötig breiten Sidebars führte.

**Lösung:**
`stretch='always'` für Content, `stretch='never'` für Sidebars.

**Ergebnis:**
Professionelles, vorhersehbares Resize-Verhalten wie in modernen IDEs (VS Code, IntelliJ, etc.).

✅ **Status:** Implementiert und getestet
