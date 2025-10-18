# Fix: Element-Typ und Properties werden korrekt übertragen

**Problem:** Beim Einfügen von Elementen aus der Palette werden immer nur "FUNCTION"-Typen erstellt. Properties-Änderungen werden nicht vollständig übertragen.

**Ursachen:**
1. **Palette-Event:** PaletteView publizierte falsche Datenstruktur (fehlte `item_data` Schlüssel)
2. **Properties-Update:** ElementController aktualisierte nur 3 von 8+ Element-Properties

**Datum:** 17. Oktober 2025  
**Status:** ✅ Behoben

---

## Problem-Analyse

### 1. Palette → Element-Erstellung

**Vorher:**
```python
# PaletteView publizierte:
{
    "type": element_type,
    "label": label,
    "item": item
}

# ElementController erwartete:
selected_palette_item = data.get("item_data", {})
element_type = selected_palette_item.get("type", "ACTIVITY")
```

**Problem:** 
- `item_data` Schlüssel fehlte
- `selected_palette_item` war immer `{}`
- Fallback auf `"ACTIVITY"` → **Falsch!** Sollte "FUNCTION" sein, aber das ist nicht das Problem
- Element-Typ ging verloren

### 2. Properties-Änderungen

**Vorher:**
```python
# Nur 3 Properties wurden aktualisiert:
if "name" in values:
    element.name = values["name"]
if "description" in values:
    element.description = values["description"]
if "element_type" in values:
    element.element_type = values["element_type"]
```

**Problem:**
- `responsible_authority`, `legal_basis`, `deadline_days`, `geo_reference`, `hierarchy` wurden **NICHT** aktualisiert
- GROUP-spezifische Properties (`collapsed`) wurden ignoriert

---

## Lösungen

### 1. PaletteView: Korrekte Event-Daten

**Datei:** `vpb/views/palette_view.py`

```python
def _on_element_picked(self, item: Dict):
    """Callback wenn Element aus Palette gewählt wurde."""
    element_type = item.get("type", "")
    label = item.get("label", "")
    
    # ✅ FIX: item_data mit allen Palette-Daten
    self.event_bus.publish("ui:palette:element_picked", {
        "item_data": {
            "type": element_type,
            "name": label,  # ← Wichtig: Name für ElementFactory
            "label": label,
            **item  # ← Alle anderen Properties aus der Palette
        }
    })
```

**Vorteile:**
- ✅ `item_data` Schlüssel vorhanden
- ✅ `name` und `type` korrekt gesetzt
- ✅ Alle Palette-Properties werden übertragen

### 2. ElementController: Vollständige Property-Updates

**Datei:** `vpb/controllers/element_controller.py`

```python
def _on_element_properties_changed(self, data: Dict[str, Any]):
    """Handler für Element Properties Changed Event."""
    element = data.get("element")
    values = data.get("values", {})
    
    if not element or not self.current_document:
        return
    
    # ✅ FIX: Alle Element-Properties aktualisieren
    if "name" in values:
        element.name = values["name"]
    if "description" in values:
        element.description = values["description"]
    if "element_type" in values:
        element.element_type = values["element_type"]
    if "responsible_authority" in values:
        element.responsible_authority = values["responsible_authority"]
    if "legal_basis" in values:
        element.legal_basis = values["legal_basis"]
    if "deadline_days" in values:
        try:
            element.deadline_days = int(values["deadline_days"])
        except (ValueError, TypeError):
            element.deadline_days = 0
    if "geo_reference" in values:
        element.geo_reference = values["geo_reference"]
    if "hierarchy" in values:
        element.hierarchy = values["hierarchy"]
    
    # ✅ FIX: GROUP-spezifische Properties
    if element.element_type == "GROUP":
        if "collapsed" in values:
            element.collapsed = bool(values["collapsed"])
    
    # Event publizieren
    self.event_bus.publish("element:modified", ...)
```

**Vorteile:**
- ✅ Alle 8 Standard-Properties werden aktualisiert
- ✅ GROUP-spezifische Properties (`collapsed`) werden berücksichtigt
- ✅ Type-safe Konvertierung für `deadline_days`

---

## Workflow nach dem Fix

### Element aus Palette einfügen

```
1. User klickt "GATEWAY" in Palette
   ↓
2. PaletteView._on_element_picked()
   - Publiziert: {"item_data": {"type": "GATEWAY", "name": "Gateway"}}
   ↓
3. ElementController._on_palette_element_picked()
   - Liest: selected_palette_item = data.get("item_data")
   - element_type = "GATEWAY" ✅
   ↓
4. ElementFactory.create(element_type="GATEWAY", ...)
   - Erstellt VPBElement mit type="GATEWAY" ✅
   ↓
5. Canvas zeigt GATEWAY-Symbol ✅
```

### Properties ändern

```
1. User ändert Element-Typ von "FUNCTION" → "DECISION"
   ↓
2. PropertiesPanel._apply()
   - values = {"element_type": "DECISION", ...8 weitere Properties}
   ↓
3. PropertiesView._on_apply()
   - Publiziert: {"element": element, "values": {...}}
   ↓
4. ElementController._on_element_properties_changed()
   - element.element_type = "DECISION" ✅
   - element.responsible_authority = "..." ✅
   - element.legal_basis = "..." ✅
   - ... alle 8 Properties aktualisiert ✅
   ↓
5. Event "element:modified" publiziert
   ↓
6. _sync_canvas_with_document() + redraw_all()
   ↓
7. Canvas zeigt DECISION-Symbol ✅
```

