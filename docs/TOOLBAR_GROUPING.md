# Toolbar: Gruppierungs- und Zeitschleifen-Buttons

**Datum:** 18. Oktober 2025  
**Feature:** Toolbar-Integration für Gruppierung und Zeitschleifen

---

## 🎯 Übersicht

Die Toolbar wurde um **3 neue Buttons** erweitert, die schnellen Zugriff auf Gruppierungs- und Zeitschleifen-Funktionen bieten.

---

## 🔘 Neue Buttons

### 1. ⬜ Gruppe bilden

**Funktion:** Erstellt einen GROUP-Container aus der aktuellen Auswahl

**Workflow:**
1. Mehrere Elemente im Canvas auswählen (Strg+Click oder Rechteck-Auswahl)
2. Button "⬜ Gruppe bilden" in der Toolbar klicken
3. GROUP-Container erscheint mit grauem, gestricheltem Rahmen [6,4]

**Tastenkombination:** Alternativ über Menü: Bearbeiten → "Gruppe aus Auswahl bilden"

**Symbol:** ⬜ (leeres Quadrat) - repräsentiert Container

---

### 2. ⟳ Zeitschleife bilden

**Funktion:** Erstellt einen TIME_LOOP-Container aus der aktuellen Auswahl

**Workflow:**
1. Mehrere Elemente im Canvas auswählen
2. Button "⟳ Zeitschleife bilden" in der Toolbar klicken
3. TIME_LOOP-Container erscheint mit orangem, gestricheltem Rahmen [8,4]
4. Standard-Zeiteinstellung: Intervall, 60 Minuten

**Tastenkombination:** Alternativ über Menü: Bearbeiten → "Zeitschleife aus Auswahl bilden"

**Symbol:** ⟳ (Kreispfeil) - repräsentiert Wiederholung/Schleife

**Zeit-Properties (nach Erstellung im Properties-Panel konfigurierbar):**
- **loop_type:** interval, cron, date, relative
- **loop_interval_minutes:** Minuten zwischen Wiederholungen
- **loop_cron:** Cron-Expression (z.B. "0 9 * * *")
- **loop_date:** Festes Datum (ISO-Format)
- **loop_relative_days:** Tage relativ zu Prozessstart
- **loop_max_iterations:** Max. Wiederholungen (0 = unbegrenzt)

---

### 3. ◻ Gruppe auflösen

**Funktion:** Löst einen ausgewählten GROUP- oder TIME_LOOP-Container auf

**Workflow:**
1. GROUP oder TIME_LOOP-Container im Canvas auswählen
2. Button "◻ Gruppe auflösen" in der Toolbar klicken
3. Container wird gelöscht, Mitglieder bleiben erhalten
4. Verbindungen zum/vom Container werden entfernt

**Tastenkombination:** Alternativ über Menü: Bearbeiten → "Gruppe auflösen"

**Symbol:** ◻ (leeres Quadrat mit Linie) - repräsentiert Auflösung

**Wichtig:** 
- Funktioniert für GROUP **und** TIME_LOOP
- Mitglieder-Elemente werden **nicht** gelöscht
- Nur der Container und seine Verbindungen werden entfernt

---

## 📐 Toolbar-Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│ VPB | Neu | Öffnen | Speichern | ║ Element + | Neu zeichnen | Auto-Layout │
│ ║ ⬜ Gruppe | ⟳ Zeitschleife | ◻ Auflösen ║ Ausrichten ▼ | Verteilen ▼ │
└─────────────────────────────────────────────────────────────────────────┘
```

**Reihenfolge:**
1. **VPB-Logo** + Datei-Buttons (Neu, Öffnen, Speichern)
2. **Separator** (║)
3. **Edit-Buttons** (Element hinzufügen, Neu zeichnen, Auto-Layout)
4. **Separator** (║)
5. **Gruppierungs-Buttons** (⬜ Gruppe, ⟳ Zeitschleife, ◻ Auflösen) ← **NEU**
6. **Separator** (║)
7. **Anordnen-Menüs** (Ausrichten, Verteilen, Formationen)

---

## 💡 Verwendungsbeispiele

### Beispiel 1: Einfache Gruppe

**Szenario:** Verwaltungsaufgaben zusammenfassen

1. Elemente auswählen:
   - "Antrag prüfen"
   - "Dokumente anfordern"
   - "Bescheid erstellen"

2. Button "⬜ Gruppe bilden" klicken

3. **Ergebnis:** GROUP-Container umschließt alle 3 Elemente
   - Grauer gestrichelter Rahmen
   - Name: "Gruppe" (umbenennen im Properties-Panel)
   - Kann zugeklappt werden (collapsed)

### Beispiel 2: Zeitgesteuerte Wiederholung

**Szenario:** Tägliche Datensynchronisation

1. Elemente auswählen:
   - "Daten abholen (API)"
   - "Daten validieren"
   - "Daten speichern (DB)"

2. Button "⟳ Zeitschleife bilden" klicken

3. **Ergebnis:** TIME_LOOP-Container mit Standard-Intervall
   - Oranger gestrichelter Rahmen
   - Standard: Intervall, 60 Minuten

4. **Konfiguration im Properties-Panel:**
   - loop_type → "interval" ändern zu "cron"
   - loop_cron → "0 2 * * *" (täglich um 2:00 Uhr)
   - Name → "Tägliche Synchronisation"

### Beispiel 3: Gruppe auflösen

**Szenario:** Testgruppe wieder entfernen

1. GROUP-Container "Test-Gruppe" auswählen

2. Button "◻ Gruppe auflösen" klicken

3. **Ergebnis:**
   - Container wird gelöscht
   - Mitglieder bleiben sichtbar
   - Verbindungen zur Gruppe werden entfernt

---

## 🔧 Technische Details

### Event-Publishing

```python
# Gruppe bilden
self._publish_action("edit.group")
→ Event: "ui:action:edit.group"
→ Handler: _handle_group_from_selection()
→ Canvas: canvas._group_from_selection()

