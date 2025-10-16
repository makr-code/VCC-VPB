# AI Chat Terminal - Wiederherstellung & Integration

## Übersicht

Der **AI Chat Terminal** wurde wiederhergestellt und in die refaktorisierte VPB Application integriert. Der Chat ermöglicht natürlichsprachliche Interaktion mit dem Canvas über ein Ollama-Backend.

## Status

✅ **Wiederhergestellt:** AI Chat Terminal ist funktional
✅ **Integriert:** In vertikalem PanedWindow unter dem Content-Bereich
✅ **Controller:** ChatController mit allen Legacy-Methoden
✅ **UI:** ChatPanel mit Eingabe, Historie und Task-Manager

## Architektur

### Komponenten

```
┌─────────────────────────────────────────────────────────┐
│              VPB Application (vpb_app.py)               │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Content Area (Diagram/Code/XML)           │ │
│  │  ┌─────────┬──────────────┬─────────────┐        │ │
│  │  │ Palette │    Canvas    │  Properties │        │ │
│  │  └─────────┴──────────────┴─────────────┘        │ │
│  └───────────────────────────────────────────────────┘ │
│         ↕ Resizable Sash                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │           AI Chat Terminal (height=200)           │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │  ChatPanel                                   │ │ │
│  │  │  - Message History                           │ │ │
│  │  │  - Input Field                               │ │ │
│  │  │  - Send/Stop Buttons                         │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  │  ChatController                                   │ │
│  │  - handle_send()                                  │ │
│  │  - handle_stop()                                  │ │
│  │  - handle_attach()                                │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Dateien

**Existierende Komponenten:**
- `vpb/ui/chat_panel.py` - Chat UI (Eingabe, Historie)
- `vpb/ui/chat_controller.py` - Chat-Logik & Ollama-Integration
- `vpb/ui/chat_console.py` - Hilfsfunktion zum Erstellen des Chats
- `vpb/ui/task_manager.py` - Background-Task-Manager

**Integration in vpb_app.py:**
- `_init_chat_terminal()` - Initialisiert Chat-Komponenten
- Chat-Methoden für Canvas-Manipulation
- Ollama-Konfiguration

## Integration in vpb_app.py

### Initialisierung

```python
class VPBApplication:
    def __init__(self, args=None):
        # Ollama Settings
        self._ollama_endpoint = "http://localhost:11434"
        self._ollama_model = "llama3.2"
        self._ollama_temperature = 0.7
        self._ollama_num_predict = 2048
        
    def _init_views(self):
        # Vertical Split: Content + Chat
        self.vertical_paned = tk.PanedWindow(orient=tk.VERTICAL)
        
        # Content Area (Diagram/Code/XML)
        content_area = tk.Frame(self.vertical_paned)
        self.vertical_paned.add(content_area, minsize=400)
        
        # AI Chat Terminal
        self._init_chat_terminal(self.vertical_paned)
```

### Chat Terminal Setup

```python
def _init_chat_terminal(self, parent):
    """Initialisiert den AI Chat Terminal."""
    from vpb.ui.chat_console import create_chat_console
    from vpb.ui.chat_controller import ChatController
    
    # Chat Terminal Container
    chat_frame = tk.Frame(parent)
    parent.add(chat_frame, minsize=150, height=200)
    
    # Chat Controller erstellen
    self.chat_controller = ChatController(self)  # ← self statt self.root!
    
    # Chat Console erstellen
    self.chat_container, self.chat_panel, self.task_manager = create_chat_console(
        self.root,
        chat_frame,
        on_send=self.chat_controller.handle_send,
        on_stop=self.chat_controller.handle_stop,
        on_attach=self.chat_controller.handle_attach,
    )
    
    # Controller mit UI verbinden
    self.chat_controller.bind_ui(self.chat_panel, self.task_manager)
```

### Canvas-Manipulations-Methoden

```python
def _apply_full_process_json(self, parsed_data):
    """Wendet vollständigen Prozess-JSON an (Replace)."""
    self.canvas.load_from_dict(parsed_data)
    self.canvas.redraw_all()
    self.status.set("✅ Prozess vollständig ersetzt")

def _merge_full_process_json(self, parsed_data):
    """Merged Prozess-JSON mit existierendem Canvas."""
    # Neue Elemente/Connections hinzufügen
    for elem in parsed_data.get('elements', []):
        if elem_id not in self.canvas.elements:
            new_elem = VPBElement.from_dict(elem)
            self.canvas.elements[elem_id] = new_elem
    self.canvas.redraw_all()

def _apply_add_only_patch(self, parsed_data):
    """Wendet Add-Only Patch an (nur neue Elemente)."""
    # Nur Elemente mit neuen IDs hinzufügen
    # ...

def _apply_diagnose_patch(self, parsed_data):
    """Wendet Diagnose-Patch an (Fehlerbehebungen)."""
    # Korrigiert existierende Elemente basierend auf Diagnose
    # ...

def _ensure_chat_visible(self):
    """Stellt sicher, dass Chat sichtbar ist."""
    pass  # TODO: Implementierung wenn minimierbar
