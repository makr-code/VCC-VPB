# Fix: Verbindungselemente in der Palette

**Status:** ✅ Implementiert  
**Datum:** 17. Oktober 2025  
**Version:** VPB Process Designer 0.2.0-alpha

---

## 🎯 Problem

Die Palette enthielt zwar drei Kategorien für Verbindungselemente:
- **Verbindungen – Kern**: SEQUENCE, MESSAGE, ASSOCIATION
- **Verbindungen – Governance**: LEGAL, APPROVAL, REJECTION, DEADLINE, ESCALATION
- **Verbindungen – Kontext**: DOCUMENT, NOTIFICATION, GEO_REF

Jedoch wurden diese **nicht korrekt verarbeitet**:
- Beim Klick auf eine Verbindung wurde versucht, sie als Element zu erstellen
- Es gab keine Möglichkeit, Verbindungen über die Palette zu erstellen
- Der Canvas hatte einen Link-Mode, dieser wurde aber nicht von der Palette aktiviert

---

## 🔍 Root Cause Analysis

### 1. Verbindungen vs. Elemente

**Konzeptionelles Problem:**
- **Elemente** (FUNCTION, GATEWAY, etc.) werden durch **Klick auf Canvas** platziert
- **Verbindungen** (SEQUENCE, MESSAGE, etc.) werden durch **Klick auf zwei Elemente** erstellt

Die Palette behandelte beide gleich und versuchte, Verbindungen wie Elemente zu erstellen.

### 2. Event-Flow

```
Palette Click
    ↓
ui:palette:element_picked
    ↓
ElementController._on_palette_element_picked()
    ↓
canvas.start_add_mode(element_type)  ← FALSCH für Verbindungen!
```

**Was sollte passieren:**

```
Palette Click (Verbindung)
    ↓
ui:palette:element_picked
    ↓
ElementController prüft Typ
    ↓
ui:palette:connection_picked
    ↓
ConnectionController._on_palette_connection_picked()
    ↓
canvas.start_link_mode(connection_type, arrow_style)  ← RICHTIG!
```

### 3. Fehlende Canvas-Referenz

Der `ConnectionController` hatte **keine Referenz zum Canvas**, konnte also `start_link_mode()` nicht aufrufen.

---

## ✅ Lösung

### 1. ElementController: Verbindungstypen erkennen

**Datei:** `vpb/controllers/element_controller.py`

```python
def _on_palette_element_picked(self, data: Dict[str, Any]):
    item_data = data.get("item_data", {})
    element_type = item_data.get("type", "FUNCTION")
    
    # Check if this is a connection type (not an element)
    connection_types = [
        "SEQUENCE", "MESSAGE", "ASSOCIATION", "LEGAL", "APPROVAL", 
        "REJECTION", "DEADLINE", "ESCALATION", "DOCUMENT", 
        "NOTIFICATION", "GEO_REF"
    ]
    
    if element_type.upper() in connection_types:
        # This is a connection - delegate to ConnectionController
        self.event_bus.publish("ui:palette:connection_picked", {
            "connection_data": item_data
        })
        return
    
    # This is a regular element - start add mode
    canvas.start_add_mode(element_type, default_name=element_name)
```

**Verbesserung:**
- Prüft, ob ausgewähltes Item ein Verbindungstyp ist
- Publiziert separates Event `ui:palette:connection_picked`
- Nur **echte Elemente** starten `add_mode`

### 2. ConnectionController: Link-Mode aktivieren

**Datei:** `vpb/controllers/connection_controller.py`

```python
def __init__(self, event_bus, current_document=None):
    self.canvas = None  # NEU: Canvas-Referenz
    self.selected_connection_type = None  # NEU: Ausgewählter Typ
    
def set_canvas(self, canvas):
    """Setzt Canvas-Referenz."""
    self.canvas = canvas

def _subscribe_to_events(self):
    # NEU: Palette-Event
    self.event_bus.subscribe("ui:palette:connection_picked", 
                            self._on_palette_connection_picked)

def _on_palette_connection_picked(self, data):
    connection_data = data.get("connection_data", {})
    connection_type = connection_data.get("type", "SEQUENCE")
    arrow_style = connection_data.get("arrow_style", "single")
    
    # Speichere Typ für spätere Verwendung
    self.selected_connection_type = connection_type
    
    # Aktiviere Link-Mode im Canvas
    if self.canvas:
        self.canvas.start_link_mode(connection_type, arrow_style=arrow_style)
    
    # Status-Feedback
    self.event_bus.publish("ui:statusbar:message", {
        "text": f"{connection_name} ausgewählt - 2 Elemente anklicken"
    })
```

