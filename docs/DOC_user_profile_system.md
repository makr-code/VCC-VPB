# User Profile System - Dokumentation

## Überblick

Das **User Profile System** ist ein zentrales System zur Verwaltung benutzerspezifischer Einstellungen und Daten im VPB Process Designer. Alle Benutzereinstellungen werden in einer JSON-Datei gespeichert und beim nächsten Start automatisch wiederhergestellt.

**Autor:** GitHub Copilot  
**Datum:** 17. Oktober 2025  
**Version:** 1.0

---

## Features

### 1. **Benutzerspezifische Profile**
- Profile basieren auf `username@hostname`
- Automatische Erkennung des aktuellen Benutzers
- Separate Profile für verschiedene Benutzer/Rechner

### 2. **Gespeicherte Einstellungen**

#### Canvas-Ansicht
- ✅ Zoom-Level (0.1x - 5.0x)
- ✅ Pan-Position (X/Y)
- ✅ Grid-Sichtbarkeit
- ✅ Snap-to-Grid
- ✅ Ruler-Sichtbarkeit
- ✅ Minimap-Sichtbarkeit

#### UI-Präferenzen
- ✅ Sidebar-Breiten (links/rechts)
- ✅ Panel-Zustände (Palette, Properties, Chat, Minimap)
- ✅ Toolbar-Einstellungen
- ✅ Theme und Farbschema

#### Workspace
- ✅ Recent Files (max. 10)
- ✅ Letzte geöffnete Datei
- ✅ Pro-Datei-Zustände

#### Tools
- ✅ Zuletzt ausgewähltes Element
- ✅ Favoriten-Elemente
- ✅ Letzter Verbindungstyp
- ✅ Custom Keybindings

#### Chat
- ✅ Chat-Historie pro Projekt
- ✅ Automatisches Speichern
- ✅ Wiederherstellung beim Projektwechsel

---

## Architektur

### Dateistruktur

```
user_profiles/
├── <username>@<hostname>.json    # Benutzerprofil
├── mkrueger@DESKTOP-712S8LO.json # Beispiel
└── ...
```

### Profil-Schema

```json
{
  "username": "mkrueger",
  "hostname": "DESKTOP-712S8LO",
  "profile_version": "1.0",
  "last_updated": "2025-10-17T14:30:00",
  
  "canvas_view": {
    "zoom_level": 1.5,
    "pan_x": 100.0,
    "pan_y": 50.0,
    "grid_visible": true,
    "snap_to_grid": false,
    "ruler_visible": true,
    "minimap_visible": true
  },
  
  "ui_preferences": {
    "palette_panel": {
      "visible": true,
      "width": 250,
      "collapsed": false
    },
    "properties_panel": {
      "visible": true,
      "width": 250,
      "collapsed": false
    },
    "left_sidebar_width": 300,
    "right_sidebar_width": 350,
    "toolbar_icon_size": "medium",
    "show_toolbar_labels": false,
    "theme": "default",
    "color_scheme": "light"
  },
  
  "workspace": {
    "last_opened_file": "C:\\Projects\\test.vpb.json",
    "recent_files": [
      "C:\\Projects\\test.vpb.json",
      "C:\\Projects\\demo.vpb.json"
    ],
    "file_states": {}
  },
  
  "tools": {
    "last_selected_element": "task",
    "favorite_elements": ["task", "decision", "process"],
    "last_connection_type": "arrow",
    "custom_keybindings": {}
  },
  
  "chat_history": {
    "test-a1b2c3d4e5": [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
  }
}
```

---

## Verwendung

### Initialisierung

```python
from vpb.infrastructure.user_profile_manager import UserProfileManager

# Manager erstellen
manager = UserProfileManager()

# Profil laden
profile = manager.load()

print(f"Benutzer: {profile.username}@{profile.hostname}")
```

### Einstellungen ändern

```python
# Canvas-Ansicht aktualisieren
manager.update_canvas_view(
    zoom=1.5,
    pan_x=100.0,
    grid_visible=True
)

# UI-Präferenzen aktualisieren
manager.update_ui_preferences(
    left_sidebar_width=300,
    right_sidebar_width=350
)

# Recent File hinzufügen
manager.add_recent_file("C:\\Projects\\test.vpb.json")

# Chat-Historie speichern
manager.update_chat_history(
    project_id="test-a1b2c3d4e5",
    messages=[
        {"role": "user", "content": "Hallo"},
        {"role": "assistant", "content": "Hallo! Wie kann ich helfen?"}
    ]
)
```

