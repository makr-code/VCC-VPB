# VPB Refactor - Fehlende Implementierungen & Funktionen

**Datum:** 14. Oktober 2025  
**Status:** Alpha 0.2.0 Integration Analysis  
**Vergleich:** `vpb_app.py` (NEU) vs. `vpb_app_legacy.py` (ALT)

---

## 📊 Übersicht

| Kategorie | Status | Items | Priorität |
|-----------|--------|-------|-----------|
| Core Integration Classes | ⚠️ Teilweise | 6/6 fehlen | ⭐⭐⭐ Hoch |
| UI Controllers | ⚠️ Teilweise | 3/3 fehlen | ⭐⭐⭐ Hoch |
| Canvas Features | ⚠️ Teilweise | 5/10 fehlen | ⭐⭐ Mittel |
| Menu Actions | ❌ Fehlt | 20+ fehlen | ⭐⭐⭐ Hoch |
| Keyboard Shortcuts | ❌ Fehlt | Alle fehlen | ⭐⭐ Mittel |
| Settings Persistence | ❌ Fehlt | Komplett | ⭐⭐ Mittel |
| Autosave | ❌ Fehlt | Komplett | ⭐ Niedrig |
| Export Features | ⚠️ Teilweise | PDF/SVG fehlen | ⭐⭐ Mittel |

---

## 🔴 KRITISCHE FEHLENDE KOMPONENTEN

### 1. Integration Classes (Alt: vpb/ui/app_*.py)

Diese Klassen verbinden die UI-Komponenten mit der Business-Logik:

#### 1.1 AppActions ❌ FEHLT
**Datei (Alt):** `vpb/ui/app_actions.py`  
**Funktion:** Orchestriert alle Benutzer-Aktionen (Datei, Bearbeiten, etc.)  
**Was fehlt:**
- File Operations (New, Open, Save, Save As, Close)
- Edit Operations (Undo, Redo, Cut, Copy, Paste, Delete)
- Element Operations (Add, Move, Resize, Group, Ungroup)
- View Operations (Zoom In/Out, Pan, Fit to Screen)
- Layout Operations (Auto-Layout, Align, Distribute)
- Export Operations (PDF, SVG, PNG, XML, BPMN)

**Implementation Status:**
```python
# ALT (Legacy):
from vpb.ui.app_actions import AppActions
self.app_actions = AppActions(self)

# NEU (Refactored):
# ❌ Nicht implementiert!
# Controllers handhaben nur Event-Bus Events
# File-Dialoge in vpb_app.py, aber nicht alle Actions
```

**TODO:**
- [ ] Erstelle `vpb/integration/app_actions.py`
- [ ] Implementiere alle Actions als Event-Publisher
- [ ] Integriere mit bestehenden Controllern
- [ ] Keyboard Shortcuts verbinden

---

#### 1.2 AppPaletteIntegration ❌ FEHLT
**Datei (Alt):** `vpb/ui/app_palette_integration.py`  
**Funktion:** Verbindet Palette mit Canvas (Element-Platzierung)  
**Was fehlt:**
- Element-Picking aus Palette
- Add-Mode Aktivierung/Deaktivierung
- Canvas-Click → Element-Platzierung
- Palette Reload Logik

**Implementation Status:**
```python
# ALT:
from vpb.ui.app_palette_integration import AppPaletteIntegration
self._palette_integration = AppPaletteIntegration(self, self._palette)

# NEU:
# ⚠️ Teilweise: PaletteView publiziert "ui:palette:element_picked"
# ❌ ABER: Niemand reagiert darauf! Canvas wird nicht in Add-Mode gesetzt
```

**TODO:**
- [ ] Erstelle `vpb/integration/palette_integration.py`
- [ ] Subscribe zu `ui:palette:element_picked`
- [ ] Setze Canvas in Add-Mode
- [ ] Handle Canvas-Click für Element-Platzierung
- [ ] Zeige Cursor-Preview beim Hovern