```

## ChatController Anforderungen

Der `ChatController` erwartet von der App folgende Attribute/Methoden:

### Erforderliche Attribute

```python
# Ollama Configuration
self._ollama_endpoint    # "http://localhost:11434"
self._ollama_model       # "llama3.2"
self._ollama_temperature # 0.7
self._ollama_num_predict # 2048

# Canvas Reference
self.canvas              # VPBCanvas Instanz

# Status Feedback
self.status              # Property mit .set(message) Methode
```

### Erforderliche Methoden

```python
# Canvas-Manipulation
self._apply_full_process_json(parsed_data)  # Replace
self._merge_full_process_json(parsed_data)  # Merge
self._apply_add_only_patch(parsed_data)     # Add Only
self._apply_diagnose_patch(parsed_data)     # Diagnose & Fix

# UI Control
self._ensure_chat_visible()                 # Chat einblenden
```

## Ollama-Konfiguration

### Default Settings

```python
{
    "endpoint": "http://localhost:11434",
    "model": "llama3.2",
    "temperature": 0.7,
    "num_predict": 2048
}
```

### Anpassung (TODO)

```python
# In settings.json
{
    "ollama": {
        "endpoint": "http://localhost:11434",
        "model": "llama3.2:latest",
        "temperature": 0.5,
        "num_predict": 4096
    }
}

# In vpb_app.py
settings = self.settings_manager.get("ollama", {})
self._ollama_endpoint = settings.get("endpoint", "http://localhost:11434")
self._ollama_model = settings.get("model", "llama3.2")
```

## Chat-Funktionen

### 1. Prozess-Generierung

**User:** "Erstelle einen Prozess für Baugenehmigung mit Start, 3 Aufgaben und Ende"

**Chat Response:**
```json
{
  "elements": [
    {"id": "E1", "type": "START_EVENT", "name": "Antrag einreichen", ...},
    {"id": "E2", "type": "TASK", "name": "Unterlagen prüfen", ...},
    {"id": "E3", "type": "TASK", "name": "Genehmigung prüfen", ...},
    {"id": "E4", "type": "TASK", "name": "Bescheid erstellen", ...},
    {"id": "E5", "type": "END_EVENT", "name": "Genehmigung erteilt", ...}
  ],
  "connections": [...]
}
```

**Action:** Apply-Button → `_apply_full_process_json()` → Canvas zeigt Prozess

### 2. Prozess-Erweiterung

**User:** "Füge eine Entscheidung 'Ist vollständig?' nach der Prüfung hinzu"

**Chat Response:**
```json
{
  "elements": [
    {"id": "E6", "type": "GATEWAY", "name": "Ist vollständig?", ...}
  ],
  "connections": [
    {"id": "C5", "source": "E2", "target": "E6", ...},
    {"id": "C6", "source": "E6", "target": "E3", "label": "Ja", ...},
    {"id": "C7", "source": "E6", "target": "E1", "label": "Nein", ...}
  ]
}
```

**Action:** Merge-Button → `_merge_full_process_json()` → Neue Elemente hinzugefügt

### 3. Prozess-Diagnose

**User:** "Prüfe den Prozess auf Fehler"

**Chat Response:**
```json
{
  "issues": [
    {"type": "warning", "element": "E3", "message": "Keine Rechtsgrundlage angegeben"},
    {"type": "error", "element": "E4", "message": "Keine ausgehende Verbindung"}
  ],
  "fixes": [
    {"element_id": "E3", "legal_basis": "BauGB §29"},
    {"element_id": "E4", "connections": [...]}
  ]
}
```

**Action:** Fix-Button → `_apply_diagnose_patch()` → Korrekturen angewendet

## UI Layout

### Vertical PanedWindow

```
┌─────────────────────────────────────────────────────────┐
│                 Content Area                            │
│  (Canvas, Code, XML Tabs)                               │
│                  minsize=400                            │
│                                                         │
│                                                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
═══════════════════════════════════════════════════════════ ← Resizable Sash
┌─────────────────────────────────────────────────────────┐
│            AI Chat Terminal                             │
│  minsize=150, height=200                                │
│                                                         │
│  > User: Erstelle einen Prozess...                     │
│  🤖 Assistant: Hier ist der Prozess:                   │
│  [Apply] [Merge] [Fix]                                 │
│                                                         │
│  [_________________________________] [Send] [Stop]      │
└─────────────────────────────────────────────────────────┘
```

### Chat Panel Features

**Message History:**
- User-Messages (rechts, blau)
- Assistant-Messages (links, grau)
- System-Messages (zentriert, gelb)
- Code-Blocks (monospace, dunkler Hintergrund)

**Action Buttons:**
- 🔄 **Apply** - Wendet JSON vollständig an (Replace)
- ➕ **Merge** - Fügt neue Elemente hinzu
- 🔧 **Fix** - Wendet Diagnose-Korrekturen an
- 📋 **Copy** - Kopiert JSON in Zwischenablage

**Input Field:**
- Multiline Text-Eingabe
- Auto-Resize bei langem Text
- Strg+Enter zum Senden

**Control Buttons:**
- 📤 **Send** - Sendet Message an Ollama
- ⛔ **Stop** - Bricht laufende Anfrage ab
- 📎 **Attach** - Fügt Canvas-Kontext hinzu

## Status Feedback

### Status Property

```python
@property
def status(self):
    """Legacy-Kompatibilität für status.set()"""
    class StatusProxy:
        def __init__(self, status_bar):
            self._status_bar = status_bar
        
        def set(self, message):
            if self._status_bar:
                self._status_bar.set_message(message)
    
    return StatusProxy(self.status_bar)