### Profil speichern

```python
# Automatisch bei update_* Methoden
# Oder manuell:
manager.save()
```

---

## Integration in VPB App

### 1. Initialisierung (vpb_app.py)

```python
class VPBApplication:
    def __init__(self):
        # User Profile Manager initialisieren
        self.user_profile_manager = UserProfileManager()
        self.user_profile = self.user_profile_manager.load()
        
        print(f"👤 Benutzerprofil geladen: {self.user_profile.username}@{self.user_profile.hostname}")
```

### 2. Wiederherstellen beim Start

```python
def run(self):
    # Benutzerprofil wiederherstellen
    self._restore_user_profile()
    
    # Mainloop starten
    self.root.mainloop()

def _restore_user_profile(self):
    """Stellt Benutzereinstellungen aus dem Profil wieder her."""
    profile = self.user_profile
    
    # Canvas-Ansicht
    canvas.view_scale = profile.canvas_view.zoom_level
    canvas.view_tx = profile.canvas_view.pan_x
    canvas.view_ty = profile.canvas_view.pan_y
    canvas.grid_visible = profile.canvas_view.grid_visible
    
    # Sidebar-Breiten
    paned_window.sashpos(0, profile.ui_preferences.left_sidebar_width)
    
    # Recent Files
    menu_bar.update_recent_files(profile.workspace.recent_files)
```

### 3. Speichern beim Beenden

```python
def _on_exit(self):
    # Benutzerprofil speichern
    self._save_user_profile()
    
    # App beenden
    self.root.quit()

def _save_user_profile(self):
    """Speichert aktuelle Benutzereinstellungen."""
    profile = self.user_profile
    
    # Canvas-Ansicht
    profile.canvas_view.zoom_level = canvas.view_scale
    profile.canvas_view.pan_x = canvas.view_tx
    profile.canvas_view.pan_y = canvas.view_ty
    
    # Sidebar-Breiten
    profile.ui_preferences.left_sidebar_width = paned_window.sashpos(0)
    
    # Speichern
    self.user_profile_manager.save(profile)
```

### 4. Auto-Save bei Änderungen

```python
def _subscribe_to_events(self):
    # Canvas View Changed Events
    self.event_bus.subscribe("canvas:zoom_changed", self._on_canvas_view_changed)
    self.event_bus.subscribe("canvas:pan_changed", self._on_canvas_view_changed)
    self.event_bus.subscribe("canvas:grid_toggled", self._on_canvas_view_changed)

def _on_canvas_view_changed(self, data):
    """Speichert Canvas-Ansicht automatisch."""
    self.user_profile_manager.update_canvas_view(
        zoom=self.canvas.view_scale,
        pan_x=self.canvas.view_tx,
        pan_y=self.canvas.view_ty,
        grid_visible=self.canvas.grid_visible
    )
```

---

## Migration

### Bestehende Daten migrieren

```bash
# Migration-Skript ausführen
python -m vpb.infrastructure.migrate_to_user_profile
```

Das Skript migriert:
- ✅ `settings.json` → UI Preferences
- ✅ `recent_files.json` → Workspace
- ✅ `chats/` → Chat History

### Manuell migrieren

```python
from vpb.infrastructure.migrate_to_user_profile import ProfileMigration

migration = ProfileMigration()
profile = migration.migrate_all()
```

---

## API-Referenz

### UserProfileManager

#### `__init__(profile_dir="user_profiles")`
Initialisiert den Manager.

#### `load() -> UserProfile`
Lädt das Profil von Disk oder erstellt ein neues.

#### `save(profile: UserProfile = None) -> bool`
Speichert das Profil auf Disk.

#### `update_canvas_view(**kwargs) -> None`
Aktualisiert Canvas-Ansicht und speichert automatisch.

**Parameter:**
- `zoom: float` - Zoom-Level
- `pan_x: float` - Horizontale Position
- `pan_y: float` - Vertikale Position
- `grid_visible: bool` - Grid-Sichtbarkeit
- `snap_to_grid: bool` - Snap-to-Grid

#### `update_ui_preferences(**kwargs) -> None`
Aktualisiert UI-Präferenzen und speichert automatisch.

**Parameter:**
- `left_sidebar_width: int` - Linke Sidebar-Breite
- `right_sidebar_width: int` - Rechte Sidebar-Breite
- Weitere Attribute von `UIPreferences`