---

#### 1.3 AppPropertiesBridge ❌ FEHLT
**Datei (Alt):** `vpb/ui/app_properties_bridge.py`  
**Funktion:** Synchronisiert Properties-Panel mit Canvas-Selection  
**Was fehlt:**
- Selection-Change → Properties aktualisieren
- Properties-Change → Element aktualisieren
- Undo/Redo für Property-Änderungen
- Multi-Selection Support

**Implementation Status:**
```python
# ALT:
from vpb.ui.app_properties_bridge import AppPropertiesBridge
self._properties_bridge = AppPropertiesBridge(self, self._properties)

# NEU:
# ❌ Nicht implementiert!
# PropertiesView existiert, aber keine Verbindung zum Canvas
```

**TODO:**
- [ ] Erstelle `vpb/integration/properties_bridge.py`
- [ ] Subscribe zu Canvas Selection Events
- [ ] Update Properties Panel bei Selection
- [ ] Handle Property Changes → Canvas Update
- [ ] Implementiere Undo/Redo

---

#### 1.4 AppChatIntegration ❌ FEHLT (TEILWEISE)
**Datei (Alt):** `vpb/ui/app_chat_integration.py`  
**Funktion:** Verbindet AI-Chat mit Canvas/Dokument  
**Was fehlt:**
- AI → Canvas Update (generierte Elemente einfügen)
- Canvas → AI Context (aktuelles Dokument senden)
- Streaming AI Responses
- Task Management Integration

**Implementation Status:**
```python
# ALT:
from vpb.ui.app_chat_integration import AppChatIntegration
self._chat_integration = AppChatIntegration(self)

# NEU:
# ⚠️ Teilweise: ChatController + ChatPanel vorhanden
# ❌ ABER: Keine Integration mit Canvas/Document
```

**TODO:**
- [ ] Erweitere ChatController
- [ ] Implementiere AI → Document Callbacks
- [ ] Implementiere Document → AI Context
- [ ] Integriere mit AIController

---

#### 1.5 AppShortcuts ❌ FEHLT
**Datei (Alt):** `vpb/ui/app_shortcuts.py`  
**Funktion:** Keyboard Shortcuts Management  
**Was fehlt:**
- ALLE Keyboard Shortcuts!
- Shortcut Overlay (Hilfe-Dialog)
- Custom Shortcut Configuration

**Implementation Status:**
```python
# ALT:
from vpb.ui.app_shortcuts import AppShortcuts
self.shortcuts = AppShortcuts(self)
# Bindet: Ctrl+N, Ctrl+O, Ctrl+S, Ctrl+Z, Ctrl+Y, Del, etc.

# NEU:
# ❌ Komplett nicht implementiert!
```

**Fehlende Shortcuts:**
- `Ctrl+N` - Neues Dokument
- `Ctrl+O` - Öffnen
- `Ctrl+S` - Speichern
- `Ctrl+Shift+S` - Speichern unter
- `Ctrl+Z` - Undo
- `Ctrl+Y` / `Ctrl+Shift+Z` - Redo
- `Ctrl+C` - Kopieren
- `Ctrl+V` - Einfügen
- `Ctrl+X` - Ausschneiden
- `Del` - Löschen
- `Ctrl+A` - Alles auswählen
- `Ctrl++` - Zoom In
- `Ctrl+-` - Zoom Out
- `Ctrl+0` - Zoom Reset
- `F1` - Hilfe
- `F5` - Refresh
- `Space` - Pan-Mode (Hand-Tool)

**TODO:**
- [ ] Erstelle `vpb/integration/shortcuts.py`
- [ ] Implementiere alle Standard-Shortcuts
- [ ] Verbinde mit Controllers/Actions
- [ ] Erstelle Shortcut-Overlay Dialog
- [ ] Persistiere Custom Shortcuts

---

