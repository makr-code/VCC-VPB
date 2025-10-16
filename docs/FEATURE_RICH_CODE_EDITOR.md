# Feature: Rich Code Editor mit Syntax-Highlighting

## Übersicht

Der neue **Rich Code Editor** ersetzt die einfachen Textfelder in den JSON- und XML-Tabs durch professionelle Code-Editoren mit Syntax-Highlighting, Zeilennummern und Formatierungs-Funktionen.

## Features

### 1. **VS Code Dark+ Theme**
- Dunkler Hintergrund (#1e1e1e)
- Heller Text (#d4d4d4)
- Professionelle Farbgebung für Code-Elemente
- Augenschonende Darstellung

### 2. **Syntax-Highlighting**

#### JSON
- **Keywords** (blau): `true`, `false`, `null`
- **Strings** (orange): `"text"`
- **Numbers** (hellgrün): `123`, `45.67`, `1e-10`
- **Brackets** (gold): `{}`, `[]`, `:`, `,`

#### XML
- **Tags** (cyan): `<element>`
- **Attributes** (hellblau): `attribute="value"`
- **Strings** (orange): `"value"`
- **Comments** (grün): `<!-- comment -->`
- **Brackets** (gold): `<`, `>`, `/`

### 3. **Zeilennummern**
- Automatisch synchronisiert beim Scrollen
- Graue Hintergrundfarbe zur Abgrenzung
- Linksbündig mit 4-stelliger Breite
- Monospace-Font (Consolas/Courier)

### 4. **Toolbar**

#### Language Label
`📝 JSON` oder `📝 XML` - Zeigt die aktuelle Sprache an

#### Buttons

**⚡ Format** (Blau)
- Pretty-Print für JSON (2-Space Indentation)
- Pretty-Print für XML (2-Space Indentation)
- Nur im Edit-Mode verfügbar
- Bei Parse-Fehlern: Console-Output

**📋 Copy** (Grau)
- Kopiert gesamten Code in Zwischenablage
- Immer verfügbar
- Kein Highlighting erforderlich

**🔒 Read** / **🔓 Edit** (Rot/Grün)
- Toggle zwischen Read-Only und Edit-Mode
- Read-Mode (🔒 Rot): Kein Editieren, dunklerer Hintergrund
- Edit-Mode (🔓 Grün): Editierbar, normaler Hintergrund
- Schaltet Format-Button mit um

### 5. **Scrolling**
- Vertikaler Scrollbar (rechts)
- Horizontaler Scrollbar (unten, mit Spacer für Line Numbers)
- Synchronisiertes Scrolling zwischen Text und Zeilennummern
- Smooth Scrolling

### 6. **Performance**
- Delayed Syntax-Highlighting (300ms nach letzter Änderung)
- Verhindert Lag beim schnellen Tippen
- Regex-basiert (keine externen Dependencies)

## Architektur

### Komponenten

```
RichCodeEditor (tk.Frame)
├─ Toolbar (tk.Frame)
│  ├─ Language Label
│  └─ Button Frame
│     ├─ Format Button
│     ├─ Copy Button
│     └─ Read/Edit Toggle Button
├─ Editor Container (tk.Frame)
│  ├─ Line Numbers (tk.Text, disabled, 4 chars wide)
│  ├─ Code Text (tk.Text, undo enabled)
│  └─ Vertical Scrollbar
└─ Horizontal Scrollbar Frame
   ├─ Spacer (60px für Line Numbers)
   └─ Horizontal Scrollbar
```

### Dateien

**Neue Dateien:**
- `vpb/ui/rich_code_editor.py` (~400 lines) - RichCodeEditor Class

**Modifizierte Dateien:**
- `vpb_app.py` - `_create_code_tab()` verwendet jetzt RichCodeEditor

### Public API

```python
class RichCodeEditor(tk.Frame):
    def __init__(self, parent, language="json", **kwargs):
        """
        Args:
            parent: Parent Widget
            language: "json" oder "xml"
        """
    
    def set_text(self, text: str):
        """Setzt Text (triggert Highlighting)"""
    
    def get_text() -> str:
        """Gibt Text zurück"""
    
    def set_readonly(self, readonly: bool):
        """Setzt Read-Only Mode"""
    
    def clear():
        """Löscht Inhalt"""
```

### Integration

```python
# vpb_app.py - _create_code_tab()

from vpb.ui.rich_code_editor import RichCodeEditor

# JSON Editor
editor = RichCodeEditor(parent, language="json")
editor.pack(fill=tk.BOTH, expand=True)
self.json_editor = editor
self.json_text = editor.text  # Kompatibilität

# Initialer Content
editor.set_text("# JSON Code hier...")
```

## Verwendung

### 1. Code Anzeigen
```python
# JSON laden
json_content = json.dumps(data, indent=2)
self.json_editor.set_text(json_content)
# → Automatisches Syntax-Highlighting
```

### 2. Code Editieren
```python
# Edit-Mode aktivieren
self.json_editor.set_readonly(False)
# → Button zeigt "🔓 Edit"
# → Format-Button aktiviert
# → User kann editieren
```

### 3. Code Formatieren
```python
# User klickt "⚡ Format"
# → JSON wird pretty-printed (2-Space Indentation)
# → Bei Fehler: Console-Output
```

### 4. Code Kopieren
```python
# User klickt "📋 Copy"
# → Gesamter Code in Zwischenablage
```

## Technische Details

### Syntax-Highlighting Patterns

#### JSON Regex Patterns
```python
# Keywords
r'\b(true|false|null)\b'

# Strings
r'"([^"\\]|\\.)*"'

# Numbers
r'\b-?\d+\.?\d*([eE][+-]?\d+)?\b'

# Brackets
r'[{}[\],:]'
```

#### XML Regex Patterns
```python
# Comments
r'<!--.*?-->'  (re.DOTALL)

# Tags
r'</?(\w+)'

# Attributes
r'(\w+)='

# Strings
r'"([^"\\]|\\.)*"'

# Brackets
r'[<>/]'
```

### Color Scheme (VS Code Dark+)

```python
colors = {
    'bg': '#1e1e1e',           # Editor Background
    'fg': '#d4d4d4',           # Normal Text
    'line_bg': '#252526',      # Line Numbers Background
    'line_fg': '#858585',      # Line Numbers Text
    'selection': '#264f78',    # Selection Background
    'keyword': '#569cd6',      # Blue
    'string': '#ce9178',       # Orange
    'number': '#b5cea8',       # Light Green
    'comment': '#6a9955',      # Green
    'tag': '#4ec9b0',          # Cyan
    'attribute': '#9cdcfe',    # Light Blue
    'bracket': '#ffd700',      # Gold
}
```

### Event Handling

```python
# Key Release → Update Line Numbers
self.text.bind('<KeyRelease>', self._on_key_release)

# Text Modified → Delayed Highlighting (300ms)
self.text.bind('<<Modified>>', self._on_modified)

# Mouse Click → Update Line Numbers
self.text.bind('<Button-1>', self._update_line_numbers)

# Delayed Highlighting Job
self._highlight_job = self.after(300, self._apply_syntax_highlighting)
```

## Vorteile

### Benutzererfahrung
- ✅ **Professionelles Aussehen** - VS Code Dark+ Theme
- ✅ **Bessere Lesbarkeit** - Syntax-Highlighting
- ✅ **Navigation** - Zeilennummern
- ✅ **Produktivität** - Format-Button, Copy-Button
- ✅ **Sicherheit** - Read-Only Mode verhindert versehentliche Änderungen

### Entwicklung
- ✅ **Keine Dependencies** - Nur Tkinter + Regex
- ✅ **Einfache Integration** - Drop-in Replacement
- ✅ **Erweiterbar** - Neue Sprachen hinzufügbar
- ✅ **Performant** - Delayed Highlighting

## Beispiel-Screenshots (Konzept)

### JSON Editor
```
┌─────────────────────────────────────────────────────────┐
│ 📝 JSON        [⚡ Format] [📋 Copy] [🔒 Read]          │
├────┬────────────────────────────────────────────────────┤
│  1 │ {                                                   │
│  2 │   "name": "Antrag bearbeiten",                     │
│  3 │   "version": "1.0.0",                              │
│  4 │   "elements": [                                     │
│  5 │     {                                               │
│  6 │       "id": "e1",                                   │
│  7 │       "type": "START",                              │
│  8 │       "label": "Antrag einreichen",                │
│  9 │       "x": 100,                                     │
│ 10 │       "y": 100                                      │
│ 11 │     }                                               │
│ 12 │   ]                                                 │
│ 13 │ }                                                   │
└────┴────────────────────────────────────────────────────┘
```

Farben:
- `{`, `}`, `[`, `]`, `:`, `,` → Gold
- `"name"`, `"version"`, `"elements"` → Orange (Strings)
- `100`, `1.0.0` → Hellgrün (Numbers)

### XML Editor
```
┌─────────────────────────────────────────────────────────┐
│ 📝 XML         [⚡ Format] [📋 Copy] [🔓 Edit]          │
├────┬────────────────────────────────────────────────────┤
│  1 │ <?xml version="1.0" encoding="UTF-8"?>             │
│  2 │ <process name="Antrag bearbeiten">                 │
│  3 │   <!-- Prozess-Elemente -->                        │
│  4 │   <element id="e1" type="START">                   │
│  5 │     <label>Antrag einreichen</label>               │
│  6 │     <position x="100" y="100"/>                    │
│  7 │   </element>                                        │
│  8 │ </process>                                          │
└────┴────────────────────────────────────────────────────┘
```

Farben:
- `process`, `element`, `label`, `position` → Cyan (Tags)
- `name`, `id`, `type`, `x`, `y` → Hellblau (Attributes)
- `"Antrag bearbeiten"`, `"e1"`, `"START"` → Orange (Strings)
- `<!-- Prozess-Elemente -->` → Grün (Comments)

## Zukünftige Erweiterungen

### Mögliche Features
- 🔄 **Undo/Redo Buttons** in Toolbar
- 🔄 **Search/Replace** Dialog
- 🔄 **Line Wrapping** Toggle
- 🔄 **Font Size** Anpassung
- 🔄 **Export to File** Button
- 🔄 **Diff View** (Vergleich mit gespeicherter Version)
- 🔄 **Error Markers** (rote Wellenlinien bei Parse-Fehlern)
- 🔄 **Auto-Complete** für JSON-Keys

### Weitere Sprachen
- Python (.py)
- JavaScript (.js)
- YAML (.yml)
- Markdown (.md)

## Zusammenfassung

Der **Rich Code Editor** hebt die VPB Process Designer-UX auf ein neues Level:

**Vorher:**
- Einfache weiße Textfelder
- Keine Syntax-Highlighting
- Keine Zeilennummern
- Keine Formatierungs-Funktionen

**Nachher:**
- Professioneller VS Code Dark+ Editor
- Vollständiges Syntax-Highlighting
- Zeilennummern mit Sync-Scrolling
- Format, Copy, Read-Only Funktionen
- Bessere Lesbarkeit und Produktivität

✅ **Status:** Implementiert und funktionsfähig
