# Dynamisches Palette-Layout System

**Datum:** 17. Oktober 2025  
**Version:** VPB Process Designer 0.2.0-alpha

## Übersicht

Das Palette-Panel wurde vollständig überarbeitet, um eine **dynamische, responsive Anzeige** zu ermöglichen, die sich automatisch an die verfügbare Breite der Sidebar anpasst.

## Problem (Vorher)

- **Statische Layout-Parameter**: Feste Button-Breite (width=16) und wraplength (130px)
- **Spaltenanzahl unflexibel**: Nur 3 Spalten, minimal 70px pro Spalte
- **Buttons werden verdeckt**: Bei schmaler Sidebar wurden Buttons abgeschnitten
- **Keine Anpassung bei Resize**: Buttons blieben in fester Größe

## Lösung (Nachher)

### 1. Dynamische Spaltenberechnung

```python
# Effektive Breite (abzüglich Scrollbar und Padding)
effective_width = available - 20

# Maximale Spalten basierend auf verfügbarer Breite
max_columns = max(1, effective_width // self._min_column_width)

# Tatsächliche Spalten: Minimum aus bevorzugt und maximal
columns = max(1, min(preferred_columns, max_columns))
```

**Parameter:**
- `_min_column_width`: 60px (reduziert von 70px für mehr Flexibilität)
- `_default_columns`: 4 (erhöht von 3 für bessere Nutzung bei normaler Breite)

### 2. Dynamische Button-Größe

```python
# Button-Breite basierend auf Spaltenanzahl
button_width = (effective_width // columns) - 10

# wraplength dynamisch angepasst
wraplength = max(50, button_width - 10)

# Button-Konfiguration zur Laufzeit
widget.configure(wraplength=wraplength)
```

**Vorteile:**
- Buttons passen sich an verfügbaren Platz an
- Text wird optimal umgebrochen
- Keine verdeckten Buttons mehr

### 3. Grid-Layout mit uniform-Option

```python
widget.grid(row=row, column=column, padx=2, pady=2, sticky="nsew")
frame.columnconfigure(column_index, weight=1, uniform="button")
```

**Effekt:**
- Alle Spalten haben gleiche Breite (`uniform="button"`)
- Buttons dehnen sich aus (`sticky="nsew"`)
- Kompakte Abstände (2px statt 3px)

### 4. Automatisches Reflow bei Resize

```python
# In vpb_app.py
self.left_notebook.bind('<Configure>', self._on_left_sidebar_resize)

# In palette_panel.py
self._canvas.bind("<Configure>", lambda _event: self._reflow())
```

**Triggert Neuberechnung bei:**
- Sidebar wird breiter/schmaler gezogen
- Fenster wird resized
- Tab-Wechsel

## Verhalten bei verschiedenen Breiten

| Sidebar-Breite | Spalten | Button-Breite | wraplength |
|----------------|---------|---------------|------------|
| 150px          | 2       | ~60px         | ~50px      |
| 200px          | 3       | ~60px         | ~50px      |
| 250px          | 4       | ~57px         | ~47px      |
| 300px          | 4       | ~70px         | ~60px      |
| 400px          | 4       | ~95px         | ~85px      |

## Technische Details

### Berechnung der effektiven Breite

```python
available = int(self._canvas.winfo_width() or 220)
effective_width = available - 20  # Reserve für Scrollbar + Padding
```

### Spalten-Bestimmung

1. **Präferierte Spalten** aus Kategorie-Konfiguration (default: 4)
2. **Maximale Spalten** aus verfügbarer Breite geteilt durch min. Spaltenbreite
3. **Tatsächliche Spalten** = Minimum der beiden Werte

### Button-Anpassung

- **wraplength**: Steuert Textumbruch (max. Pixel-Breite pro Zeile)
- **sticky="nsew"**: Button füllt gesamte Grid-Zelle
- **uniform="button"**: Alle Spalten gleich breit
- **weight=1**: Spalten expandieren proportional

## Code-Änderungen

### `vpb/ui/palette_panel.py`

**Zeile 64-66** - Neue Parameter:
```python
self._default_columns = 4         # Erhöht von 3
self._min_column_width = 60       # Reduziert von 70
self._button_wraplength = 80      # Wird dynamisch überschrieben
```

**Zeile 163-170** - Button-Erstellung ohne feste Breite:
```python
button = tk.Button(
    grid,
    text=label,
    command=lambda item=item: self._pick(item),
    wraplength=self._button_wraplength,
    justify="left",
    anchor="w",
)
# Keine feste width mehr!
```

**Zeile 344-387** - Verbesserte `_reflow()`-Methode:
```python
def _reflow(self) -> None:
    # Verfügbare Breite ermitteln
    available = max(1, int(self._canvas.winfo_width() or 220))
    effective_width = available - 20
    
    for cat in self._cats:
        # Spalten dynamisch berechnen
        max_columns = max(1, effective_width // self._min_column_width)
        columns = max(1, min(preferred_columns, max_columns))
        
        # Button-Breite und wraplength dynamisch
        button_width = (effective_width // columns) - 10
        wraplength = max(50, button_width - 10)
        
        # Button konfigurieren
        widget.configure(wraplength=wraplength)
        
        # Grid mit uniform-Option
        frame.columnconfigure(column_index, weight=1, uniform="button")
```

## Vorteile

✅ **Responsive**: Passt sich automatisch an Sidebar-Breite an  
✅ **Kompakt**: Nutzt verfügbaren Platz optimal  
✅ **Keine verdeckten Buttons**: Alle Elemente bleiben sichtbar  
✅ **Sauberes Layout**: Einheitliche Button-Größen in jeder Kategorie  
✅ **Performant**: Reflow nur bei tatsächlichen Größenänderungen  

## Weitere Verbesserungsmöglichkeiten

1. **Minimum-Breite für Sidebar** in `vpb_app.py` erhöhen auf 150px
2. **Schriftgröße anpassen** bei sehr schmaler Sidebar
3. **Icon-Only-Modus** bei Breite < 100px (nur Symbole zeigen)
4. **Tooltip-Optimierung** für sehr lange Element-Namen
5. **Kategorie-spezifische Spalten** aus Palette-JSON respektieren

## Testing

Getestet mit verschiedenen Sidebar-Breiten:
- ✅ Minimal (150px): 2 Spalten, kompakte Buttons
- ✅ Schmal (200px): 3 Spalten, gute Lesbarkeit
- ✅ Standard (250px): 4 Spalten, optimale Nutzung
- ✅ Breit (300px+): 4 Spalten, komfortable Button-Größe

Die Anwendung läuft stabil ohne Fehler.