#### 1.6 AppTaskDispatch ❌ FEHLT
**Datei (Alt):** `vpb/ui/app_task_dispatch.py`  
**Funktion:** Background Task Management (AI, Export, etc.)  
**Was fehlt:**
- Task Queue
- Progress Feedback
- Cancel Funktionalität

**Implementation Status:**
```python
# ALT:
from vpb.ui.app_task_dispatch import AppTaskDispatch
self.task_dispatch = AppTaskDispatch(self)

# NEU:
# ⚠️ TaskManager existiert (für Chat), aber nicht allgemein verfügbar
```

**TODO:**
- [ ] Erweitere TaskManager für allgemeine Tasks
- [ ] Integriere mit ExportController
- [ ] Integriere mit AIController
- [ ] Progress-Bar in StatusBar

---

## 🟡 UI CONTROLLERS (Alt: vpb/ui/*_controller.py)

### 2.1 CanvasController ❌ FEHLT
**Datei (Alt):** `vpb/ui/canvas_controller.py`  
**Funktion:** Low-Level Canvas Event Handling  
**Was fehlt:**
- Mouse-Event Routing
- Selection Management
- Drag & Drop Logik
- Context Menu

**Implementation Status:**
```python
# ALT:
from vpb.ui import CanvasController
self.canvas_controller = CanvasController(self, self.canvas)

# NEU:
# ⚠️ ElementController + ConnectionController existieren
# ❌ ABER: Kein Low-Level Canvas-Controller
```

**TODO:**
- [ ] Integriere mit ElementController
- [ ] Mouse-Event Delegation
- [ ] Selection State Management

---

### 2.2 PropertiesController ✅ VORHANDEN (aber nicht verbunden)
**Datei (Alt):** `vpb/ui/properties_controller.py`  
**Status:** Existiert, aber nicht mit Canvas verbunden  
**TODO:**
- [ ] Verbinde mit AppPropertiesBridge
- [ ] Selection-Sync implementieren

---

### 2.3 TaskController ⚠️ TEILWEISE
**Datei (Alt):** `vpb/ui/task_controller.py`  
**Status:** TaskManager existiert, aber nicht vollständig integriert  
**TODO:**
- [ ] Erweitere für allgemeine Tasks
- [ ] Progress Tracking

---

## 🟠 CANVAS FEATURES

### 3.1 Grid & Lineale ⚠️ TEILWEISE IMPLEMENTIERT
**Status:**
- ✅ Grid-Code vorhanden (`VPBCanvas.grid_visible`, `_draw_grid()`)
- ✅ Lineale vorhanden (`RulerCanvas`)
- ❌ Nicht initial gezeichnet
- ❌ Nicht mit Canvas verbunden

**Gefixte Issues:**
```python
# GEFIXED in vpb_app.py:
self.ruler_x.attach(self.canvas)
self.ruler_y.attach(self.canvas)
self.canvas.grid_visible = True
self.canvas.redraw_all()
```

**Verbleibende TODOs:**
- [ ] Grid Toggle in Menu
- [ ] Grid Size Einstellung
- [ ] Snap-to-Grid Toggle
- [ ] Lineale Show/Hide Toggle

---

### 3.2 Hierarchie-Canvas ⚠️ TEILWEISE
**Status:**
- ✅ HierarchyCanvas Widget vorhanden
- ❌ Nicht mit Daten gefüllt
- ❌ Keine Selection-Synchronisation

**TODO:**
- [ ] Hierarchie-Daten aus Document extrahieren
- [ ] HierarchyCanvas.redraw() bei Document-Änderung
- [ ] Selection-Sync: Hierarchy ↔ Canvas

---

### 3.3 Zeitachse (Time Axis) ❌ FEHLT
**Status:**
- ✅ Code vorhanden (`time_axis_enabled`, `_draw_time_axis()`)
- ❌ Nicht aktiviert

**TODO:**
- [ ] Aktiviere Zeitachse in Canvas
- [ ] Zeitachse Toggle in Menu
- [ ] Zeitachse Interval Einstellung

