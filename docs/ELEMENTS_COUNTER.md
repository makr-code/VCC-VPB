# 🔢 COUNTER Element - Vollständige Dokumentation

**Version:** 1.0  
**Status:** Production-Ready ✅  
**Implementiert:** VPB Process Designer 0.2.1-alpha  
**Datum:** 18. Oktober 2025

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Counter-Typen](#counter-typen)
3. [Eigenschaften-Referenz](#eigenschaften-referenz)
4. [Verwendung im Designer](#verwendung-im-designer)
5. [Verwendungsbeispiele](#verwendungsbeispiele)
6. [Validierungsregeln](#validierungsregeln)
7. [Best Practices](#best-practices)
8. [API & JSON-Struktur](#api--json-struktur)
9. [SPS-Hintergrund](#sps-hintergrund)
10. [FAQ](#faq)

---

## Übersicht

### Was ist ein Counter?

Ein **Counter (Zähler)** ist ein Prozess-Element, das Durchläufe oder Ereignisse zählt. Es ist inspiriert von **SPS-Zählern** (Speicherprogrammierbare Steuerung) und dient zur Steuerung von Wiederholungen, Eskalationen und Schwellenwerten in Verwaltungsprozessen.

### Wann verwenden?

Verwenden Sie einen Counter, wenn Sie:

- ✅ **Wiederholungen begrenzen** möchten (z.B. max. 3 Mahnungen)
- ✅ **Eskalationen auslösen** möchten (z.B. nach 5 Versuchen an Vorgesetzten)
- ✅ **Versuche zählen** möchten (z.B. fehlgeschlagene Zustellungen)
- ✅ **Durchläufe kontrollieren** möchten (z.B. Freigabe-Runden)
- ✅ **Schwellenwerte überwachen** möchten (z.B. Antragspositionen)

### Vorteile gegenüber manueller Zählung

| Counter-Element | Manuelle Lösung (Variablen) |
|-----------------|------------------------------|
| ✅ Visuell sichtbar im Prozess | ❌ Unsichtbare Variablen |
| ✅ Automatische Validierung | ❌ Manuelle Prüfung nötig |
| ✅ Integrierte Eskalations-Logik | ❌ Komplexe Gateway-Ketten |
| ✅ Typsicher (UP/DOWN/UP_DOWN) | ❌ Fehleranfällige Logik |
| ✅ Reset-Funktion eingebaut | ❌ Manuelles Zurücksetzen |

---

## Counter-Typen

### 1. UP Counter (Aufwärtszähler) ⬆️

**Zählt von Start-Wert bis Maximum**

```
Start: 0 → 1 → 2 → 3 → MAX erreicht!
```

**Verwendung:**
- Wiederholungszähler (von 0 beginnend)
- Versuche zählen (1., 2., 3. Versuch)
- Durchläufe zählen (Iteration 1, 2, 3...)

**Beispiel:** Mahnungsprozess
```
Startwert: 0
Maximum: 3
Bei jedem Durchlauf: 0 → 1 → 2 → 3 → Inkasso
```

### 2. DOWN Counter (Abwärtszähler) ⬇️

**Zählt von Start-Wert bis Null**

```
Start: 10 → 9 → 8 → ... → 1 → 0 → Fertig!
```

**Verwendung:**
- Restliche Versuche anzeigen
- Countdown-Funktionen
- Kontingente verbrauchen

**Beispiel:** Freigabe-Kontingent
```
Startwert: 5 (5 Freigaben verfügbar)
Bei jedem Durchlauf: 5 → 4 → 3 → 2 → 1 → 0 → Kontingent aufgebraucht
```

### 3. UP_DOWN Counter (Bidirektionaler Zähler) ⬍⬍

**Kann sowohl hoch- als auch runterzählen**

```
Start: 5 → 6 → 7 → 6 → 5 → 4 → 3 ...
```

**Verwendung:**
- Warteschlangen (Personen hinzufügen/entfernen)
- Lagerbestände (Zu-/Abgang)
- Dynamische Kontingente

**Beispiel:** Antragsbearbeitung mit Rückläufen
```
Startwert: 0
Maximum: 10
+1 bei neuem Antrag, -1 bei Erledigung
```

### Vergleichstabelle

| Eigenschaft | UP | DOWN | UP_DOWN |
|-------------|----|----- |---------|
| **Richtung** | Nur aufwärts | Nur abwärts | Beide |
| **Start** | 0 oder custom | Custom Start-Wert | 0 oder custom |
| **Ende** | Maximum erreicht | 0 erreicht | Maximum oder 0 |
| **Gültiger Bereich** | `[start, max]` | `[0, start]` | `[0, max]` |
| **Typische Anwendung** | Wiederholungen zählen | Kontingent verbrauchen | Warteschlangen |

---

## Eigenschaften-Referenz

### Counter-Typ (`counter_type`)

**Typ:** String (Dropdown)  
**Werte:** `"UP"`, `"DOWN"`, `"UP_DOWN"`  
**Standard:** `"UP"`

Bestimmt die Zählrichtung des Counters.

### Start-Wert (`counter_start_value`)

**Typ:** Integer (0-10000)  
**Standard:** `0`

Der Anfangswert des Counters:
- **UP:** Oft 0 (zählt ab 0 hoch)
- **DOWN:** Kontingent-Größe (z.B. 5 Versuche)
- **UP_DOWN:** Oft 0 (aber flexibel)

### Maximum (`counter_max_value`)

**Typ:** Integer (1-10000)  
**Standard:** `100`

Der maximale Wert:
- **UP:** Schwellenwert für Eskalation
- **DOWN:** Wird ignoriert (zählt bis 0)
- **UP_DOWN:** Obere Grenze

**Validierung:** Muss größer als `counter_start_value` sein (ERROR)

### Aktueller Wert (`counter_current_value`)

**Typ:** Integer (read-only in UI)  
**Standard:** `0`

Der momentane Zählstand:
- Wird automatisch aktualisiert beim Prozessdurchlauf
- Kann programmatisch gesetzt werden (z.B. beim Laden)
- Wird bei `clone()` auf `start_value` zurückgesetzt

**Validierung:** Sollte im gültigen Bereich liegen (WARNING bei Abweichung)

### Reset bei Maximum (`counter_reset_on_max`)

**Typ:** Boolean (Checkbox)  
**Standard:** `False`

Automatisches Zurücksetzen bei Erreichen des Maximums:
- **True:** Counter springt auf `start_value` zurück → **Loop-Funktion** 🔁
- **False:** Counter bleibt bei Maximum stehen

**Verwendung:**
- ✅ **True:** Für endlos laufende Prozesse (z.B. Monitoring)
- ✅ **False:** Für begrenzte Wiederholungen (z.B. max. 3 Mahnungen)

### Element bei Maximum (`counter_on_max_reached`)

**Typ:** String (Element-ID)  
**Standard:** `""` (leer)

Element-ID, das bei Erreichen des Maximums angesprungen wird:
- Ermöglicht **Eskalations-Logik** ohne zusätzliche Gateways
- Alternative zu normalen ausgehenden Verbindungen
- Wird **zusätzlich** zu normalen Verbindungen ausgeführt

**Beispiel:**
```
counter_on_max_reached: "inkasso_001"
→ Bei max=3 erreicht: Springe direkt zu Inkasso-Element
```

**Validierung:** Element-ID muss im Dokument existieren (ERROR bei ungültiger ID)

---

## Verwendung im Designer

### 1. Counter hinzufügen

1. **Palette öffnen** (linke Sidebar)
2. **Kategorie "Elemente – Logik"** 🔢 aufklappen
3. **"Zähler (Counter)"** auswählen
4. **Auf Canvas klicken** zum Platzieren

**Visual:**
- **Form:** Diamant (Raute) ◇
- **Farbe:** Hellblau (#E8F4F8) mit blauem Rahmen (#2196F3)
- **Anzeige:** `current/max` (z.B. "0/3") + Counter-Typ ("🔢 UP")

### 2. Counter konfigurieren

1. **Counter-Element auswählen** (Klick auf Canvas)
2. **Properties Panel** öffnet sich rechts
3. **Counter-Section** 🔢 enthält:

| Feld | Beschreibung |
|------|--------------|
| **Counter-Typ** | Dropdown: UP / DOWN / UP_DOWN |
| **Startwert** | Spinbox: 0-10000 |
| **Maximum** | Spinbox: 1-10000 |
| **Aktueller Wert** | Read-only Label (blau) |
| **Reset bei Max** | Checkbox |
| **Element bei Max** | Entry: Element-ID eingeben |

4. **Übernehmen-Button** klicken zum Speichern

### 3. Counter verbinden

**Eingehende Verbindungen:**
- Mindestens 1 Verbindung empfohlen (sonst WARNING)
- Jeder Durchlauf erhöht/verringert den Counter

**Ausgehende Verbindungen:**
- Normale Sequence-Verbindung: Immer
- `on_max_reached`: Nur bei Maximum

**Typisches Pattern:**
```
[Funktion] → [Counter] → [Gateway]
                ↓
          (on_max_reached)
                ↓
          [Eskalation]
```

### 4. Counter validieren

**Menü:** Prozess → Validieren (oder Strg+Shift+V)

**Prüft:**
- ✅ Maximum > Start
- ✅ Current in gültigem Bereich
- ✅ on_max_reached Element existiert
- ✅ Hat eingehende Verbindungen
- ✅ Hat ausgehende Verbindungen oder on_max_reached

---

## Verwendungsbeispiele

### Beispiel 1: Mahnungsprozess mit Eskalation 📧

**Szenario:** Automatischer Mahnversand mit max. 3 Mahnungen, danach Inkasso

**Prozess-Struktur:**
```
START
  ↓
[Prüfe Zahlung] → bezahlt? → JA → END
  ↓ NEIN
[Counter: Mahnungen] (UP, max=3)
  ↓
[Mahnung senden]
  ↓
[Timer: 14 Tage]
  ↓
[Gateway: Bezahlt?] → JA → END
  ↓ NEIN
[Loop zurück zu Counter]

Counter bei max=3:
  ↓ (on_max_reached: "inkasso_001")
[Inkasso beauftragen] → END
```

**Counter-Konfiguration:**
```json
{
  "element_id": "counter_mahnung",
  "element_type": "COUNTER",
  "name": "Mahnungs-Zähler",
  "counter_type": "UP",
  "counter_start_value": 0,
  "counter_max_value": 3,
  "counter_current_value": 0,
  "counter_reset_on_max": false,
  "counter_on_max_reached": "inkasso_001"
}
```

**Ablauf:**
1. Zahlung nicht eingegangen → Counter: 0 → 1
2. 14 Tage warten → Noch nicht bezahlt → Counter: 1 → 2
3. 14 Tage warten → Noch nicht bezahlt → Counter: 2 → 3
4. Counter erreicht max=3 → Springt zu `inkasso_001`
5. Inkasso-Prozess startet

**Siehe auch:** `processes/example_counter_mahnung.vpb.json`

---

### Beispiel 2: Freigabe-Workflow mit begrenzten Versuchen ✅

**Szenario:** Antrag muss freigegeben werden, max. 5 Versuche

**Counter-Konfiguration:**
```json
{
  "counter_type": "DOWN",
  "counter_start_value": 5,
  "counter_max_value": 10,
  "counter_current_value": 5,
  "counter_reset_on_max": false,
  "counter_on_max_reached": "ablehnung_001"
}
```

**Ablauf:**
- Start: 5 Versuche verfügbar
- Freigabe angefordert → Counter: 5 → 4
- Freigabe abgelehnt → Counter: 4 → 3
- ...
- Counter erreicht 0 → `ablehnung_001` wird aufgerufen

---

### Beispiel 3: Monitoring mit endloser Schleife 🔁

**Szenario:** Regelmäßige Prüfung mit Report alle 10 Durchläufe

**Counter-Konfiguration:**
```json
{
  "counter_type": "UP",
  "counter_start_value": 0,
  "counter_max_value": 10,
  "counter_current_value": 0,
  "counter_reset_on_max": true,
  "counter_on_max_reached": "report_001"
}
```

**Ablauf:**
- Durchlauf 1-9: Normal weiterlaufen
- Durchlauf 10: Counter=10 → `report_001` (Report erstellen)
- Counter reset auf 0 → Schleife startet von vorne

**Hinweis:** ValidationService empfiehlt `reset_on_max=true` für Loops (INFO-Message)

---

### Beispiel 4: Dynamische Warteschlange (UP_DOWN) 📊

**Szenario:** Anträge in Bearbeitung (max. 100 gleichzeitig)

**Counter-Konfiguration:**
```json
{
  "counter_type": "UP_DOWN",
  "counter_start_value": 0,
  "counter_max_value": 100,
  "counter_current_value": 42,
  "counter_reset_on_max": false,
  "counter_on_max_reached": "warteschlange_voll_001"
}
```

**Ablauf:**
- Neuer Antrag → Counter +1
- Antrag erledigt → Counter -1
- Counter bei 100 → Neue Anträge in Warteschlange (`warteschlange_voll_001`)

---

## Validierungsregeln

Der Counter wird automatisch validiert beim Speichern oder Menü → Validieren.

### ❌ ERROR-Regeln (blockieren Ausführung)

| Regel | Prüfung | Fehlermeldung | Lösung |
|-------|---------|---------------|--------|
| **Max > Start** | `counter_max_value > counter_start_value` | "Counter maximum (X) must be greater than start (Y)" | Maximum erhöhen oder Start verringern |
| **on_max_reached existiert** | Element-ID in Dokument vorhanden | "Target element 'X' for on_max_reached does not exist" | Gültige Element-ID eingeben oder leer lassen |
| **Gültiger Counter-Typ** | Typ ist UP/DOWN/UP_DOWN | "Invalid counter_type 'X'. Must be one of: UP, DOWN, UP_DOWN" | Gültigen Typ wählen |

### ⚠️ WARNING-Regeln (sollten behoben werden)

| Regel | Prüfung | Warnung | Empfehlung |
|-------|---------|---------|------------|
| **Current in Range** | `counter_current_value` im gültigen Bereich | "Current value (X) is outside valid range [Y, Z]" | Wert korrigieren |
| **Hat eingehende Verbindungen** | Mindestens 1 Incoming | "Counter has no incoming connections (will never be incremented)" | Verbindung hinzufügen |
| **Hat ausgehende Verbindungen** | Mindestens 1 Outgoing oder on_max_reached | "Counter has no outgoing connections and no on_max_reached target" | Verbindung oder Eskalations-Ziel hinzufügen |

### ℹ️ INFO-Regeln (Vorschläge)

| Regel | Bedingung | Info-Nachricht |
|-------|-----------|----------------|
| **Loop ohne Reset** | Incoming + Outgoing + !reset_on_max | "Counter in loop without reset_on_max" → Suggestion: "Consider enabling reset_on_max for continuous counting" |

### Gültige Bereiche nach Typ

| Counter-Typ | Gültiger Bereich für `current_value` |
|-------------|--------------------------------------|
| **UP** | `[counter_start_value, counter_max_value]` |
| **DOWN** | `[0, counter_start_value]` |
| **UP_DOWN** | `[0, counter_max_value]` |

**Beispiele:**
- UP (start=0, max=3): Valid = 0, 1, 2, 3
- DOWN (start=5, max=10): Valid = 0, 1, 2, 3, 4, 5
- UP_DOWN (start=0, max=100): Valid = 0-100

---

## Best Practices

### ✅ DO: Empfohlene Patterns

#### 1. Klare Benennung
```
✅ "Mahnungs-Zähler"
✅ "Freigabe-Versuche"
✅ "Warteschlangen-Länge"

❌ "Counter 1"
❌ "Zähler"
❌ "test"
```

#### 2. Reset bei Loops aktivieren
```
Endlos-Prozess mit Counter?
→ counter_reset_on_max = true ✅
```

#### 3. Eskalation über on_max_reached
```
Max erreicht → Spezielle Aktion?
→ counter_on_max_reached = "eskalation_element_id" ✅

Vermeidet komplexe Gateway-Logik!
```

#### 4. Start-Wert = 0 für UP Counter
```
UP Counter: Wiederholungen zählen
→ counter_start_value = 0 ✅

Nutzer versteht: "1. Versuch", "2. Versuch", ...
```

#### 5. DOWN Counter für verbleibende Kontingente
```
"5 Versuche übrig" → DOWN Counter ✅
counter_start_value = 5
Bei 0 → Kontingent aufgebraucht
```

### ❌ DON'T: Häufige Fehler

#### 1. Max ≤ Start
```
❌ counter_start_value = 10
   counter_max_value = 5
   → ERROR beim Validieren!

✅ counter_start_value = 0
   counter_max_value = 10
```

#### 2. Keine Verbindungen
```
❌ Counter isoliert im Prozess
   → Wird nie inkrementiert!

✅ Mindestens 1 eingehende Verbindung
```

#### 3. Kein Eskalations-Ziel
```
❌ counter_max_value = 3
   counter_on_max_reached = ""
   Keine Outgoing Connection
   → Counter endet im Nichts!

✅ Entweder on_max_reached ODER Outgoing Connection
```

#### 4. Loop ohne Reset
```
❌ Endlos-Prozess mit Counter
   counter_reset_on_max = false
   → Counter bleibt bei Max hängen!

✅ counter_reset_on_max = true für Loops
```

#### 5. Falsche Counter-Typen mischen
```
❌ UP Counter mit countdown-Logik verwenden
❌ DOWN Counter für Aufwärtszählung

✅ Richtigen Typ für Anwendungsfall wählen
```

---

## API & JSON-Struktur

### JSON-Repräsentation

```json
{
  "element_id": "counter_001",
  "element_type": "COUNTER",
  "name": "Mahnungs-Zähler",
  "x": 250,
  "y": 150,
  "shape": "diamond",
  "fill": "#E8F4F8",
  "outline": "#2196F3",
  
  "counter_type": "UP",
  "counter_start_value": 0,
  "counter_max_value": 3,
  "counter_current_value": 0,
  "counter_reset_on_max": false,
  "counter_on_max_reached": "inkasso_001"
}
```

### Programmgesteuerter Zugriff (Python)

#### Counter erstellen
```python
from vpb.models.element import VPBElement

counter = VPBElement(
    element_id="counter_001",
    element_type="COUNTER",
    name="Test Counter",
    x=100,
    y=100,
    counter_type="UP",
    counter_start_value=0,
    counter_max_value=3,
    counter_current_value=0,
    counter_reset_on_max=False,
    counter_on_max_reached=""
)
```

#### Counter-Wert ändern
```python
# Inkrementieren
counter.counter_current_value += 1

# Dekrementieren
counter.counter_current_value -= 1

# Maximum prüfen
if counter.counter_current_value >= counter.counter_max_value:
    print("Maximum erreicht!")
    if counter.counter_on_max_reached:
        # Eskalation auslösen
        escalate_to(counter.counter_on_max_reached)
```

#### Counter validieren
```python
from vpb.services.validation_service import ValidationService

service = ValidationService()
result = service.validate_document(document)

# Fehler anzeigen
for error in result.errors:
    if error.element_id == counter.element_id:
        print(f"ERROR: {error.message}")
```

#### Counter klonen
```python
# Klonen setzt current_value auf start_value zurück
cloned = counter.clone()
print(cloned.counter_current_value)  # → start_value (0)
```

### REST-API (falls vorhanden)

```http
GET /api/v1/processes/{process_id}/elements/{element_id}
→ Gibt Counter-Element mit allen Eigenschaften zurück

PUT /api/v1/processes/{process_id}/elements/{element_id}
Content-Type: application/json
{
  "counter_current_value": 2
}
→ Aktualisiert Counter-Wert
```

---

## SPS-Hintergrund

### Was ist ein SPS-Zähler?

In der **SPS-Technik** (Speicherprogrammierbare Steuerung) sind **Zähler** fundamentale Bausteine:

- **CTU** (Count Up): Aufwärtszähler
- **CTD** (Count Down): Abwärtszähler
- **CTUD** (Count Up/Down): Bidirektionaler Zähler

### SPS → VPB Mapping

| SPS-Konzept | VPB Counter | Beschreibung |
|-------------|-------------|--------------|
| **CTU** | `counter_type: "UP"` | Zählt Ereignisse bis Maximum |
| **CTD** | `counter_type: "DOWN"` | Zählt Kontingent runter bis 0 |
| **CTUD** | `counter_type: "UP_DOWN"` | Flexibles Zählen in beide Richtungen |
| **Preset (PV)** | `counter_start_value` | Startwert des Zählers |
| **Limit** | `counter_max_value` | Schwellenwert für Eskalation |
| **Current Value (CV)** | `counter_current_value` | Aktueller Zählstand |
| **Reset** | `counter_reset_on_max` | Automatisches Zurücksetzen |
| **Output** | `counter_on_max_reached` | Ausgang bei Limit-Erreichen |

### Vorteile der SPS-Inspiration

✅ **Bewährte Konzepte**: Seit Jahrzehnten in Industrie-Steuerungen eingesetzt  
✅ **Einfach verständlich**: Klare Up/Down-Semantik  
✅ **Robust**: Typ-sichere Zähllogik  
✅ **Flexibel**: 3 Typen decken alle Anwendungsfälle ab

### Warum Counter für Verwaltungsprozesse?

Verwaltungsprozesse haben oft **iterative Strukturen**:

- 📧 **Mahnungen**: Max. X Mahnungen vor Eskalation
- ✅ **Freigaben**: Max. Y Ablehnungen möglich
- 🔄 **Wiederholungen**: Prozess läuft bis Schwellenwert
- 📊 **Kontingente**: Budgets, Quoten, Limits

Counter machen diese **Strukturen explizit sichtbar** im Prozessmodell!

---

## FAQ

### F: Kann ich Counter zurücksetzen?

**A:** Ja, auf zwei Arten:

1. **Automatisch:** `counter_reset_on_max = true` (bei Maximum)
2. **Manuell:** Neues Element "RESET" zu Counter-Element hinzufügen (TODO: Future Feature)
3. **Programmgesteuert:** `counter.counter_current_value = counter.counter_start_value`

---

### F: Was passiert bei Maximum?

**A:** Drei Szenarien:

| Konfiguration | Verhalten |
|---------------|-----------|
| `on_max_reached` gesetzt | Springt zu angegebenem Element |
| `reset_on_max = true` | Counter springt auf `start_value` zurück |
| Beides nicht | Counter bleibt bei Maximum stehen, Prozess läuft normal weiter |

---

### F: Kann Counter negativ werden?

**A:** Nein, Validierung verhindert das:

- **DOWN Counter:** Minimum ist 0
- **UP Counter:** Minimum ist `start_value`
- **UP_DOWN Counter:** Minimum ist 0

Versuch, unter 0 zu gehen → WARNING in Validierung

---

### F: Unterschied zwischen on_max_reached und Outgoing Connection?

**A:**

| | Outgoing Connection | on_max_reached |
|-|---------------------|----------------|
| **Wann** | Immer | Nur bei Maximum |
| **Zweck** | Normaler Prozessfluss | Eskalations-Logik |
| **Anzahl** | Beliebig viele | Nur 1 Element |
| **Kombinierbar** | Ja | Ja |

**Empfehlung:** Verwenden Sie `on_max_reached` für **Ausnahmepfade** (Eskalationen), normale Verbindungen für **Haupt-Flow**.

---

### F: Kann ich Counter in Subprozessen verwenden?

**A:** Ja, aber **Scope beachten**:

- Counter-Wert ist **lokal** zum Subprozess
- Bei Subprozess-Ende: Wert geht verloren
- Für **persistente Zählung**: Counter im Haupt-Prozess

**Zukünftig geplant:** Global Counter (über Prozess-Grenzen hinweg)

---

### F: Performance bei vielen Countern?

**A:** 

- ✅ **Unbedenklich** bis ~100 Counter pro Prozess
- ⚠️ **Prüfen** ab 100+ Counter (kann UI verlangsamen)
- 🔧 **Optimierung:** Gruppieren Sie ähnliche Counter in Subprozessen

---

### F: Counter in Timer-Schleifen?

**A:** Ja, **häufiges Pattern**:

```
[Counter] → [Aktion] → [Timer] → [Gateway] → zurück zu [Counter]
```

**Wichtig:** 
- `counter_reset_on_max = true` für Endlos-Loops ✅
- ValidationService zeigt INFO bei Loop ohne Reset

---

### F: Counter vs. Variable - was verwenden?

**A:**

| Kriterium | Counter | Variable |
|-----------|---------|----------|
| **Sichtbarkeit** | ✅ Im Prozess sichtbar | ❌ Unsichtbar |
| **Validierung** | ✅ Automatisch | ❌ Manuell |
| **Eskalation** | ✅ on_max_reached | ❌ Gateway-Logik nötig |
| **Flexibilität** | ❌ Nur Zahlen | ✅ Beliebige Typen |

**Faustregel:** Für **Zähllogik** → Counter, für **komplexe Daten** → Variablen

---

### F: Counter mit mehreren Exits?

**A:** Aktuell **nicht direkt** möglich, aber:

**Workaround:**
```
[Counter] → [Gateway]
              ├─ Bei Wert < 3 → Wiederholen
              ├─ Bei Wert = 3 → Eskalation 1
              └─ Bei Wert > 5 → Eskalation 2
```

**Zukünftig geplant:** `counter_on_values` mit mehreren Schwellenwerten

---

## 🚀 Weitere Ressourcen

### Dokumentation
- [VPB Process Designer Übersicht](vpb_process_designer.md)
- [Validation Service](DOC_vpb_compliance_engine.md)
- [SPS-Elemente Roadmap](TODO_SPS_ELEMENTS_IMPLEMENTATION.md)

### Beispiele
- `processes/example_counter_mahnung.vpb.json` - Mahnungsprozess
- `tests/test_counter_element.py` - Unit Tests
- `tests/test_counter_validation.py` - Validierungs-Tests

### Nächste SPS-Elemente (Roadmap)
- **CONDITION** (Bedingungsprüfung) - Q4 2025
- **ERROR_HANDLER** (Fehlerbehandlung) - Q4 2025
- **STATE** (Zustandsautomat) - Q1 2026
- **INTERLOCK** (Verriegelungen) - Q1 2026

---

**Version History:**
- **1.0** (18.10.2025): Initiale Dokumentation nach Counter v1.0 Release
- **0.9** (27.11.2024): Beta-Dokumentation während Implementierung

**Autoren:** VPB Development Team  
**Lizenz:** Internal Use  
**Support:** GitHub Issues oder makr-code@github

---

*Diese Dokumentation ist Teil des VPB Process Designer Projekts.*  
*Für Fragen oder Feedback öffnen Sie bitte ein Issue im Repository.*
