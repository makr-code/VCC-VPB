# Separate Notebooks für Eigenschaften und Übersicht ✅

**Datum:** 14. Oktober 2025  
**Feature:** Eigenschaften und Übersicht als separate Notebooks  
**Status:** ✅ Implementiert

---

## 📋 Änderung

### Vorher:
```
Rechte Spalte:
┌──────────────────┐
│ ┌──────────────┐ │
│ │ Eigenschaften│ │ ← Tab 1
│ ├──────────────┤ │
│ │  Übersicht   │ │ ← Tab 2  
│ └──────────────┘ │
└──────────────────┘
```
Ein Notebook mit 2 Tabs - Tab-Umschaltung erforderlich

### Nachher:
```
Rechte Spalte (Vertical PanedWindow):
┌──────────────────┐
│ ┌──────────────┐ │
│ │ Eigenschaften│ │ ← Notebook 1
│ └──────────────┘ │
├──────────────────┤ ← Resizable Sash
│ ┌──────────────┐ │
│ │  Übersicht   │ │ ← Notebook 2
│ │  (MiniMap)   │ │
│ └──────────────┘ │
└──────────────────┘
```
Zwei separate Notebooks - beide gleichzeitig sichtbar!

---

## 🎯 Vorteile

### 1. Beide gleichzeitig sichtbar
- **Vorher:** Tab-Umschaltung zwischen Properties und MiniMap
- **Jetzt:** Properties OBEN, MiniMap UNTEN - beide immer sichtbar
- Kein Tab-Wechsel mehr nötig!

### 2. Größe individuell anpassbar
- Vertikaler Sash (Trennlinie) ist verschiebbar
- Mehr Platz für Properties → MiniMap kleiner
- Mehr Platz für MiniMap → Properties kleiner
- Flexibel nach Bedarf anpassbar

### 3. Besserer Workflow
- Element im Canvas auswählen
- Properties zeigt Details (Name, Typ, etc.)
- MiniMap zeigt Position im Gesamtdiagramm
- Alles auf einen Blick!

---

## 🔧 Implementierung

```python
# vpb_app.py - _init_views()

# Rechte Spalte: Vertikales PanedWindow für Properties und MiniMap
self.right_paned = tk.PanedWindow(
    self.paned_window, 
    orient=tk.VERTICAL, 
    sashwidth=5
)
self.paned_window.add(self.right_paned, minsize=250, width=300)

# Oberes Notebook: Properties
self.properties_notebook = ttk.Notebook(self.right_paned)
self.right_paned.add(self.properties_notebook, minsize=200)

self.properties_view = create_properties_view(
    self.properties_notebook, 
    self.event_bus
)
self.properties_notebook.add(self.properties_view, text="Eigenschaften")

# Unteres Notebook: MiniMap  
self.minimap_notebook = ttk.Notebook(self.right_paned)
self.right_paned.add(self.minimap_notebook, minsize=150)

self.minimap_frame = tk.Frame(self.minimap_notebook, bg="#fafafa")
self.minimap_notebook.add(self.minimap_frame, text="Übersicht")
```

**Key Changes:**
1. `ttk.Notebook` → `tk.PanedWindow(orient=VERTICAL)`
2. Properties und MiniMap jeweils eigenes `ttk.Notebook`
3. Beide Notebooks im PanedWindow mit minsize

---

## 🎨 Finale UI-Struktur