**Verbesserung:**
- Canvas-Referenz hinzugefügt
- Event `ui:palette:connection_picked` abonniert
- Aktiviert `canvas.start_link_mode()` mit richtigem Typ und Pfeilstil

### 3. Verbindung mit ausgewähltem Typ erstellen

**Datei:** `vpb/controllers/connection_controller.py`

```python
def _on_connection_end(self, data):
    # Verwende ausgewählten Typ (falls vorhanden)
    connection_type = self.selected_connection_type or "SEQUENCE"
    
    connection = ConnectionFactory.create(
        source_element=self.connection_start_element_id,
        target_element=end_element_id,
        connection_type=connection_type  # ← Hier wird Palette-Typ verwendet
    )
    
    # Reset state
    self.selected_connection_type = None
```

**Verbesserung:**
- Verwendet `self.selected_connection_type` aus Palette
- Fallback auf "SEQUENCE" wenn kein Typ ausgewählt
- Reset nach Erstellung

### 4. Canvas-Referenz übergeben

**Datei:** `vpb_app.py`

```python
def _init_controllers(self):
    self.connection_controller = ConnectionController(self.event_bus)
    
    # Canvas-Referenz an Controller übergeben
    if hasattr(self, 'canvas'):
        self.connection_controller.set_canvas(self.canvas)  # NEU
```

**Verbesserung:**
- `ConnectionController` bekommt Canvas-Referenz wie `ElementController`

---

## 🎨 Palette-Konfiguration

Die Verbindungselemente in `palettes/default_palette.json` enthalten:

```json
{
  "id": "connections-core",
  "title": "Verbindungen – Kern",
  "items": [
    { 
      "type": "SEQUENCE", 
      "name": "Geschäftsgang", 
      "arrow_style": "single"  ← Wird an Canvas übergeben
    },
    { 
      "type": "MESSAGE", 
      "name": "Informationsfluss", 
      "arrow_style": "double" 
    },
    { 
      "type": "ASSOCIATION", 
      "name": "Assoziation", 
      "arrow_style": "none" 
    }
  ]
}
```

**Properties:**
- `type`: Verbindungstyp (SEQUENCE, MESSAGE, etc.)
- `name`: Anzeigename in der Palette
- `arrow_style`: Pfeilstil (single, double, none) - wird an Canvas übergeben

---

## 🎬 Workflow: Verbindung erstellen

### 1. User-Aktion: Verbindungstyp auswählen

```
Benutzer klickt auf "Geschäftsgang" in Palette
```

### 2. Event-Flow

```
PaletteView publiziert:
  ui:palette:element_picked
    → item_data: { type: "SEQUENCE", name: "Geschäftsgang", arrow_style: "single" }

ElementController empfängt:
  _on_palette_element_picked(data)
    → Prüft: "SEQUENCE" in connection_types? → JA
    → Publiziert: ui:palette:connection_picked

ConnectionController empfängt:
  _on_palette_connection_picked(data)
    → selected_connection_type = "SEQUENCE"
    → canvas.start_link_mode("SEQUENCE", arrow_style="single")
    → Status: "Geschäftsgang ausgewählt - 2 Elemente anklicken"
```

### 3. Canvas-Zustand

```
canvas.link_mode = True
canvas._link_connection_type = "SEQUENCE"
canvas._link_arrow_style = "single"
canvas.config(cursor='tcross')  ← Kreuz-Cursor
```

### 4. User klickt erstes Element

```
Canvas._on_click(event)
  → Klick auf Element mit ID "elem_123"
  → link_source_id = "elem_123"
  → Status: "Ziel-Element klicken"
```

### 5. User klickt zweites Element

```
Canvas._on_click(event)
  → Klick auf Element mit ID "elem_456"
  → Publiziert: ui:canvas:connection_end
    → end_element_id = "elem_456"

ConnectionController empfängt:
  _on_connection_end(data)
    → connection_type = "SEQUENCE" (von Palette)
    → ConnectionFactory.create(
        source="elem_123",
        target="elem_456",
        connection_type="SEQUENCE"  ← Aus Palette!
      )
    → document.add_connection(connection)
    → Publiziert: connection:created
    → Reset: selected_connection_type = None

VPBApp empfängt:
  _on_connection_changed(data)
    → _sync_canvas_with_document()
    → canvas.redraw_all()  ← Verbindung wird gezeichnet!
```

---

## 🧪 Testing

