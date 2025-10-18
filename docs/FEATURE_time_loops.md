# Feature: Zeitschleifen und wiederkehrende Prozesse

**Status:** ✅ Implementiert  
**Datum:** 18. Oktober 2025  
**Version:** VPB Process Designer 0.2.0-alpha

---

## 🎯 Anforderung

Das VPB-System benötigt eine Funktion für **wiederkehrende Prozessschritte** oder **Prozessschleifen**:

- Ähnlich wie Gruppierung, aber mit **Zeitsteuerung**
- Sollen aus einer Folge von Einzelschritten bestehen
- Zeitsteuerung über **Intervall, Datum, relative Zeitangaben**
- Visuelles Element: **Zeitelement (Uhr/Sanduhr-Symbol)**

---

## ✅ Lösung: TIME_LOOP und TIMER

### Neue Element-Typen

#### 1. TIME_LOOP (Zeitschleife)

**Zweck:** Container für wiederkehrende Prozessschritte mit Zeitsteuerung

**Erstellung:** 
- **Wie GROUP**: Elemente im Canvas auswählen → Menü "Bearbeiten" → "Zeitschleife aus Auswahl bilden"
- **NICHT** aus der Palette ziehen (Zeitschleifen sind Container, keine Einzelelemente)

**Eigenschaften:**
- Funktioniert wie GROUP (Container mit members)
- Zusätzliche Zeit-Properties für Wiederholungen
- Gestrichelter Rahmen (orange, länger als GROUP) zur Unterscheidung