---

### 3.4 Zoom & Pan ⚠️ TEILWEISE
**Status:**
- ✅ Zoom/Pan Code in Canvas vorhanden
- ⚠️ Mausrad-Verhalten konfigurierbar?
- ❌ Zoom-Controls in UI fehlen

**TODO:**
- [ ] Zoom-Buttons in Toolbar
- [ ] Zoom-Slider in Toolbar
- [ ] Fit-to-Screen Button
- [ ] Zoom-Level Anzeige in StatusBar

---

### 3.5 Undo/Redo ⚠️ TEILWEISE
**Status:**
- ✅ Undo/Redo Stack in Canvas vorhanden
- ❌ Nicht mit UI verbunden

**TODO:**
- [ ] Undo/Redo Buttons in Toolbar
- [ ] Undo/Redo in Menu
- [ ] Keyboard Shortcuts (Ctrl+Z, Ctrl+Y)
- [ ] Undo/Redo Historie anzeigen

---

## 🔵 MENU ACTIONS

### 4.1 Datei-Menü ⚠️ TEILWEISE
**Implementiert:**
- ✅ Neu (Event: `ui:menu:file:new`)
- ✅ Öffnen (Event: `ui:menu:file:open`)
- ✅ Speichern (Event: `ui:menu:file:save`)

**Fehlt:**
- ❌ Speichern unter
- ❌ Schließen
- ❌ Recent Files Liste
- ❌ Import (JSON, XML, BPMN)
- ❌ Export Submenu (PDF, SVG, PNG, XML, BPMN)

**TODO:**
- [ ] Erweitere MenuBar um fehlende Items
- [ ] Implementiere Export-Dialoge
- [ ] Recent Files Management

---

### 4.2 Bearbeiten-Menü ❌ KOMPLETT FEHLT
**Fehlt:**
- ❌ Undo/Redo
- ❌ Cut/Copy/Paste
- ❌ Delete
- ❌ Select All
- ❌ Find Element

**TODO:**
- [ ] Erstelle Edit-Menu Items
- [ ] Implementiere Clipboard-Operationen
- [ ] Implementiere Find-Dialog

---

### 4.3 Ansicht-Menü ❌ KOMPLETT FEHLT
**Fehlt:**
- ❌ Zoom In/Out/Reset
- ❌ Fit to Screen
- ❌ Grid Toggle
- ❌ Lineale Toggle
- ❌ Zeitachse Toggle
- ❌ Hierarchie Toggle
- ❌ Fullscreen

**TODO:**
- [ ] Erstelle View-Menu
- [ ] Verbinde mit Canvas-Settings

---

### 4.4 Einfügen-Menü ❌ FEHLT
**Fehlt:**
- ❌ Element einfügen (aus Palette)
- ❌ Verbindung einfügen
- ❌ Gruppe erstellen
- ❌ Kommentar einfügen

**TODO:**
- [ ] Erstelle Insert-Menu
- [ ] Verbinde mit Palette

---

### 4.5 Anordnen-Menü ⚠️ TEILWEISE
**Status:**
- ✅ Event-Bus Events existieren
- ❌ Keine Menu-Items

**TODO:**
- [ ] Erstelle Arrange-Menu
- [ ] Align Submenu (Left, Right, Top, Bottom, Center H/V)
- [ ] Distribute Submenu (Horizontal, Vertical)
- [ ] Formation Submenu (Line, Circle, Grid)
- [ ] Auto-Layout

---

### 4.6 Tools-Menü ❌ FEHLT
**Fehlt:**
- ❌ Validation ausführen
- ❌ AI Process Generation
- ❌ AI Ingestion Wizard
- ❌ Merge Tool
- ❌ Diff Tool

**TODO:**
- [ ] Erstelle Tools-Menu
- [ ] Verbinde mit AIController
- [ ] Verbinde mit ValidationController

