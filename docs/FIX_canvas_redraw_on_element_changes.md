# Fix: Canvas Redraw bei Element/Verbindungs-Änderungen

**Problem:** Wenn Elemente aus der Palette eingefügt oder Eigenschaften im Properties Panel geändert werden, wird die Canvas-Darstellung nicht aktualisiert.

**Ursache:** Das Canvas hat eine **eigene interne Kopie** der Elemente (`self.elements`) und Verbindungen (`self.connections`), die nicht automatisch mit dem DocumentModel synchronisiert wird.

**Datum:** 17. Oktober 2025  
**Status:** ✅ Behoben

---

## Problem-Analyse

### Architektur

```
┌─────────────────┐
│ ElementController│
│                 │
│ Publiziert:     │
│ - element:created
│ - element:modified
│ - element:deleted
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  DocumentModel  │
│                 │
│ elements: []    │
│ connections: [] │
└─────────────────┘

         ❌ NICHT SYNCHRONISIERT

┌─────────────────┐
│    VPBCanvas    │
│                 │
│ self.elements   │ ← Eigene Kopie!
│ self.connections│ ← Eigene Kopie!
└─────────────────┘
```

### Symptome

1. **Element aus Palette einfügen:**
   - ✅ Element wird im DocumentModel erstellt
   - ❌ Canvas zeigt Element NICHT an
   - ❌ `canvas.elements` enthält das neue Element nicht

2. **Properties ändern:**
   - ✅ Element-Properties werden im DocumentModel aktualisiert
   - ❌ Canvas zeigt alte Darstellung
   - ❌ `canvas.elements[id]` zeigt auf alte Instanz

3. **Element löschen:**
   - ✅ Element wird aus DocumentModel entfernt
   - ❌ Canvas zeigt Element weiterhin
   - ❌ `canvas.elements[id]` existiert noch

---

## Lösung

### 1. Event-Subscriptions hinzufügen

**Datei:** `vpb_app.py`

```python
def _subscribe_to_events(self):
    # ... bestehende Subscriptions ...
    
    # Element/Connection Events (Canvas Redraw)
    self.event_bus.subscribe("element:created", self._on_element_changed)
    self.event_bus.subscribe("element:modified", self._on_element_changed)
    self.event_bus.subscribe("element:deleted", self._on_element_changed)
    self.event_bus.subscribe("connection:created", self._on_connection_changed)
    self.event_bus.subscribe("connection:modified", self._on_connection_changed)
    self.event_bus.subscribe("connection:deleted", self._on_connection_changed)
```

### 2. Synchronisierungs-Methode implementieren

```python
def _sync_canvas_with_document(self):
    """Synchronisiert Canvas-Elemente mit dem aktuellen Dokument."""
    try:
        if not hasattr(self, 'canvas') or not hasattr(self, 'document_controller'):
            return
        
        document = self.document_controller.get_current_document()
        if not document:
            return
        
        # Aktualisiere Canvas-Elemente aus Dokument
        self.canvas.elements.clear()
        for element in document.elements:
            self.canvas.elements[element.element_id] = element
        
        # Aktualisiere Canvas-Verbindungen aus Dokument
        self.canvas.connections.clear()
        for connection in document.connections:
            self.canvas.connections[connection.connection_id] = connection
        
        # Jetzt neu zeichnen
        self.canvas.redraw_all()
        
    except Exception as e:
        print(f"⚠️ Fehler beim Sync von Canvas mit Dokument: {e}")
```

### 3. Event-Handler implementieren

```python
def _on_element_changed(self, data):
    """Synchronisiert Canvas mit Dokument, wenn Element erstellt/geändert/gelöscht wird."""
    try:
        if hasattr(self, 'canvas') and hasattr(self, 'document_controller'):
            self._sync_canvas_with_document()
    except Exception as e:
        print(f"⚠️ Fehler beim Canvas-Sync nach Element-Änderung: {e}")

def _on_connection_changed(self, data):
    """Synchronisiert Canvas mit Dokument, wenn Verbindung erstellt/geändert/gelöscht wird."""
    try:
        if hasattr(self, 'canvas') and hasattr(self, 'document_controller'):
            self._sync_canvas_with_document()
    except Exception as e:
        print(f"⚠️ Fehler beim Canvas-Sync nach Verbindungs-Änderung: {e}")
```

---

## Workflow nach dem Fix

### Element einfügen