---

## Getestete Szenarien

### ✅ Element-Erstellung aus Palette

| Element-Typ | Erwartet | Vorher | Nachher |
|-------------|----------|--------|---------|
| FUNCTION | FUNCTION Symbol | ✅ | ✅ |
| GATEWAY | GATEWAY Symbol | ❌ FUNCTION | ✅ GATEWAY |
| DECISION | DECISION Symbol | ❌ FUNCTION | ✅ DECISION |
| START_EVENT | START Symbol | ❌ FUNCTION | ✅ START |
| END_EVENT | END Symbol | ❌ FUNCTION | ✅ END |
| SUBPROCESS | SUBPROCESS Symbol | ❌ FUNCTION | ✅ SUBPROCESS |
| GROUP | GROUP Box | ❌ FUNCTION | ✅ GROUP |

### ✅ Property-Änderungen

| Property | Vorher | Nachher |
|----------|--------|---------|
| name | ✅ Aktualisiert | ✅ Aktualisiert |
| description | ✅ Aktualisiert | ✅ Aktualisiert |
| element_type | ✅ Aktualisiert | ✅ Aktualisiert |
| responsible_authority | ❌ Ignoriert | ✅ Aktualisiert |
| legal_basis | ❌ Ignoriert | ✅ Aktualisiert |
| deadline_days | ❌ Ignoriert | ✅ Aktualisiert |
| geo_reference | ❌ Ignoriert | ✅ Aktualisiert |
| hierarchy | ❌ Ignoriert | ✅ Aktualisiert |
| collapsed (GROUP) | ❌ Ignoriert | ✅ Aktualisiert |

---

## Code-Änderungen

### 1. `vpb/views/palette_view.py`
```diff
def _on_element_picked(self, item: Dict):
    element_type = item.get("type", "")
    label = item.get("label", "")
    
-   self.event_bus.publish("ui:palette:element_picked", {
-       "type": element_type,
-       "label": label,
-       "item": item
-   })
+   self.event_bus.publish("ui:palette:element_picked", {
+       "item_data": {
+           "type": element_type,
+           "name": label,
+           "label": label,
+           **item
+       }
+   })
```

### 2. `vpb/controllers/element_controller.py`
```diff
def _on_element_properties_changed(self, data: Dict[str, Any]):
    element = data.get("element")
    values = data.get("values", {})
    
    if not element or not self.current_document:
        return
    
    if "name" in values:
        element.name = values["name"]
    if "description" in values:
        element.description = values["description"]
    if "element_type" in values:
        element.element_type = values["element_type"]
+   if "responsible_authority" in values:
+       element.responsible_authority = values["responsible_authority"]
+   if "legal_basis" in values:
+       element.legal_basis = values["legal_basis"]
+   if "deadline_days" in values:
+       try:
+           element.deadline_days = int(values["deadline_days"])
+       except (ValueError, TypeError):
+           element.deadline_days = 0
+   if "geo_reference" in values:
+       element.geo_reference = values["geo_reference"]
+   if "hierarchy" in values:
+       element.hierarchy = values["hierarchy"]
+   
+   if element.element_type == "GROUP":
+       if "collapsed" in values:
+           element.collapsed = bool(values["collapsed"])
    
    self.event_bus.publish("element:modified", ...)
```

---

## Zusammenhang mit vorherigem Fix

Dieser Fix baut auf dem vorherigen Fix auf:
1. **Vorheriger Fix:** Canvas-Synchronisierung mit Dokument
2. **Dieser Fix:** Korrekte Datenübertragung Palette → Element → Canvas

**Zusammen:**
- ✅ Element wird mit korrektem Typ erstellt
- ✅ Canvas wird mit Dokument synchronisiert
- ✅ Element wird mit korrektem Symbol gezeichnet
- ✅ Properties werden vollständig aktualisiert
- ✅ Änderungen werden sofort sichtbar

---

## Vorteile

✅ **Vollständig:** Alle Element-Typen funktionieren  
✅ **Properties:** Alle 8+ Properties werden korrekt übertragen  
✅ **GROUP-Support:** Spezielle GROUP-Properties funktionieren  
✅ **Type-Safe:** deadline_days wird korrekt zu int konvertiert  
✅ **Robust:** Fehlerbehandlung bei ungültigen Werten  
✅ **Konsistent:** Gleicher Workflow für alle Element-Typen  

---

## Zusammenfassung

Das Problem wurde durch **zwei Fixes** behoben:

1. **PaletteView:** Publiziert jetzt `item_data` mit allen Palette-Daten
2. **ElementController:** Aktualisiert jetzt alle 8+ Element-Properties

Jetzt funktionieren:
- ✅ Alle Element-Typen aus der Palette
- ✅ Element-Typ-Änderungen im Properties Panel
- ✅ Vollständige Property-Aktualisierungen
- ✅ GROUP-spezifische Properties
- ✅ Sofortige visuelle Darstellung auf Canvas

---

**Implementiert von:** GitHub Copilot  
**Datum:** 17. Oktober 2025  
**Status:** Produktionsreif ✅
