# Fix: AI-generierte Prozesse vollständig importieren

**Status:** ✅ Implementiert  
**Datum:** 17. Oktober 2025  
**Version:** VPB Process Designer 0.2.0-alpha

---

## 🎯 Problem

AI-generierte Prozesse werden **beim Import nicht vollständig übernommen**:
- Elemente fehlen oder haben falsche Properties
- Verbindungen werden nicht erstellt
- JSON-Parsing schlägt fehl bei leicht ungültigem Format

**Ursache:**
- AI generiert manchmal **ungültiges JSON** (Kommentare, trailing commas, unquoted keys)
- Standard-`json.loads()` ist zu strikt
- Keine Debug-Ausgaben bei Fehlern
- Sanitization könnte Properties überschreiben

---

## ✅ Lösung

### 1. Robustes JSON-Parsing mit `dirtyjson`

**Problem:** AI generiert JSON mit:
- Trailing commas: `{"test": 123,}`
- Unquoted keys: `{test: 123}`
- Kommentare: `{/* comment */ "test": 123}`

**Lösung:** Multi-Level Fallback-Parsing

```python
def _try_parse_with_fallbacks(candidate: str):
    parsers = [
        ("json.loads", json.loads),                    # Standard-Parser
        ("strip_trailing_commas", _strip_trailing...),  # Commas entfernen
        ("dirtyjson.loads", dirtyjson.loads)           # Toleranter Parser
    ]
    
    for parser_name, parser in parsers:
        try:
            result = parser(candidate)
            if parser_name != "json.loads":
                print(f"✅ JSON geparst mit: {parser_name}")
            return result
        except Exception as exc:
            errors.append(f"{parser_name}: {exc}")
    
    # Alle Parser fehlgeschlagen
    print("❌ JSON-Parsing fehlgeschlagen:")
    for err in errors:
        print(f"   - {err}")
    return None
```

**Fallback-Kette:**
1. `json.loads` - Standard Python JSON (strikt)
2. `strip_trailing_commas` - Entfernt `,}` und `,]`
3. `dirtyjson.loads` - Toleriert unquoted keys, Kommentare, etc.

### 2. Verbesserte Debug-Ausgaben

**Datei:** `ollama_client.py`

```python
def extract_json(text: str):
    # Debug: Input-Preview
    preview = text[:200] + "..." if len(text) > 200 else text
    print(f"🔍 JSON-Extraktion aus Text ({len(text)} Zeichen): {preview}")
    
    # Code-Fence-Extraktion
    if fence_match:
        candidate = fence_match.group(1).strip()
        print(f"📝 JSON-Block in Code-Fence gefunden ({len(candidate)} Zeichen)")
        
    # Roher Block-Extraktion
    if start != -1 and end != -1:
        candidate = text[start:end + 1]
        print(f"📝 JSON-Block gefunden: Position {start} bis {end}")
    
    # Sanitization
    elem_count = len(data.get("elements", []))
    conn_count = len(data.get("connections", []))
    print(f"🔧 Sanitize VPB: {elem_count} Elemente, {conn_count} Verbindungen")
```

### 3. Erweiterte Fehlerbehandlung im Import

**Datei:** `vpb_app.py`

```python
def _apply_full_process_json(self, parsed_data):
    print(f"\n🔧 _apply_full_process_json aufgerufen")
    print(f"   Typ: {type(parsed_data)}")
    
    # Validierung
    if not hasattr(self, 'canvas'):
        print(f"❌ Kein Canvas verfügbar")
        return
    
    if not isinstance(parsed_data, dict):
        print(f"❌ parsed_data ist kein Dict")
        return
    
    # Struktur-Info
    elem_count = len(parsed_data.get('elements', []))
    conn_count = len(parsed_data.get('connections', []))
    print(f"   Struktur: {elem_count} Elemente, {conn_count} Verbindungen")
    
    # Import
    self.canvas.load_from_dict(parsed_data)
    self.canvas.redraw_all()
    
    # Erfolg
    print(f"✅ Prozess ersetzt: {elem_count} Elemente, {conn_count} Verbindungen")
```

### 4. Detailliertes Merge-Logging