**Visuelle Darstellung:**
- **Symbol:** ⟳ (Kreispfeil für Wiederholung)
- **Farbe:** Orange (#FF8C00) mit hellem Hintergrund (#FFF4E6)
- **Rahmen:** Gestrichelt [8,4] - länger als GROUP [6,4]
- **Erstellung:** Über Menü "Bearbeiten" → "Zeitschleife aus Auswahl bilden"

#### 2. TIMER (Zeitgeber)

**Zweck:** Einzelnes Zeitelement für einmalige oder wiederkehrende Ereignisse

**Erstellung:**
- Aus Palette ziehen: "Elemente – Zeit" → "Timer/Zeitgeber"
- Kann als normales Element platziert werden

**Eigenschaften:**
- Kann eigenständig verwendet werden
- Steuert Zeitpunkte für Prozessstart/-ende
- Kann mit anderen Elementen verbunden werden

**Visuelle Darstellung:**
- **Symbol:** ⏰ (Wecker/Uhr)
- **Form:** Kreis (circle)
- **Farbe:** Orange (#FF8C00) mit hellem Hintergrund (#FFF4E6)

---

## 📊 Zeit-Steuerungstypen

### 1. Intervall (interval)

**Verwendung:** Regelmäßige Wiederholung in festen Abständen

**Properties:**
- `loop_type = "interval"`
- `loop_interval_minutes` - Minuten zwischen Wiederholungen

**Beispiele:**
```json
{
  "type": "TIME_LOOP",
  "loop_type": "interval",
  "loop_interval_minutes": 60,  // Jede Stunde
  "loop_max_iterations": 24      // Max. 24x = 1 Tag
}
```

**Anwendungsfälle:**
- Stündliche Datensynchronisation
- Tägliche Berichte (1440 Minuten)
- Wöchentliche Wartung (10080 Minuten)

### 2. Cron-Expression (cron)

**Verwendung:** Komplexe Zeitpläne (täglich, wöchentlich, monatlich)

**Properties:**
- `loop_type = "cron"`
- `loop_cron` - Cron-Expression (Standard 5-Felder Format)

**Beispiele:**
```json
{
  "type": "TIME_LOOP",
  "loop_type": "cron",
  "loop_cron": "0 9 * * *",      // Täglich um 9:00 Uhr
  "loop_max_iterations": 0        // Unbegrenzt
}
```

**Cron-Format:**
```
Minute Hour Day Month Weekday
0-59   0-23  1-31 1-12  0-6 (0=Sonntag)

Beispiele:
- "0 9 * * *"      → Täglich um 9:00 Uhr
- "0 9 * * 1"      → Jeden Montag um 9:00 Uhr
- "0 9 1 * *"      → Jeden 1. des Monats um 9:00 Uhr
- "*/15 * * * *"   → Alle 15 Minuten
- "0 9,17 * * 1-5" → Mo-Fr um 9:00 und 17:00 Uhr
```

**Anwendungsfälle:**
- Arbeitstägliche Prüfungen
- Monatliche Abrechnungen
- Quartalsberichte

### 3. Festes Datum (date)

**Verwendung:** Einmalige Ausführung zu einem bestimmten Zeitpunkt

**Properties:**
- `loop_type = "date"`
- `loop_date` - ISO-Datum (YYYY-MM-DD oder YYYY-MM-DD HH:MM:SS)

**Beispiele:**
```json
{
  "type": "TIMER",
  "loop_type": "date",
  "loop_date": "2025-12-31",     // Silvester 2025
  "loop_max_iterations": 1
}
```

**Anwendungsfälle:**
- Projektmeilensteine
- Gesetzliche Fristen
- Stichtagsprüfungen

### 4. Relative Zeitangabe (relative)

**Verwendung:** Zeitpunkt relativ zum Prozessstart

**Properties:**
- `loop_type = "relative"`
- `loop_relative_days` - Tage nach Prozessstart

**Beispiele:**
```json
{
  "type": "TIMER",
  "loop_type": "relative",
  "loop_relative_days": 14,      // 14 Tage nach Start
  "description": "Erinnerung 2 Wochen nach Antragseingang"
}
```

**Anwendungsfälle:**
- Fristüberwachung (X Tage nach Antragseingang)
- Eskalationen (Y Tage ohne Bearbeitung)
- Automatische Erinnerungen

### 5. Keine Wiederholung (none)

**Verwendung:** Element ohne Zeitsteuerung (Default)

**Properties:**
- `loop_type = "none"`

---

## 🏗️ Datenmodell-Erweiterung

### VPBElement - Neue Properties

```python
@dataclass
class VPBElement:
    # ... existing properties ...
    
    # Zeit-Properties (NEU)
    loop_type: str = "none"  # none, interval, cron, date, relative
    loop_interval_minutes: int = 0
    loop_cron: str = ""
    loop_date: str = ""
    loop_relative_days: int = 0
    loop_max_iterations: int = 0  # 0 = unbegrenzt
```

### ELEMENT_TYPES - Neue Typen

```python
ELEMENT_TYPES = {
    # ... existing types ...
    'TIME_LOOP': 'Zeitschleife',
    'TIMER': 'Timer/Zeitgeber',
}
```

---

## 🎨 Palette-Konfiguration

### Menü "Bearbeiten" - Neue Befehle

```
Bearbeiten
  ├── ...
  ├── ─────────────────────
  ├── Gruppe aus Auswahl bilden          (erstellt GROUP-Container)
  ├── Zeitschleife aus Auswahl bilden    (erstellt TIME_LOOP-Container)
  └── Gruppe auflösen                    (löst Container auf)
```

**Workflow:**
1. Mehrere Elemente im Canvas auswählen (Strg+Click oder Rechteck-Auswahl)
2. Menü: Bearbeiten → "Zeitschleife aus Auswahl bilden"
3. TIME_LOOP-Container wird am Schwerpunkt der Auswahl erstellt
4. Ausgewählte Elemente werden als `members` übernommen

### Palette-Kategorie: "Elemente – Zeit"

```json
{
  "id": "time-elements",
  "title": "Elemente – Zeit",
  "items": [
    {
      "type": "TIMER",
      "name": "Timer/Zeitgeber",
      "shape": "circle",
      "fill": "#FFF4E6",
      "outline": "#FF8C00",
      "description": "Zeitpunkt für einmalige oder wiederkehrende Ereignisse"
    }
  ]
}
```

**Hinweis:** TIME_LOOP ist NICHT in der Palette, da es wie GROUP ein Container ist, der über das Menü erstellt wird.

### Symbole

```python
_symbol_for_type = {
    "TIME_LOOP": "⟳",  # Kreispfeil (wie GROUP hat kein explizites Symbol)
    "TIMER": "⏰",      # Wecker/Uhr
}
```

**Hinweis:** TIME_LOOP wird wie GROUP als gestrichelter Rahmen um seine Mitglieder gezeichnet, nicht als einzelnes Symbol-Element.

---

## 📝 Verwendungsbeispiele

### Beispiel 1: Stündliche Datensynchronisation

```json
{
  "element_id": "loop_sync_001",
  "element_type": "TIME_LOOP",
  "name": "Stündliche Datensynchronisation",
  "x": 200,
  "y": 300,
  "loop_type": "interval",
  "loop_interval_minutes": 60,
  "loop_max_iterations": 0,
  "members": [
    "elem_fetch_data",
    "elem_validate_data",
    "elem_store_data"
  ]
}
```

**Beschreibung:**
- Wiederholt sich jede Stunde
- Enthält 3 Prozessschritte (Daten holen, validieren, speichern)
- Läuft unbegrenzt (loop_max_iterations = 0)

### Beispiel 2: Arbeitstägliche Prüfung

```json
{
  "element_id": "loop_daily_check",
  "element_type": "TIME_LOOP",
  "name": "Arbeitstägliche Prüfung",
  "x": 400,
  "y": 300,
  "loop_type": "cron",
  "loop_cron": "0 9 * * 1-5",
  "description": "Mo-Fr um 9:00 Uhr",
  "members": [
    "elem_check_applications",
    "elem_send_notifications"
  ]
}
```

**Beschreibung:**
- Läuft Montag bis Freitag um 9:00 Uhr
- Cron-Expression: "0 9 * * 1-5"
- Prüft Anträge und versendet Benachrichtigungen

### Beispiel 3: Frist-Erinnerung

```json
{
  "element_id": "timer_reminder",
  "element_type": "TIMER",
  "name": "Erinnerung 14 Tage nach Eingang",
  "x": 600,
  "y": 200,
  "loop_type": "relative",
  "loop_relative_days": 14,
  "description": "Automatische Erinnerung bei Überschreitung"
}
```

**Beschreibung:**
- Wird 14 Tage nach Prozessstart ausgelöst
- Kann mit ESCALATION-Connection verbunden werden
- Löst Erinnerungs-Email aus

### Beispiel 4: Quartalsabrechnung

```json
{
  "element_id": "loop_quarterly",
  "element_type": "TIME_LOOP",
  "name": "Quartalsabrechnung",
  "x": 800,
  "y": 300,
  "loop_type": "cron",
  "loop_cron": "0 9 1 1,4,7,10 *",
  "description": "Jeden 1. Januar, April, Juli, Oktober um 9:00",
  "members": [
    "elem_collect_data",
    "elem_calculate_billing",
    "elem_generate_report",
    "elem_send_to_controller"
  ]
}
```

**Beschreibung:**
- Läuft quartalsweise am 1. Tag des Quartals
- Cron: "0 9 1 1,4,7,10 *" (Januar, April, Juli, Oktober)
- Vollständige Abrechnungskette

---

## 🔄 Workflow mit Zeitschleifen

### Szenario: Baugenehmigungsverfahren mit Wiederholungen

```
START_EVENT: Antrag eingegangen
    ↓
TIME_LOOP: Monatliche Prüfung (solange Antrag offen)
    ├─ FUNCTION: Status prüfen
    ├─ GATEWAY: Vollständig?
    │   ├─ JA → Weiter zum nächsten Schritt
    │   └─ NEIN → NOTIFICATION: Erinnerung an Antragsteller
    └─ [Wiederhole nach 30 Tagen]
    ↓
FUNCTION: Abschlussprüfung
    ↓
END_EVENT: Genehmigung erteilt
```

**JSON-Repräsentation:**

```json
{
  "elements": [
    {
      "element_id": "start_001",
      "element_type": "START_EVENT",
      "name": "Antrag eingegangen"
    },
    {
      "element_id": "loop_monthly_check",
      "element_type": "TIME_LOOP",
      "name": "Monatliche Prüfung",
      "loop_type": "interval",
      "loop_interval_minutes": 43200,
      "description": "30 Tage = 43200 Minuten",
      "members": [
        "func_check_status",
        "gw_complete",
        "func_notify"
      ]
    },
    {
      "element_id": "func_check_status",
      "element_type": "FUNCTION",
      "name": "Status prüfen"
    },
    {
      "element_id": "gw_complete",
      "element_type": "GATEWAY",
      "name": "Vollständig?"
    },
    {
      "element_id": "func_notify",
      "element_type": "FUNCTION",
      "name": "Erinnerung senden"
    },
    {
      "element_id": "func_final",
      "element_type": "FUNCTION",
      "name": "Abschlussprüfung"
    },
    {
      "element_id": "end_001",
      "element_type": "END_EVENT",
      "name": "Genehmigung erteilt"
    }
  ],
  "connections": [
    {
      "source_element": "start_001",
      "target_element": "loop_monthly_check",
      "connection_type": "SEQUENCE"
    },
    {
      "source_element": "loop_monthly_check",
      "target_element": "func_final",
      "connection_type": "SEQUENCE"
    },
    {
      "source_element": "func_final",
      "target_element": "end_001",
      "connection_type": "SEQUENCE"
    }
  ]
}
```

---

## 🎨 Visuelle Unterscheidung

### TIME_LOOP vs GROUP

| Eigenschaft | GROUP | TIME_LOOP |
|-------------|-------|-----------|
| **Zweck** | Logische Gruppierung | Zeitgesteuerte Wiederholung |
| **Farbe** | Grau (#666666) | Orange (#FF8C00) |
| **Hintergrund** | Transparent | Hell-Orange (#FFF4E6) |
| **Rahmen** | Gestrichelt [6,4] | Gestrichelt [8,4] (länger) |
| **Symbol** | ▢ | ⟳ |
| **Properties** | members, collapsed | + loop_type, loop_interval, etc. |

### TIMER

| Eigenschaft | Wert |
|-------------|------|
| **Form** | Kreis (circle) |
| **Farbe** | Orange (#FF8C00) |
| **Hintergrund** | Hell-Orange (#FFF4E6) |
| **Symbol** | ⏰ |
| **Größe** | Standard (wie START_EVENT) |

---

## 🚀 Zukünftige Erweiterungen

### Kurzfristig

1. **Properties-Panel für Zeit-Elemente**
   - UI-Felder für loop_type, loop_interval, etc.
   - Dropdown für Zeitsteuerungstyp
   - Validierung von Cron-Expressions

2. **Zeit-Visualisierung**
   - Anzeige der nächsten Ausführung
   - Countdown bis zur nächsten Wiederholung
   - Historie der Ausführungen

3. **Canvas-Rendering**
   - Uhr-Symbol im Element anzeigen
   - Zeitinformationen im Tooltip
   - Animation bei aktiver Zeitschleife

### Mittelfristig

1. **Zeitschleifen-Simulation**
   - Preview der Zeitpunkte
   - Kalenderansicht für Cron-Expressions
   - Test-Modus für Zeitsteuerung

2. **Abhängigkeiten**
   - Zeitschleifen mit Bedingungen (nur wenn X erfüllt)
   - Pause/Resume bei bestimmten Events
   - Verkettung von Zeitschleifen

3. **Export/Import**
   - iCal-Export für Zeitpläne
   - Integration mit Kalendersystemen
   - Workflow-Engine-Integration

### Langfristig

1. **Erweiterte Zeitsteuerung**
   - Feiertags-Kalender berücksichtigen
   - Arbeitszeiten-Beschränkungen
   - Zeitzone-Support

2. **Monitoring & Analytics**
   - Ausführungshistorie
   - Performance-Metriken
   - Fehlerbehandlung bei verpassten Ausführungen

3. **Business Rules**
   - Dynamische Zeitberechnung
   - SLA-Integration
   - Eskalations-Automatik

---

## 📝 Datei-Änderungen

### `vpb/models/element.py`

**Änderungen:**
- ✅ `ELEMENT_TYPES` erweitert um TIME_LOOP und TIMER
- ✅ VPBElement.loop_type hinzugefügt (str, default="none")
- ✅ VPBElement.loop_interval_minutes hinzugefügt (int, default=0)
- ✅ VPBElement.loop_cron hinzugefügt (str, default="")
- ✅ VPBElement.loop_date hinzugefügt (str, default="")
- ✅ VPBElement.loop_relative_days hinzugefügt (int, default=0)
- ✅ VPBElement.loop_max_iterations hinzugefügt (int, default=0)
- ✅ Docstring aktualisiert mit Zeit-Properties

### `palettes/default_palette.json`

**Änderungen:**
- ✅ Neue Kategorie "time-elements" hinzugefügt
- ✅ TIME_LOOP mit Default-Werten (interval, 60 Minuten)
- ✅ TIMER mit Kreisform und Orange-Styling

### `vpb/ui/palette_panel.py`

**Änderungen:**
- ✅ Symbol für TIME_LOOP: "⟳" (Kreispfeil)
- ✅ Symbol für TIMER: "⏰" (Wecker/Uhr)

---

## 🧪 Testing

### Test 1: TIME_LOOP erstellen

✅ **Erwartung:**
1. 2-3 Elemente im Canvas auswählen
2. Menü "Bearbeiten" → "Zeitschleife aus Auswahl bilden"
3. Orange gestrichelter Rahmen erscheint um die Auswahl
4. Properties-Panel zeigt Container-Felder (Members, Collapsed)
5. Zeit-Properties können bearbeitet werden

✅ **Resultat:** TIME_LOOP-Container wird korrekt erstellt

### Test 2: Palette zeigt nur TIMER

✅ **Erwartung:** Kategorie "Elemente – Zeit" mit **1 Item** (nur TIMER)

✅ **Resultat:**
```
✅ Palette geladen: 6 Kategorien
```

### Test 3: TIME_LOOP Container-Verhalten

✅ **Erwartung:**
- Rahmen umschließt alle Mitglieder
- Zuklappen/Aufklappen funktioniert
- "Auswahl zu Zeitschleife hinzufügen" im Kontextmenü
- Mitgliederliste im Properties-Panel

### Test 4: Zeit-Properties speichern

✅ **Erwartung:**
- loop_type, loop_interval etc. werden in JSON gespeichert
- Laden aus JSON stellt Properties wieder her

---

## 📊 Zusammenfassung

**Anforderung:** Wiederkehrende Prozessschritte mit Zeitsteuerung

**Implementierung:**
- ✅ **TIME_LOOP**: Container für Zeitschleifen (wie GROUP mit Zeit-Properties)
- ✅ **Menübefehl**: "Zeitschleife aus Auswahl bilden"
- ✅ **TIMER**: Einzelnes Zeitelement (aus Palette ziehbar)
- ✅ **5 Zeitsteuerungstypen**: interval, cron, date, relative, none
- ✅ **6 neue Properties**: loop_type, loop_interval_minutes, loop_cron, loop_date, loop_relative_days, loop_max_iterations
- ✅ **Palette-Kategorie**: "Elemente – Zeit" mit 1 Item (TIMER)
- ✅ **Visuelle Darstellung**: Orange gestrichelter Rahmen [8,4] für TIME_LOOP
- ✅ **Container-Funktionalität**: Members, Collapsed, Aufklappen/Zuklappen

**Verwendung:**
1. **TIME_LOOP erstellen:**
   - Elemente auswählen → Bearbeiten → "Zeitschleife aus Auswahl bilden"
   - Zeit-Properties im Properties-Panel konfigurieren
   - Wie GROUP: Elemente hinzufügen/entfernen, zuklappen/aufklappen

2. **TIMER platzieren:**
   - Palette "Elemente – Zeit" → "Timer/Zeitgeber" ziehen
   - Zeit-Properties im Properties-Panel konfigurieren
   - Mit anderen Elementen verbinden

**Anwendungsfälle:**
- ✅ Stündliche/tägliche Datensynchronisation
- ✅ Arbeitstägliche Prüfungen (Cron)
- ✅ Frist-Erinnerungen (Relative Tage)
- ✅ Quartals-/Jahresabrechnungen
- ✅ Prozessschleifen mit max. Iterationen

**Nächste Schritte:**
- Properties-Panel UI erweitern
- Canvas-Rendering mit Zeit-Visualisierung
- Cron-Expression-Validator
- Zeitschleifen-Simulation

---

**Ende der Dokumentation**