# Zeitschleife bilden
self._publish_action("edit.time_loop")
→ Event: "ui:action:edit.time_loop"
→ Handler: _handle_time_loop_from_selection()
→ Canvas: canvas._time_loop_from_selection()

# Gruppe auflösen
self._publish_action("edit.ungroup")
→ Event: "ui:action:edit.ungroup"
→ Handler: _handle_ungroup_selected()
→ Canvas: canvas._ungroup_selected()
```

### Canvas-Methoden

#### `canvas._group_from_selection()`
```python
def _group_from_selection(self):
    sels = [eid for eid in self.selected_ids if eid in self.elements]
    if len(sels) < 1:
        messagebox.showinfo("Gruppe", "Bitte wählen Sie mindestens ein Element aus.")
        return
    
    self.push_undo()
    
    # Schwerpunkt berechnen
    xs = [self.elements[e].x for e in sels]
    ys = [self.elements[e].y for e in sels]
    cx = int(sum(xs) / len(xs))
    cy = int(sum(ys) / len(ys))
    
    # GROUP erstellen
    g = self.add_element("GROUP", name="Gruppe", at=(cx, cy))
    g.members = list(sels)
    g.collapsed = False
    
    self.selected_ids = {g.element_id}
    self.selected_id = g.element_id
    self.redraw_all()
```

#### `canvas._time_loop_from_selection()`
```python
def _time_loop_from_selection(self):
    sels = [eid for eid in self.selected_ids if eid in self.elements]
    if len(sels) < 1:
        messagebox.showinfo("Zeitschleife", "Bitte wählen Sie mindestens ein Element aus.")
        return
    
    self.push_undo()
    
    # Schwerpunkt berechnen
    xs = [self.elements[e].x for e in sels]
    ys = [self.elements[e].y for e in sels]
    cx = int(sum(xs) / len(xs))
    cy = int(sum(ys) / len(ys))
    
    # TIME_LOOP erstellen mit Default-Zeitsteuerung
    tl = self.add_element("TIME_LOOP", name="Zeitschleife", at=(cx, cy))
    tl.members = list(sels)
    tl.collapsed = False
    tl.loop_type = "interval"
    tl.loop_interval_minutes = 60
    
    self.selected_ids = {tl.element_id}
    self.selected_id = tl.element_id
    self.redraw_all()