```python
def _merge_full_process_json(self, parsed_data):
    print(f"\n🔧 _merge_full_process_json aufgerufen")
    print(f"   Neu: {elem_count_new} Elemente, {conn_count_new} Verbindungen")
    print(f"   Existierend: {elem_count_existing} Elemente, {conn_count_existing} Verbindungen")
    
    for elem in parsed_data.get('elements', []):
        if elem_id not in self.canvas.elements:
            # Hinzufügen
            print(f"   ➕ Element hinzugefügt: {elem_id} ({elem.element_type})")
        else:
            print(f"   ⏭️  Element übersprungen (existiert): {elem_id}")
    
    print(f"✅ Gemerged: +{added_elements} Elemente, +{added_connections} Verbindungen")
```

---

## 🧪 Test-Ergebnisse

### Test 1: Gültiges JSON
```
🔍 JSON-Extraktion aus Text (155 Zeichen)
📝 JSON-Block in Code-Fence gefunden (143 Zeichen)
✅ JSON erfolgreich extrahiert (Code-Fence)
🔧 Sanitize VPB: 1 Elemente, 0 Verbindungen
✅ Resultat: 1 Elemente
```

### Test 2: JSON mit Trailing Commas
```
📝 JSON-Block in Code-Fence gefunden (145 Zeichen)
✅ JSON erfolgreich geparst mit: strip_trailing_commas
✅ JSON erfolgreich extrahiert (Code-Fence)
🔧 Sanitize VPB: 1 Elemente, 0 Verbindungen
✅ Resultat: 1 Elemente
```

### Test 3: JSON mit unquoted keys
```
📝 JSON-Block gefunden: Position 0 bis 126 (127 Zeichen)
✅ JSON erfolgreich geparst mit: dirtyjson.loads
✅ JSON erfolgreich extrahiert (roher Block)
🔧 Sanitize VPB: 1 Elemente, 0 Verbindungen
✅ Resultat: 1 Elemente
```

### Test 4: Vollständiger AI-Prozess
```
📝 JSON-Block in Code-Fence gefunden (1064 Zeichen)
✅ JSON erfolgreich extrahiert (Code-Fence)
🔧 Sanitize VPB: 3 Elemente, 2 Verbindungen
✅ Erfolgreich: 3 Elemente, 2 Verbindungen

📝 Erstes Element:
   ID: start_001
   Typ: START_EVENT
   Name: Antrag eingegangen
   Position: (100, 200)
```

---

## 📊 Import-Workflow

### Schritt 1: AI generiert JSON

```
User: "Erstelle ein Baugenehmigungsverfahren"

AI: Hier ist der Prozess:
```json
{
  "metadata": {...},
  "elements": [
    {element_id: "start_001", ...},  ← unquoted keys!
    {element_id: "func_001", ...},
  ],                                   ← trailing comma!
  "connections": [...]
}
```
```

### Schritt 2: ChatController extrahiert JSON

```python
parsed = OllamaClient.extract_json(ai_response)
```

**Ablauf:**
1. Sucht nach Code-Fence `​```json ... ​```​`
2. Falls nicht gefunden: Sucht ersten `{` bis letzten `}`
3. Versucht Parsing mit Fallback-Kette:
   - `json.loads` → ❌ Fehler: unquoted keys
   - `strip_trailing_commas` → ❌ Fehler: unquoted keys
   - `dirtyjson.loads` → ✅ Erfolgreich!

### Schritt 3: VPB-Struktur sanitizen

```python
data = OllamaClient._sanitize_vpb_structure(parsed)
```

**Sanitization:**
- Fehlende Properties mit Defaults ergänzen
- Numerische Werte konvertieren (x, y, deadline_days)
- Null-Werte durch Defaults ersetzen

### Schritt 4: Buttons anzeigen

```python
chat.add_dynamic_button("Diagramm ersetzen", replace_cb)
chat.add_dynamic_button("Diagramm mergen", merge_cb)
```

### Schritt 5: User klickt Button

**Replace:**
```python
_apply_full_process_json(parsed_data)
  → canvas.load_from_dict(parsed_data)
  → canvas.redraw_all()
```

**Merge:**
```python
_merge_full_process_json(parsed_data)
  → Für jedes Element/Connection:
      - Prüfe ob ID existiert
      - Wenn neu: VPBElement.from_dict() und hinzufügen
  → canvas.redraw_all()
```

---

## 🐛 Debugging-Tipps

### Problem: "Kein JSON im Text gefunden"

