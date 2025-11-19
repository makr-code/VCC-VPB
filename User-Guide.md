# User Guide / Benutzerhandbuch

**Version:** 0.5.0  
**Target:** End Users / Endbenutzer

---

## Overview / Übersicht

VPB (Visual Process Builder) ermöglicht die visuelle Modellierung von Verwaltungsprozessen mit SPS-ähnlichen Elementen.

VPB (Visual Process Builder) enables visual modeling of administrative processes with PLC-like elements.

---

## Interface / Benutzeroberfläche

### Main Window / Hauptfenster

```
┌─────────────────────────────────────────────────────────────┐
│ Menu Bar / Menüleiste                                        │
├─────────────────────────────────────────────────────────────┤
│ Toolbar / Werkzeugleiste                                     │
├─────────┬───────────────────────────────────┬───────────────┤
│         │                                   │               │
│ Palette │        Canvas                     │  Properties   │
│         │     (Arbeitsfläche)              │               │
│         │                                   │               │
├─────────┴───────────────────────────────────┴───────────────┤
│ Status Bar / Statusleiste                                    │
└─────────────────────────────────────────────────────────────┘
```

### Components / Komponenten

**1. Palette (Links / Left)**
- Element-Bibliothek / Element library
- Drag & Drop auf Canvas
- Kategorisiert nach Typ
- **See:** [[SPS-Elements]]

**2. Canvas (Mitte / Center)**
- Prozess-Arbeitsfläche / Process workspace
- Zoom & Pan
- Grid-Snapping
- Element-Platzierung

**3. Properties (Rechts / Right)**
- Element-Eigenschaften / Element properties
- Dynamische Formulare / Dynamic forms
- Echtzeit-Validierung / Real-time validation

**4. Menu Bar (Oben / Top)**
- Datei / File
- Bearbeiten / Edit
- Ansicht / View
- Prozess / Process
- Werkzeuge / Tools
- Hilfe / Help

---

## Working with Processes / Arbeiten mit Prozessen

### Creating a Process / Prozess erstellen

1. **New Process / Neuer Prozess**
   ```
   File → New (Ctrl+N)
   ```

2. **Process Properties / Prozess-Eigenschaften**
   - Name
   - Description / Beschreibung
   - Version
   - Author / Autor

### Adding Elements / Elemente hinzufügen

**Method 1: Drag & Drop**
1. Select element from palette
2. Drag onto canvas
3. Drop at desired position

**Method 2: Double-Click**
1. Double-click element in palette
2. Click on canvas to place

**Available Elements:**
- [[Counter-Element]] - Zähler / Counter
- [[Condition-Element]] - Bedingung / Condition
- [[Error-Handler-Element]] - Fehlerbehandlung / Error handler
- [[State-Element]] - Zustand / State
- [[Interlock-Element]] - Verriegelung / Interlock
- And more... / Und mehr...

### Connecting Elements / Elemente verbinden

**Create Connection / Verbindung erstellen:**
1. Click source element output
2. Drag to target element input
3. Release mouse

**Connection Types:**
- Normal flow (solid line)
- Conditional flow (dashed line)
- Error flow (red line)

**Connection Properties:**
- Label / Beschriftung
- Condition / Bedingung
- Priority / Priorität

### Editing Properties / Eigenschaften bearbeiten

1. **Select Element**
   - Click on element
   - Properties panel updates

2. **Edit Values**
   - Text fields
   - Dropdowns
   - Checkboxes
   - Number inputs

3. **Validation**
   - Real-time validation
   - Error indicators
   - Tooltips with hints

### Layout & Organization / Layout & Organisation

**Auto-Layout:**
```
Process → Auto Layout (Ctrl+L)
```

**Layout Algorithms:**
- Hierarchical (default)
- Grid
- Circular
- Force-directed

**Manual Alignment:**
- Align left / right / top / bottom
- Distribute horizontally / vertically
- Make same size

**Grouping:**
- Select multiple elements (Ctrl+Click)
- Group (Ctrl+G)
- Ungroup (Ctrl+Shift+G)

---

## Validation / Validierung

### Process Validation

**Run Validation:**
```
Process → Validate (F5)
```

**Validation Checks:**
- ✅ All elements connected
- ✅ No cycles (unless intended)
- ✅ Required properties set
- ✅ Valid property values
- ✅ Consistent types

