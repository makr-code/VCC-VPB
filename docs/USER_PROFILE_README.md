# Benutzereinstellungen - User Profile System

## Was ist das User Profile System?

Das **User Profile System** speichert alle Ihre persönlichen Einstellungen und Daten automatisch, sodass diese beim nächsten Start wiederhergestellt werden.

## Was wird gespeichert?

### ✅ Canvas-Ansicht
- **Zoom-Level** - Ihre bevorzugte Vergrößerung
- **Position** - Wo Sie zuletzt im Canvas waren
- **Grid** - Grid an/aus
- **Snap-to-Grid** - Einrasten aktiviert/deaktiviert

### ✅ UI-Layout
- **Sidebar-Breiten** - Links und rechts
- **Panel-Zustände** - Welche Panels geöffnet sind
- **Fenster-Position** - Wo das Fenster war

### ✅ Dateien
- **Recent Files** - Zuletzt geöffnete Dateien (max. 10)
- **Letzte Datei** - Automatisch wieder öffnen (optional)

### ✅ Chat
- **Chat-Historie** - Pro Projekt gespeichert
- **Automatische Wiederherstellung** - Beim Projekt-Wechsel

### ✅ Werkzeuge
- **Favoriten** - Ihre bevorzugten Elemente
- **Letzte Auswahl** - Zuletzt verwendetes Element

## Wo werden die Daten gespeichert?

```
VPB/
└── user_profiles/
    └── <ihr-name>@<ihr-rechner>.json
```

**Beispiel:** `user_profiles/mkrueger@DESKTOP-712S8LO.json`

## Automatisches Speichern

Das System speichert **automatisch**:
- ✅ Beim Beenden der Anwendung
- ✅ Bei Änderungen der Canvas-Ansicht (Zoom, Pan)
- ✅ Bei Änderungen der Sidebar-Breiten
- ✅ Beim Öffnen von Dateien
- ✅ Bei Chat-Nachrichten

**Sie müssen nichts manuell speichern!**

## Migration von alten Daten

Beim ersten Start werden Ihre alten Daten **automatisch migriert**:
- `settings.json` → UI-Einstellungen
- `recent_files.json` → Recent Files
- `chats/` → Chat-Historie

### Manuelle Migration

Falls nötig, können Sie die Migration manuell starten:

```bash
python -m vpb.infrastructure.migrate_to_user_profile
```

## Profil zurücksetzen

### Option 1: Datei löschen

Löschen Sie einfach Ihre Profil-Datei:
```
user_profiles/<ihr-name>@<ihr-rechner>.json
```

Beim nächsten Start wird ein neues Profil mit Standard-Einstellungen erstellt.

### Option 2: Profil umbenennen

Benennen Sie die Datei um (als Backup):
```
user_profiles/<ihr-name>@<ihr-rechner>.json.bak
```

## Mehrere Profile

Sie können mehrere Profile haben (z.B. für verschiedene Rechner):
- `mkrueger@LAPTOP.json` - Laptop-Profil
- `mkrueger@DESKTOP.json` - Desktop-Profil

Jedes Profil wird **automatisch** basierend auf Ihrem Rechner-Namen erstellt.

## Datenschutz

- ✅ **Lokal gespeichert** - Keine Cloud-Sync
- ✅ **Benutzerspezifisch** - Pro Benutzer/Rechner
- ✅ **Klartext JSON** - Einfach lesbar und editierbar
- ✅ **Keine sensiblen Daten** - Nur UI-Einstellungen

## Troubleshooting

### Einstellungen werden nicht gespeichert

1. **Prüfen Sie Schreibrechte**: Das Verzeichnis `user_profiles/` muss beschreibbar sein
2. **Schauen Sie in die Logs**: Fehlermeldungen werden in der Konsole angezeigt
3. **Profil-Datei prüfen**: Existiert die JSON-Datei?

### Profil ist korrupt

**Symptom:** Fehler beim Laden

**Lösung:**
1. Profil-Datei löschen oder umbenennen
2. Neues Profil wird automatisch erstellt
3. Migration erneut ausführen

### Recent Files werden nicht angezeigt

**Symptom:** Menü ist leer

**Lösung:**
1. Öffnen Sie eine Datei
2. Sie wird automatisch zur Liste hinzugefügt
3. Beim nächsten Start ist sie im Menü

## Beispiel-Profil

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
    "snap_to_grid": false
  },
  
  "ui_preferences": {
    "left_sidebar_width": 300,
    "right_sidebar_width": 350
  },
  
  "workspace": {
    "recent_files": [
      "C:\\Projects\\test.vpb.json",
      "C:\\Projects\\demo.vpb.json"
    ]
  }
}
```

## Support

Bei Problemen:
1. Schauen Sie in die [vollständige Dokumentation](docs/DOC_user_profile_system.md)
2. Prüfen Sie die Konsolen-Ausgabe
3. Erstellen Sie ein Issue auf GitHub

---

**Viel Erfolg mit dem VPB Process Designer! 🚀**