```
┌─────────────────────────────────────────────────────────────────┐
│ Menu Bar                                                         │
├─────────────────────────────────────────────────────────────────┤
│ Toolbar                                                          │
├───────────┬─────────────────────────────┬───────────────────────┤
│           │                             │ ┌───────────────────┐ │
│ Palette   │  Canvas (Diagramm)          │ │  Eigenschaften    │ │
│           │  ┌─────────────────┐        │ │  ─────────────    │ │
│ ┌───────┐ │  │ Ruler X         │        │ │  Element-ID: F001 │ │
│ │ BPMN  │ │  ├──┬──────────────┤        │ │  Typ: FUNCTION    │ │
│ │────── │ │  │R │              │        │ │  Name: Antrag...  │ │
│ │Events │ │  │u │  ░░░░░░░░░░░ │        │ │  ...              │ │
│ │Gates  │ │  │l │  ░░█░░█░░█░░ │        │ └───────────────────┘ │
│ │Data   │ │  │e │  ░░░░░░░░░░░ │        ├═══════════════════════┤ ← Sash
│ │...    │ │  │r │              │        │ ┌───────────────────┐ │
│ └───────┘ │  │Y │              │        │ │   Übersicht       │ │
│           │  │  │              │        │ │   ─────────────   │ │
│           │  └──┴──────────────┤        │ │  ┌─────────────┐ │ │
│           │  Scrollbars         │        │ │  │ ░░░█░░░░░░ │ │ │
│           │                     │        │ │  │ ░░░░░█░░░░ │ │ │
│           │                     │        │ │  │ ░░░░░░░█░░ │ │ │
│           │                     │        │ │  │ ░░░░░░░░░█ │ │ │
│           │                     │        │ │  │ ▓▓▓▓      │ │ │ ← Viewport
│           │                     │        │ │  │    ▓▓▓▓   │ │ │
│           │                     │        │ │  └─────────────┘ │ │
│           │                     │        │ └───────────────────┘ │
├───────────┴─────────────────────────────┴───────────────────────┤
│ AI Chat Terminal                                                │
├─────────────────────────────────────────────────────────────────┤
│ Status Bar                                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ Features

### Gleichzeitige Ansicht
- ✅ Properties oben: Element-Details bearbeiten
- ✅ MiniMap unten: Position im Diagramm sehen
- ✅ Kein Tab-Wechsel mehr nötig

### Größe anpassen
- ✅ Sash zwischen Properties und MiniMap verschiebbar
- ✅ Mehr Platz für Properties: Details besser lesbar
- ✅ Mehr Platz für MiniMap: Bessere Übersicht

### Optionale Erweiterungen
- 🔄 Weitere Tabs zu Properties-Notebook hinzufügen (z.B. "Validierung")
- 🔄 Weitere Tabs zu MiniMap-Notebook hinzufügen (z.B. "Hierarchie")
- 🔄 Properties/MiniMap zusammenklappbar machen

---

## 📁 Geänderte Dateien

**vpb_app.py** (~15 Zeilen geändert)
```python
# Vorher:
self.right_notebook = ttk.Notebook(...)
  Tab 1: Properties
  Tab 2: MiniMap

# Nachher:
self.right_paned = tk.PanedWindow(orient=VERTICAL, ...)
  self.properties_notebook = ttk.Notebook(...)
    Tab: Properties
  self.minimap_notebook = ttk.Notebook(...)
    Tab: MiniMap
```

---

## 🧪 Testing

```bash
python vpb_app.py --load test_process.vpb.json
```

**Ergebnis:**
- ✅ App startet ohne Fehler
- ✅ Properties Notebook oben mit Tab "Eigenschaften"
- ✅ MiniMap Notebook unten mit Tab "Übersicht"
- ✅ Sash zwischen beiden verschiebbar
- ✅ Properties zeigt Element-Daten beim Klick
- ✅ MiniMap zeigt Diagramm-Übersicht
- ✅ Beide gleichzeitig sichtbar!

---

## 💡 Anwendungsfälle

### Use Case 1: Element bearbeiten + Position sehen
1. Element im Canvas auswählen
2. Properties oben: Name ändern
3. MiniMap unten: Sehen wo Element im Gesamtdiagramm liegt
4. Alles ohne Tab-Wechsel!

### Use Case 2: Navigation mit Kontext
1. MiniMap: Viewport-Rechteck zeigt aktuelle Ansicht
2. Properties: Zeigt Details des selektierten Elements
3. Click-and-Drag in MiniMap: Canvas-Position ändern
4. Properties bleibt sichtbar!

### Use Case 3: Größe anpassen
1. Viele Properties zu bearbeiten? → Sash nach unten ziehen → MiniMap kleiner
2. Große Übersicht gewünscht? → Sash nach oben ziehen → MiniMap größer
3. Flexibel je nach Aufgabe!

---

**Status:** ✅ Fertig und funktioniert perfekt!  
**Implementiert:** 14. Oktober 2025  
**Beide Notebooks gleichzeitig sichtbar und individuell anpassbar!** 🎉