```

---

## 🎨 Visuelle Unterscheidung

### GROUP vs TIME_LOOP

| Eigenschaft | GROUP | TIME_LOOP |
|-------------|-------|-----------|
| **Farbe** | Grau (#666666) | Orange (#FF8C00) |
| **Hintergrund** | Transparent | Hell-Orange (#FFF4E6) |
| **Rahmen-Stil** | Gestrichelt [6,4] | Gestrichelt [8,4] (länger) |
| **Button-Symbol** | ⬜ | ⟳ |
| **Zweck** | Logische Gruppierung | Zeitgesteuerte Wiederholung |
| **Zeit-Properties** | ❌ Keine | ✅ 6 Properties |

---

## ⌨️ Shortcuts & Alternativen

### Toolbar vs Menü vs Tastatur

| Aktion | Toolbar | Menü | Tastatur |
|--------|---------|------|----------|
| Gruppe bilden | Button "⬜ Gruppe bilden" | Bearbeiten → Gruppe aus Auswahl bilden | - |
| Zeitschleife bilden | Button "⟳ Zeitschleife bilden" | Bearbeiten → Zeitschleife aus Auswahl bilden | - |
| Gruppe auflösen | Button "◻ Gruppe auflösen" | Bearbeiten → Gruppe auflösen | - |

**Hinweis:** Tastenkombinationen können in zukünftigen Versionen hinzugefügt werden (z.B. Strg+G für Gruppe)

---

## 📝 Datei-Änderungen

### `vpb/views/toolbar.py`

**Änderungen:**
- ✅ `_create_edit_buttons()` erweitert
- ✅ 3 neue Buttons hinzugefügt:
  - "⬜ Gruppe bilden" → Action: "edit.group"
  - "⟳ Zeitschleife bilden" → Action: "edit.time_loop"
  - "◻ Gruppe auflösen" → Action: "edit.ungroup"
- ✅ Separator vor Gruppierungs-Buttons
- ✅ Event-Publishing via `_publish_action()`

**Code:**
```python
def _create_edit_buttons(self) -> None:
    """Erstellt Edit-Buttons (Element hinzufügen, Neu zeichnen, Auto-Layout)."""
    edit_buttons = [
        ("Element hinzufügen", "edit.add_element", 8),
        ("Neu zeichnen", "edit.redraw", 8),
        ("Auto-Layout", "edit.auto_layout", 4),
    ]
    
    for text, action, padx in edit_buttons:
        btn = tk.Button(
            self.toolbar, 
            text=text, 
            command=lambda a=action: self._publish_action(a)
        )
        btn.pack(side=tk.LEFT, padx=padx, pady=4)
    
    # Separator
    self._add_separator()
    
    # Gruppierungs-Buttons (NEU)
    group_buttons = [
        ("⬜ Gruppe bilden", "edit.group", 4),
        ("⟳ Zeitschleife bilden", "edit.time_loop", 4),
        ("◻ Gruppe auflösen", "edit.ungroup", 8),
    ]
    
    for text, action, padx in group_buttons:
        btn = tk.Button(
            self.toolbar, 
            text=text, 
            command=lambda a=action: self._publish_action(a)
        )
        btn.pack(side=tk.LEFT, padx=padx, pady=4)
```

### Event-Bridge in `vpb_app.py`

**Bereits vorhanden** (keine Änderungen nötig):
```python
# Event-Bridge: ui:action:* → Handler
self.event_bus.subscribe("ui:action:edit.group", 
    lambda d: self._handle_group_from_selection(d))
self.event_bus.subscribe("ui:action:edit.time_loop", 
    lambda d: self._handle_time_loop_from_selection(d))
self.event_bus.subscribe("ui:action:edit.ungroup", 
    lambda d: self._handle_ungroup_selected(d))
```

---

## 🧪 Testing

### Test 1: Gruppe bilden Button

✅ **Workflow:**
1. App starten
2. 3 Elemente aus Palette ziehen (z.B. START_EVENT, FUNCTION, END_EVENT)
3. Alle 3 Elemente auswählen (Strg+Click)
4. Button "⬜ Gruppe bilden" klicken

✅ **Erwartung:**
- Grauer gestrichelter Rahmen erscheint
- Alle 3 Elemente sind im GROUP-Container
- Properties-Panel zeigt "Gruppe"-Section mit Members-Liste

### Test 2: Zeitschleife bilden Button

✅ **Workflow:**
1. 2-3 FUNCTION-Elemente auswählen
2. Button "⟳ Zeitschleife bilden" klicken

✅ **Erwartung:**
- Oranger gestrichelter Rahmen erscheint
- Properties-Panel zeigt Zeit-Properties
- Standard: loop_type="interval", loop_interval_minutes=60

### Test 3: Gruppe auflösen Button

✅ **Workflow:**
1. GROUP-Container auswählen
2. Button "◻ Gruppe auflösen" klicken

✅ **Erwartung:**
- Container verschwindet
- Mitglieder bleiben sichtbar
- Keine Verbindungen mehr zum Container

### Test 4: Fehlerfall - keine Auswahl

✅ **Workflow:**
1. Keine Elemente auswählen
2. Button "⬜ Gruppe bilden" klicken

✅ **Erwartung:**
- MessageBox: "Bitte wählen Sie mindestens ein Element aus."

---

## ✅ Status

**Implementiert:**
- ✅ 3 neue Toolbar-Buttons
- ✅ Event-Publishing (ui:action:edit.*)
- ✅ Event-Bridge in vpb_app.py
- ✅ Canvas-Methoden (_group_from_selection, _time_loop_from_selection)
- ✅ Visuelle Symbole (⬜, ⟳, ◻)
- ✅ Separator zwischen Button-Gruppen
- ✅ App getestet (Exit Code: 0)

**Vorteile:**
- ✅ Schneller Zugriff ohne Menü-Navigation
- ✅ Intuitive Symbole (⬜ für Container, ⟳ für Wiederholung)
- ✅ Konsistent mit bestehendem Toolbar-Design
- ✅ Parallele Verfügbarkeit über Menü

---

**Ende der Dokumentation**