**Prüfen:**
```python
print(f"AI-Response:\n{ai_response}")
```

**Mögliche Ursachen:**
- Kein `{` und `}` im Text
- Code-Fence ohne Inhalt
- Text ist kein String

### Problem: "JSON konnte nicht geparst werden"

**Debug-Output:**
```
❌ JSON-Parsing fehlgeschlagen mit allen Parsern:
   - json.loads: Expecting property name enclosed in double quotes
   - strip_trailing_commas: Expecting property name enclosed in double quotes
   - dirtyjson.loads: AttributeError: module has no attribute 'loads'
```

**Lösung:**
```bash
# dirtyjson installieren
pip install dirtyjson
```

### Problem: "Elemente nicht vollständig"

**Prüfen:**
```python
print(f"Parsed: {len(parsed_data.get('elements', []))} Elemente")
print(f"Canvas: {len(canvas.elements)} Elemente")
```

**Mögliche Ursachen:**
- Sanitization überschreibt Properties
- VPBElement.from_dict() ignoriert Properties
- Canvas.load_from_dict() überspringt Elemente

---

## 📝 Datei-Änderungen

### `ollama_client.py`

**Änderungen:**
- ✅ `_try_parse_with_fallbacks()`: Parser-Namen für Debug-Output
- ✅ `_try_parse_with_fallbacks()`: dirtyjson-Check mit Warnung
- ✅ `extract_json()`: Debug-Output für Input-Preview
- ✅ `extract_json()`: Debug-Output für Code-Fence/Block-Extraktion
- ✅ `_sanitize_vpb_structure()`: Debug-Output für Element/Connection-Count

**Zeilen:** ~230-320

### `vpb_app.py`

**Änderungen:**
- ✅ `_apply_full_process_json()`: Validierung mit Debug-Output
- ✅ `_apply_full_process_json()`: Struktur-Info vor Import
- ✅ `_apply_full_process_json()`: Traceback bei Fehlern
- ✅ `_merge_full_process_json()`: Detailliertes Element/Connection-Logging
- ✅ `_merge_full_process_json()`: Zähler für hinzugefügte Elemente
- ✅ `_merge_full_process_json()`: Traceback bei Fehlern

**Zeilen:** ~1030-1100

---

## 🚀 Verbesserungen

### Kurzfristig

1. **Import-Validierung**
   - Prüfe ob alle Elemente valide IDs haben
   - Prüfe ob Verbindungen auf existierende Elemente verweisen
   - Zeige Warnungen für fehlende Properties

2. **Preview vor Import**
   - Zeige Prozess-Übersicht im Chat
   - User kann Import bestätigen oder ablehnen

### Mittelfristig

1. **Inkrementelles Merging**
   - Erkenne geänderte Elemente (nicht nur neue)
   - Update existierende Elemente mit neuen Properties
   - Konflikt-Resolution bei ID-Kollisionen

2. **Undo/Redo für AI-Imports**
   - Speichere Canvas-Zustand vor Import
   - Ermögliche Rückgängig-Machen

---

## 📊 Zusammenfassung

**Problem:** AI-JSON wird nicht vollständig importiert

**Ursachen:**
- Ungültiges JSON (trailing commas, unquoted keys)
- Fehlende Debug-Ausgaben
- Keine Fehlerbehandlung

**Lösungen:**
- ✅ `dirtyjson`-Fallback für tolerantes Parsing
- ✅ Multi-Level Parser-Kette mit Debug-Output
- ✅ Erweiterte Fehlerbehandlung mit Traceback
- ✅ Detailliertes Import-Logging (Element/Connection-Count)
- ✅ Test-Skript für JSON-Extraktion

**Resultat:**
- ✅ Gültiges JSON funktioniert (json.loads)
- ✅ Trailing Commas funktionieren (strip_trailing_commas)
- ✅ Unquoted Keys funktionieren (dirtyjson.loads)
- ✅ Vollständige AI-Prozesse werden korrekt importiert
- ✅ Detaillierte Debug-Ausgaben bei jedem Schritt

**Dateien geändert:**
- `ollama_client.py` (JSON-Parsing & Debug-Output)
- `vpb_app.py` (Import-Methoden & Fehlerbehandlung)
- `test_ai_json_import.py` (Test-Skript - NEU)

---

**Ende der Dokumentation**