#### `add_recent_file(file_path: str) -> None`
Fügt eine Datei zur Recent Files Liste hinzu.

#### `get_recent_files(validate: bool = True) -> List[str]`
Gibt Recent Files zurück (optional nur existierende).

#### `update_chat_history(project_id: str, messages: List[Dict]) -> None`
Aktualisiert Chat-Historie für ein Projekt.

#### `get_chat_history(project_id: str) -> List[Dict]`
Gibt Chat-Historie für ein Projekt zurück.

---

## Events

### Publizierte Events

- `profile:loaded` - Profil wurde geladen
- `profile:saved` - Profil wurde gespeichert
- `profile:error` - Fehler beim Laden/Speichern

### Subscribed Events

- `canvas:zoom_changed` → Auto-Save
- `canvas:pan_changed` → Auto-Save
- `canvas:grid_toggled` → Auto-Save
- `ui:sidebar_resized` → Auto-Save

---

## Best Practices

### 1. **Automatisches Speichern**
Nutzen Sie die `update_*` Methoden, die automatisch speichern:

```python
# ✅ Gut - automatisches Speichern
manager.update_canvas_view(zoom=1.5)

# ❌ Schlecht - manuelles Speichern erforderlich
profile.canvas_view.zoom_level = 1.5
manager.save(profile)
```

### 2. **Event-basiertes Update**
Reagieren Sie auf Canvas-Events für Auto-Save:

```python
self.event_bus.subscribe("canvas:zoom_changed", self._on_canvas_view_changed)
```

### 3. **Validierung bei Recent Files**
Validieren Sie Dateien beim Laden:

```python
# ✅ Nur existierende Dateien
recent_files = manager.get_recent_files(validate=True)
```

### 4. **Fehlerbehandlung**
Behandeln Sie Fehler beim Laden/Speichern:

```python
try:
    profile = manager.load()
except Exception as e:
    logger.error(f"Fehler beim Laden: {e}")
    profile = UserProfile()  # Fallback
```

---

## Vorteile

✅ **Zentrale Verwaltung** - Alle Benutzereinstellungen an einem Ort  
✅ **Automatische Persistenz** - Kein manuelles Speichern erforderlich  
✅ **Benutzerspezifisch** - Profile pro Benutzer/Rechner  
✅ **Versionierung** - Profile haben Versionsnummer  
✅ **Migration** - Einfache Migration bestehender Daten  
✅ **Type-Safe** - Typsichere Dataclasses  
✅ **Event-driven** - Integration mit EventBus  
✅ **Erweiterbar** - Einfach neue Einstellungen hinzufügen  

---

## Zukünftige Erweiterungen

- [ ] Cloud-Synchronisation (Google Drive, OneDrive)
- [ ] Profile-Export/Import
- [ ] Multi-Profile Support (Work, Home, etc.)
- [ ] Settings-Sync zwischen Rechnern
- [ ] Backup/Restore von Profilen
- [ ] Profile-Vorlagen (Templates)
- [ ] Verschlüsselung sensibler Daten

---

## Troubleshooting

### Profil wird nicht gespeichert

**Symptom:** Einstellungen gehen beim Neustart verloren

**Lösung:**
1. Prüfen Sie Schreibrechte für `user_profiles/` Verzeichnis
2. Prüfen Sie Logs auf Fehler
3. Manuell speichern: `manager.save()`

### Profil ist korrupt

**Symptom:** JSON-Fehler beim Laden

**Lösung:**
1. Alte Profil-Datei löschen oder umbenennen
2. Neues Profil wird automatisch erstellt
3. Evtl. Migration erneut ausführen

### Migration schlägt fehl

**Symptom:** Alte Daten werden nicht übernommen

**Lösung:**
1. Prüfen Sie, ob `settings.json` existiert
2. Prüfen Sie, ob `recent_files.json` existiert
3. Führen Sie Migration manuell aus mit Debug-Ausgabe

---

## Zusammenfassung

Das User Profile System bietet eine **zentrale, automatische und benutzerspezifische** Verwaltung aller Einstellungen im VPB Process Designer. Es integriert sich nahtlos in die Event-driven Architecture und speichert automatisch alle relevanten Benutzereinstellungen.

**Wichtigste Features:**
- 👤 Benutzerspezifische Profile
- 💾 Automatisches Speichern
- 🔄 Event-driven Updates
- 📊 Canvas-Ansicht & UI-Präferenzen
- 💬 Chat-Historie pro Projekt
- 📁 Recent Files Management