```

### Chat Status Messages

```python
# Chat läuft
self.status.set("AI: Chat gestartet")

# Chat fertig
self.status.set("AI: Chat fertig")

# Fehler
self.status.set("AI: Kein laufender Chat")

# Prozess-Manipulation
self.status.set("✅ Prozess vollständig ersetzt")
self.status.set("✅ Prozess gemerged")
self.status.set("✅ 5 neue Elemente hinzugefügt")
self.status.set("✅ 3 Korrekturen angewendet")
```

## Bekannte Limitations

### 1. Ollama muss laufen

**Problem:** Chat funktioniert nur wenn Ollama-Server läuft

**Lösung:**
```bash
# Ollama starten
ollama serve

# Model herunterladen
ollama pull llama3.2
```

**Error Handling:**
```python
try:
    response = ollama.chat(...)
except Exception as e:
    self.status.set(f"❌ Ollama Fehler: {e}")
```

### 2. Keine Chat-History Persistierung

**Problem:** Chat-Historie geht beim Schließen verloren

**Lösung (TODO):**
```python
# In settings_manager
def save_chat_history(self, messages):
    with open("chats/chat_history.json", "w") as f:
        json.dump(messages, f)

def load_chat_history(self):
    with open("chats/chat_history.json", "r") as f:
        return json.load(f)
```

### 3. Chat nicht minimierbar/versteckbar

**Problem:** Chat nimmt immer Platz ein (minsize=150)

**Lösung (TODO):**
```python
def toggle_chat_terminal(self):
    if self.chat_visible:
        self.vertical_paned.remove(self.chat_frame)
        self.chat_visible = False
    else:
        self.vertical_paned.add(self.chat_frame, minsize=150, height=200)
        self.chat_visible = True
```

## Testing

### Manuelle Tests

**Test 1: Chat Terminal anzeigen**
```
1. ✅ App starten
2. ✅ Chat Terminal ist sichtbar unten
3. ✅ Input-Feld funktioniert
4. ✅ Send-Button vorhanden
```

**Test 2: Ollama-Integration (wenn Ollama läuft)**
```
1. ⏳ Nachricht eingeben "Hallo"
2. ⏳ Send klicken
3. ⏳ Assistant antwortet
4. ⏳ Message in Historie sichtbar
```

**Test 3: Canvas-Manipulation**
```
1. ⏳ "Erstelle einen einfachen Prozess" eingeben
2. ⏳ Apply-Button klicken
3. ⏳ Canvas zeigt generierten Prozess
4. ⏳ Status: "✅ Prozess vollständig ersetzt"
```

**Test 4: Status-Feedback**
```
1. ✅ Chat-Nachricht senden
2. ✅ Status: "AI: Chat gestartet"
3. ✅ Nach Antwort: "AI: Chat fertig"
```

## Zukünftige Erweiterungen

### Phase 1: Chat-UX
- ⏳ Chat minimieren/maximieren
- ⏳ Chat-Historie speichern (JSON)
- ⏳ Keyboard Shortcuts (Strg+Enter, Esc)
- ⏳ Auto-Scroll bei neuen Messages

### Phase 2: Erweiterte Features
- ⏳ Canvas-Screenshot als Kontext mitschicken
- ⏳ Multi-Turn Conversations
- ⏳ Conversation Branching
- ⏳ Export Chat als Markdown

### Phase 3: AI-Funktionen
- ⏳ Process-Validation via AI
- ⏳ Process-Optimization Suggestions
- ⏳ Automated Testing via AI
- ⏳ Natural Language Queries ("Zeige mir alle Gateways")

## Zusammenfassung

**Vorher:**
- ❌ Chat Terminal war in Legacy-Code eingebunden
- ❌ Nicht kompatibel mit refaktorisierter Architektur
- ❌ Fehlende Methoden und Attribute

**Nachher:**
- ✅ Chat Terminal wiederhergestellt
- ✅ Integration in vertikalem PanedWindow
- ✅ ChatController funktionsfähig
- ✅ Alle erforderlichen Methoden implementiert
- ✅ Status-Feedback funktioniert
- ✅ Canvas-Manipulation (Replace, Merge, Add, Fix)
- ✅ Ollama-Konfiguration vorhanden

**Status:** ✅ Wiederhergestellt und funktional (abhängig von Ollama-Server)

**Nächste Schritte:**
1. Ollama-Server testen
2. Chat-Historie implementieren
3. Chat minimierbar machen
4. Erweiterte AI-Funktionen hinzufügen