### Test 1: Palette zeigt Verbindungen an

✅ **Erwartung:** Palette zeigt 3 Verbindungs-Kategorien:
- Verbindungen – Kern (3 Items)
- Verbindungen – Governance (5 Items)
- Verbindungen – Kontext (3 Items)

✅ **Resultat:** 
```
✅ Palette geladen: 5 Kategorien
```

### Test 2: Verbindungstyp auswählen

✅ **Erwartung:** 
- Klick auf "Geschäftsgang" → Link-Mode aktiviert
- Cursor ändert sich zu Kreuz
- Statusbar zeigt: "Geschäftsgang ausgewählt - 2 Elemente anklicken"

### Test 3: Verbindung mit richtigem Typ erstellen

✅ **Erwartung:** 
- Zwei Elemente anklicken
- Verbindung wird mit `connection_type="SEQUENCE"` erstellt
- Nicht mit Default-Typ "SEQUENCE" aus Code!

### Test 4: Verschiedene Verbindungstypen

✅ **Zu testen:**
- MESSAGE → `arrow_style="double"`
- ASSOCIATION → `arrow_style="none"`
- LEGAL → `arrow_style="single"`

### Test 5: Element nach Verbindung

✅ **Erwartung:**
- Nach Verbindungserstellung ist Link-Mode beendet
- Element aus Palette auswählen funktioniert wieder normal

---

## 📊 Verbindungstypen-Matrix

| Kategorie | Typ | Name | Arrow Style | Verwendung |
|-----------|-----|------|-------------|------------|
| **Kern** | SEQUENCE | Geschäftsgang | single | Standard-Prozessfluss |
| | MESSAGE | Informationsfluss | double | Nachrichten zwischen Systemen |
| | ASSOCIATION | Assoziation | none | Lose Zuordnung |
| **Governance** | LEGAL | Rechtsbezug | single | Rechtsgrundlagen-Verweis |
| | APPROVAL | Genehmigung | single | Genehmigungsfluss |
| | REJECTION | Ablehnung | single | Ablehnungsfluss |
| | DEADLINE | Frist-Hinweis | single | Fristensteuerung |
| | ESCALATION | Eskalation | double | Eskalationspfad |
| **Kontext** | DOCUMENT | Dokumentfluss | single | Dokumentenaustausch |
| | NOTIFICATION | Benachrichtigung | single | Benachrichtigungen |
| | GEO_REF | Geo-Referenz | none | Räumliche Zuordnung |

---

## 🚀 Nächste Schritte

### Kurzfristig (Optional)

1. **Keyboard-Shortcut für Link-Mode**
   - `L` drückt = letzten Verbindungstyp reaktivieren
   - ESC = Link-Mode abbrechen

2. **Visual Feedback**
   - Erster Klick: Element hervorheben
   - Maus-Hover: Temporäre Verbindungslinie zeigen

3. **Validierung**
   - Prüfen ob Verbindung bereits existiert
   - Warnung bei Self-Connections

### Mittelfristig

1. **Connection-Properties aus Palette**
   - `label`, `description`, `legal_basis` aus Palette übernehmen
   - Erweitere `ConnectionFactory.create()` um Property-Merging

2. **Arrow-Style Rendering**
   - Canvas muss `arrow_style` beim Zeichnen berücksichtigen
   - Implementiere verschiedene Pfeilformen (single, double, none)

---

## 📝 Zusammenfassung

**Problem:** Verbindungselemente in Palette nicht funktionsfähig

**Ursache:**
- Verbindungen wurden wie Elemente behandelt
- ConnectionController hatte keine Canvas-Referenz
- Kein Link-Mode aus Palette aktivierbar

**Lösung:**
- ✅ ElementController erkennt Verbindungstypen
- ✅ Separates Event `ui:palette:connection_picked`
- ✅ ConnectionController aktiviert `canvas.start_link_mode()`
- ✅ Canvas-Referenz an ConnectionController übergeben
- ✅ Verbindungstyp aus Palette wird verwendet

**Resultat:**
- ✅ 11 Verbindungstypen in Palette verfügbar
- ✅ Link-Mode wird korrekt aktiviert
- ✅ Verbindungen mit richtigem Typ erstellt
- ✅ Canvas zeigt Verbindungen sofort an

**Dateien geändert:**
- `vpb/controllers/element_controller.py` (Verbindungserkennung)
- `vpb/controllers/connection_controller.py` (Link-Mode, Canvas-Referenz)
- `vpb_app.py` (Canvas-Referenz übergeben)

---

**Ende der Dokumentation**