---

### 4.7 Hilfe-Menü ⚠️ TEILWEISE
**Implementiert:**
- ✅ About Dialog

**Fehlt:**
- ❌ Keyboard Shortcuts Overlay
- ❌ Documentation
- ❌ Check for Updates

**TODO:**
- [ ] Keyboard Shortcuts Dialog
- [ ] Link zu Dokumentation
- [ ] Update-Checker

---

## 🟢 SETTINGS & PERSISTENCE

### 5.1 Settings Persistence ❌ FEHLT
**Was fehlt:**
- Fenster-Position & Größe
- Paned-Window Sash-Positionen
- Grid-Einstellungen
- Zoom-Level
- Recent Files
- Letzte Palette
- Theme-Einstellungen

**TODO:**
- [ ] Implementiere `_save_window_state()` vollständig
- [ ] Load Settings beim Start
- [ ] Save Settings beim Exit

---

### 5.2 Autosave ❌ FEHLT
**Was fehlt:**
- Automatisches Speichern
- Autosave-Interval Einstellung
- Crash Recovery

**TODO:**
- [ ] Implementiere Autosave-Timer
- [ ] Autosave-Ordner erstellen
- [ ] Recovery-Dialog bei Start

---

## 📝 EXPORT FEATURES

### 6.1 PDF Export ⚠️ SERVICE VORHANDEN
**Status:**
- ✅ ExportService.export_to_pdf() existiert
- ❌ Nicht mit UI verbunden

**TODO:**
- [ ] PDF Export Dialog
- [ ] Export-Settings (DPI, Page Size)
- [ ] Progress Feedback

---

### 6.2 SVG Export ⚠️ SERVICE VORHANDEN
**Status:**
- ✅ ExportService.export_to_svg() existiert
- ❌ Nicht mit UI verbunden

**TODO:**
- [ ] SVG Export Dialog
- [ ] Export-Settings

---

### 6.3 PNG Export ⚠️ SERVICE VORHANDEN
**Status:**
- ✅ ExportService.export_to_png() existiert
- ❌ Nicht mit UI verbunden

**TODO:**
- [ ] PNG Export Dialog
- [ ] Auflösungs-Einstellung

---

### 6.4 BPMN Export ❌ FEHLT
**Was fehlt:**
- BPMN 2.0 XML Export
- BPMN Mapping (VPB → BPMN)

**TODO:**
- [ ] Implementiere BPMN-Exporter
- [ ] BPMN-Mapping definieren

---

## 🎨 WEITERE FEHLENDE FEATURES

### 7.1 Theme Support ❌ FEHLT
**TODO:**
- [ ] Dark Mode
- [ ] Custom Themes
- [ ] Theme Switcher in Settings

---

### 7.2 Multi-Language ❌ FEHLT
**TODO:**
- [ ] i18n Infrastructure
- [ ] Deutsch/Englisch Übersetzungen

---

### 7.3 Plugins/Extensions ❌ FEHLT
**TODO:**
- [ ] Plugin API definieren
- [ ] Plugin-Loader
- [ ] Extension-Marketplace?

---

## 📊 PRIORITÄTEN-MATRIX

### 🔴 PHASE 7: KRITISCHE INTEGRATION (Nächste Schritte)
**Zeitaufwand:** 2-3 Tage

1. ✅ **AppPaletteIntegration** (1 Tag)
   - Element-Picking funktioniert nicht!
   - Canvas Add-Mode fehlt

2. ✅ **AppPropertiesBridge** (0.5 Tag)
   - Properties-Panel funktioniert nicht!
   - Selection-Sync fehlt

3. ✅ **AppShortcuts** (0.5 Tag)
   - Keine Keyboard Shortcuts!
   - Kritisch für UX

4. ✅ **AppActions** (1 Tag)
   - Viele Menu-Items funktionieren nicht!
   - File/Edit/View Actions fehlen

---