```
1. User klickt Element in Palette
   ↓
2. ElementController.create_element()
   ↓
3. document.add_element(element)
   ↓
4. event_bus.publish("element:created")
   ↓
5. VPBApplication._on_element_changed()
   ↓
6. _sync_canvas_with_document()
   - canvas.elements = document.elements
   - canvas.connections = document.connections
   ↓
7. canvas.redraw_all()
   ↓
8. ✅ Element wird angezeigt!
```

### Properties ändern

```
1. User ändert Properties im Panel
   ↓
2. PropertiesView publiziert "ui:properties:element_changed"
   ↓
3. ElementController._on_element_properties_changed()
   - element.name = new_value
   - element.description = new_value
   ↓
4. event_bus.publish("element:modified")
   ↓
5. VPBApplication._on_element_changed()
   ↓
6. _sync_canvas_with_document()
   ↓
7. canvas.redraw_all()
   ↓
8. ✅ Aktualisierte Darstellung!
```

---

## Betroffene Komponenten

### Controller
- ✅ `ElementController` - publiziert `element:*` Events
- ✅ `ConnectionController` - publiziert `connection:*` Events

### Views
- ✅ `PropertiesView` - publiziert `ui:properties:*_changed` Events
- ✅ `PaletteView` - publiziert `ui:palette:element_picked` Events

### Models
- ✅ `DocumentModel` - speichert aktuelle Elemente/Verbindungen
- ✅ `VPBElement` - Element-Daten
- ✅ `VPBConnection` - Verbindungs-Daten

### Canvas
- ✅ `VPBCanvas` - zeichnet Elemente/Verbindungen
  - `self.elements` - interne Kopie (wird jetzt synchronisiert)
  - `self.connections` - interne Kopie (wird jetzt synchronisiert)

---

## Vorteile der Lösung

✅ **Automatisch:** Canvas wird bei jeder Änderung aktualisiert  
✅ **Zentral:** Synchronisierung an einem Ort (`_sync_canvas_with_document`)  
✅ **Event-driven:** Nutzt bestehende Event-Architektur  
✅ **Robust:** Fehlerbehandlung bei Sync-Fehlern  
✅ **Skalierbar:** Funktioniert für alle Element/Connection-Operationen  

---

## Alternative Lösungen (nicht gewählt)

### 1. Canvas direkt mit DocumentModel arbeiten lassen
**Problem:** Würde große Refactorings im Canvas erfordern  
**Nachteil:** Canvas hat historisch gewachsene Logik mit eigenen Datenstrukturen

### 2. DocumentModel Observer-Pattern
**Problem:** Würde neues Architektur-Pattern einführen  
**Nachteil:** Kompliziert die bestehende Event-Bus-Architektur

### 3. Nur `redraw_all()` ohne Sync
**Problem:** Canvas würde veraltete Daten zeichnen  
**Nachteil:** `canvas.elements` wäre out-of-sync mit DocumentModel

---

## Testing

### Manuelle Tests

✅ **Element aus Palette einfügen**
- Element erscheint sofort auf Canvas
- Element hat korrekte Darstellung

✅ **Properties ändern**
- Name-Änderung wird sofort sichtbar
- Typ-Änderung ändert Symbol
- Beschreibung wird aktualisiert

✅ **Element löschen**
- Element verschwindet sofort
- Verbindungen werden entfernt

✅ **Verbindung erstellen**
- Verbindung erscheint sofort
- Routing wird korrekt berechnet

✅ **Verbindung löschen**
- Verbindung verschwindet sofort

---

## Performance-Überlegungen

### Aktuelle Implementierung
- Bei jedem Event: `_sync_canvas_with_document()` + `redraw_all()`
- Bei vielen Änderungen: Mehrfaches Redraw

### Mögliche Optimierungen (Zukunft)

1. **Debouncing:** Mehrere Änderungen innerhalb 100ms zusammenfassen
2. **Partial Updates:** Nur geänderte Elemente neu zeichnen
3. **Dirty Flags:** Tracking, was tatsächlich geändert wurde
4. **Batch Operations:** Mehrere Änderungen vor Redraw sammeln

**Aktuelle Entscheidung:** Erstmal einfache Lösung, Optimierung bei Bedarf

---

## Zusammenfassung

Das Problem wurde behoben durch:
1. ✅ Subscription auf `element:*` und `connection:*` Events
2. ✅ Synchronisierung von `canvas.elements` mit `document.elements`
3. ✅ Synchronisierung von `canvas.connections` mit `document.connections`
4. ✅ Automatisches Redraw nach Synchronisierung

Das Canvas zeigt jetzt **immer den aktuellen Dokumentzustand** an! 🎉

---

**Implementiert von:** GitHub Copilot  
**Datum:** 17. Oktober 2025  
**Status:** Produktionsreif ✅