**Validation Results:**
- ✅ Green: No errors
- ⚠️ Yellow: Warnings
- ❌ Red: Errors

**Error Types:**
- Missing connections
- Invalid property values
- Type mismatches
- Unreachable elements

---

## Export / Exportieren

### Export Formats

VPB supports multiple export formats:

**1. JSON (.vpb.json)**
- Native format
- Full process data
- Human-readable

**2. XML**
- Standard format
- Interoperability
- Schema-validated

**3. BPMN 2.0**
- Business Process Model
- Standard compliance
- Tool interoperability

**4. Images**
- PNG (raster)
- SVG (vector)
- High resolution

**5. PDF**
- Documentation
- Printable
- Annotations

**Export Process:**
```
File → Export → [Format]
```

**See:** [[Export-Formats]] for details

---

## AI Features / KI-Funktionen

### AI Chat / KI-Chat

**Open Chat:**
```
Tools → AI Chat (Ctrl+Shift+A)
```

**Capabilities:**
- Process generation from text
- Element suggestions
- Validation assistance
- Documentation help

### Process Generation

**Generate from Description:**
1. Open AI Chat
2. Describe your process
3. Review generated process
4. Accept or modify

**Example:**
```
"Create a purchase approval process with 3 approval levels
and error handling for rejected requests"
```

**See:** [[AI-Features]] for more details

---

## Keyboard Shortcuts

### Essential Shortcuts / Wichtige Tastenkürzel

| Action | Shortcut |
|--------|----------|
| New Process | `Ctrl+N` |
| Open | `Ctrl+O` |
| Save | `Ctrl+S` |
| Undo | `Ctrl+Z` |
| Redo | `Ctrl+Y` |
| Delete | `Del` |
| Select All | `Ctrl+A` |
| Copy | `Ctrl+C` |
| Paste | `Ctrl+V` |
| Auto Layout | `Ctrl+L` |
| Validate | `F5` |
| Zoom In | `Ctrl++` |
| Zoom Out | `Ctrl+-` |
| Zoom Fit | `Ctrl+0` |
| AI Chat | `Ctrl+Shift+A` |

**Full List:** [[Keyboard-Shortcuts]]

---

## Best Practices / Bewährte Praktiken

### Process Design

1. **Start Simple**
   - Begin with main flow
   - Add details incrementally

2. **Use Meaningful Names**
   - Descriptive element names
   - Clear connection labels

3. **Group Related Elements**
   - Use visual grouping
   - Organize by function

4. **Validate Frequently**
   - Run validation often
   - Fix errors early

5. **Document Decisions**
   - Add descriptions
   - Use comments

### Performance

1. **Limit Complexity**
   - Keep processes focused
   - Split large processes

2. **Use Auto-Save**
   - Enabled by default
   - Recovers from crashes

3. **Regular Backups**
   - Export regularly
   - Version control recommended

---

## Tips & Tricks

### Productivity

- **Canvas Navigation:**
  - Pan: Hold `Space` + Drag
  - Zoom: `Ctrl` + Mouse Wheel
  - Fit to view: `Ctrl+0`

- **Quick Selection:**
  - Rectangle select: Drag on canvas
  - Add to selection: `Ctrl+Click`
  - Invert selection: `Ctrl+I`

- **Duplicate Elements:**
  - Copy-paste: `Ctrl+C`, `Ctrl+V`
  - Offset automatically

- **Multi-Edit:**
  - Select multiple elements
  - Edit common properties together

### Advanced Features

- **Custom Palettes:** Create your own element libraries
- **Templates:** Save processes as templates
- **Macros:** Record repetitive actions
- **Plugins:** Extend functionality

---

## Examples / Beispiele

### Simple Process

See [[Examples]] for:
- Approval workflows
- Error handling patterns
- State machines
- Counter examples
- Condition logic

---

## Getting Help / Hilfe erhalten

### Resources

- **[[FAQ]]** - Häufig gestellte Fragen
- **[[Troubleshooting]]** - Problemlösungen
- **[[Examples]]** - Beispielprozesse
- **GitHub Issues:** Report bugs or request features

### Community

- GitHub Discussions (coming soon)
- User forum (coming soon)

---

## Next Steps

- Explore **[[SPS-Elements]]** in detail
- Try **[[Examples]]**
- Learn **[[Export-Formats]]**
- Discover **[[AI-Features]]**

---

[[Home]] | [[Getting-Started]] | [[SPS-Elements]]