### 🟡 PHASE 8: UI VERVOLLSTÄNDIGUNG (Follow-up)
**Zeitaufwand:** 2-3 Tage

1. Menu-Vervollständigung (1 Tag)
   - Edit, View, Insert, Arrange, Tools Menus

2. Export-Dialoge (1 Tag)
   - PDF, SVG, PNG, BPMN Dialogs

3. Settings & Persistence (1 Tag)
   - Window State, Recent Files, Autosave

---

### 🟢 PHASE 9: ADVANCED FEATURES (Optional)
**Zeitaufwand:** 3-5 Tage

1. AI-Integration Verbesserungen
2. Theme Support
3. Multi-Language
4. Plugin System

---

## 🎯 NÄCHSTE SCHRITTE (EMPFOHLEN)

### ✅ ERLEDIGT (Heute):
1. **Grid & Lineale Fix** ✅ DONE
   - `ruler_x.attach(canvas)` ✅
   - `canvas.redraw_all()` ✅

2. **Event-Bridge** ✅ DONE (1 Stunde)
   - Menus/Toolbar → Controller Events ✅
   - Dialoge funktionieren ✅

3. **Legacy Canvas Integration** ✅ DONE (2 Stunden)
   - DocumentController → Canvas direkt ✅
   - CRUD funktioniert ✅
   - Mausbedienung funktioniert ✅

### Nächste Woche:
4. **AppPaletteIntegration** (1-2 Stunden) - ⚠️ TEILWEISE ERLEDIGT
   - Element-Picking funktioniert ✅
   - Canvas Add-Mode aktiviert ✅
   - ABER: Noch keine vollständige Integration-Klasse

5. **AppPropertiesBridge** (1 Stunde)
   - Subscribe zu Canvas Selection Events
   - Update Properties Panel

6. **AppShortcuts** (2-3 Stunden)
   - Implementiere Standard-Shortcuts
   - Verbinde mit Controllers

5. **AppActions** (1 Tag)
   - Implementiere fehlende Actions
   - Erweitere Menus

6. **Export-Dialoge** (1 Tag)
   - PDF/SVG/PNG Export UI

### Nächste Woche:
7. **Settings Persistence** (1 Tag)
8. **Autosave** (0.5 Tag)
9. **Menu-Vervollständigung** (1 Tag)

---

## 📈 FORTSCHRITT TRACKING

```
Phase 1-6: Refactoring          ✅ 100% (765 Tests passing)
Phase 7: Integration Classes    ❌   0% (6/6 fehlen)
Phase 8: UI Vervollständigung   ❌  10% (Basis vorhanden)
Phase 9: Advanced Features      ❌   0% (Nicht gestartet)

GESAMT: ~75% Code, ~25% Integration
```

---

## 🏁 FAZIT

**Aktuelle Situation:**
- ✅ **Architektur:** Event-Driven MVC vollständig implementiert
- ✅ **Core:** Models, Services, Controllers alle vorhanden
- ✅ **Views:** UI-Komponenten vorhanden
- ❌ **Integration:** UI ↔ Business-Logik Verbindung fehlt!
- ❌ **Actions:** Viele User-Actions nicht implementiert

**Hauptproblem:**
Die refactorierte App hat die **Architektur**, aber nicht die **Integration**!

Die Legacy-App hatte 6 Integration-Klassen (`app_*.py`), die in der neuen App fehlen:
1. AppActions - Alle User-Actions
2. AppPaletteIntegration - Palette → Canvas
3. AppPropertiesBridge - Properties ↔ Canvas
4. AppChatIntegration - AI ↔ Canvas
5. AppShortcuts - Keyboard Shortcuts
6. AppTaskDispatch - Background Tasks

**Empfehlung:**
Fokus auf **Phase 7: Integration** (2-3 Tage), dann ist die App vollständig funktionsfähig!

---

**Erstellt:** 14. Oktober 2025  
**Nächstes Update:** Nach Phase 7 Completion
