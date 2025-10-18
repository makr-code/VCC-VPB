# SPS-Steuerungstechnik für Verwaltungsprozesse

**Datum:** 18. Oktober 2025  
**Analyse:** Übertragbarkeit von SPS-Konzepten auf VPB-Verwaltungsprozesse

---

## 🎯 Zielsetzung

Prüfung, welche Elemente und Konzepte aus der **SPS (Speicherprogrammierbare Steuerung)** für die Abbildung von **Verwaltungsprozessen** im VPB-System relevant und übertragbar sind.

---

## 📊 SPS-Grundkonzepte

### Was ist SPS?

**SPS (Speicherprogrammierbare Steuerung)** ist ein digitaler Computer für:
- Industrielle Automatisierung
- Prozesssteuerung in Echtzeit
- Sequenzielle und parallele Abläufe
- Zeitgesteuerte Operationen

**Programmiersprachen nach IEC 61131-3:**
- **FUP** (Funktionsplan) - Grafisch, Logikgatter
- **KOP** (Kontaktplan) - Grafisch, Relais-Logik
- **AWL** (Anweisungsliste) - Textbasiert
- **ST** (Strukturierter Text) - Hochsprache
- **AS** (Ablaufsprache) - Zustandsautomaten

---

## 🔍 Relevanzanalyse für Verwaltungsprozesse

### ✅ HOHE RELEVANZ

#### 1. **Zeitgesteuerte Prozesse (Timer/Counter)**

**SPS-Konzept:**
```
TON (Timer On-Delay)     - Verzögerung beim Einschalten
TOF (Timer Off-Delay)    - Verzögerung beim Ausschalten
TP (Timer Pulse)         - Impuls fester Dauer
CTU (Counter Up)         - Aufwärtszähler
CTD (Counter Down)       - Abwärtszähler
```

**VPB-Übertragung:** ✅ **BEREITS IMPLEMENTIERT**
```json
{
  "element_type": "TIME_LOOP",
  "loop_type": "interval",
  "loop_interval_minutes": 60,
  "loop_max_iterations": 0
}

{
  "element_type": "TIMER",
  "loop_type": "date",
  "loop_date": "2025-12-31"
}
```

**Verwaltungs-Anwendungsfälle:**
- ✅ **Fristen:** Automatische Erinnerung nach X Tagen
- ✅ **Wiedervorlagen:** Wiederholende Prüfungen
- ✅ **Eskalationen:** Timer für Nicht-Bearbeitung
- ✅ **Terminüberwachung:** Deadline-Monitoring

**Beispiel:** Baugenehmigung
```
Antrag eingeht → TON(14 Tage) → Erinnerung an Antragsteller
Antrag eingeht → TON(90 Tage) → Automatische Ablehnung (§ 13 Abs. 2 BauGB)
```

---

#### 2. **Zustandsautomaten (Ablaufsprache / Grafcet)**

**SPS-Konzept:**
```
STEP/TRANSITION-Modell:
- Schritte (S1, S2, S3...)
- Transitionen (T1, T2, T3...)
- Aktionen (A1, A2, A3...)
```

**VPB-Übertragung:** ✅ **TEILWEISE VORHANDEN**

Aktuell in VPB:
```
START_EVENT → FUNCTION → GATEWAY → FUNCTION → END_EVENT
```

Könnte erweitert werden zu:
```json
{
  "element_type": "STATE",
  "state_name": "Antrag_eingereicht",
  "transitions": [
    {"to": "In_Prüfung", "condition": "vollständig"},
    {"to": "Nachforderung", "condition": "unvollständig"}
  ]
}
```

**Verwaltungs-Anwendungsfälle:**
- ✅ **Statusverfolgung:** Antragsstatus (eingereicht, geprüft, genehmigt)
- ✅ **Genehmigungsworkflows:** Schrittweise Freigabe
- ✅ **Eskalationsstufen:** Level 1 → Level 2 → Führungskraft
- ✅ **Dokumentenstatus:** Entwurf → Freigabe → Archiviert

**Beispiel:** Bestellprozess (öffentliche Verwaltung)
```
S1: Bedarfsmeldung → T1(Budget OK) → S2: Genehmigung
S2: Genehmigung → T2(Freigabe) → S3: Bestellung
S3: Bestellung → T3(Lieferung) → S4: Wareneingang
```

---

#### 3. **Sequentielle Steuerung (Sequential Function Chart - SFC)**

**SPS-Konzept:**
```
Linear:     S1 → S2 → S3 → S4
Verzweigt:  S1 → (S2a | S2b) → S3
Parallel:   S1 → [S2a + S2b] → S3
```

**VPB-Übertragung:** ✅ **VORHANDEN**

VPB unterstützt:
- ✅ **Linear:** SEQUENCE-Verbindungen
- ✅ **Verzweigt:** GATEWAY (XOR, OR)
- ✅ **Parallel:** AND_CONNECTOR

**Verwaltungs-Anwendungsfälle:**
- ✅ **Parallele Prüfungen:** Fachprüfung + Rechtsprüfung gleichzeitig
- ✅ **Bedingte Pfade:** IF vollständig THEN weiter ELSE Nachforderung
- ✅ **Gabelungen:** Nach Antragsart (A, B, C) unterschiedliche Wege

**Beispiel:** Baugenehmigung
```
Antrag → [Fachprüfung + Rechtsprüfung + Umweltprüfung] → Zusammenführung → Bescheid
```

---

#### 4. **Interlocks / Verriegelungen**

**SPS-Konzept:**
```
IF (Tür_geschlossen AND Sicherheitsschalter_OK) THEN Motor_Start
```

**VPB-Übertragung:** ⚠️ **TEILWEISE UMSETZBAR**

Aktuell über GATEWAY + Bedingungen:
```json
{
  "element_type": "GATEWAY",
  "gateway_type": "AND",
  "conditions": [
    "Dokumente_vollständig",
    "Gebühren_bezahlt",
    "Frist_nicht_abgelaufen"
  ]
}
```

**Verwaltungs-Anwendungsfälle:**
- ✅ **Voraussetzungen:** Nur weiter wenn alle Dokumente vorliegen
- ✅ **Berechtigungen:** Nur Chef darf Beträge >10.000€ freigeben
- ✅ **Fristen:** Nur innerhalb der Antragsfrist bearbeiten
- ✅ **Compliance:** Nur mit unterschriebener Datenschutzerklärung

**Beispiel:** Zuschussantrag
```
IF (Antrag_vollständig AND Budget_verfügbar AND Bewilligungsstelle_zuständig)
THEN Bearbeitung_starten
ELSE Ablehnung
```

---

### ⚠️ MITTLERE RELEVANZ

#### 5. **Analog-Verarbeitung (PID-Regler, Skalierung)**

**SPS-Konzept:**
```
PID-Regler: Temperatur, Druck, Durchfluss regeln
Skalierung: 4-20mA → 0-100°C
```

**VPB-Übertragung:** ⚠️ **BEGRENZT RELEVANT**

Mögliche Analogien:
```json
{
  "element_type": "PRIORITY_SCORER",
  "input": "Dringlichkeit (1-10)",
  "output": "Bearbeitungspriorität (Hoch/Mittel/Niedrig)"
}
```

**Verwaltungs-Anwendungsfälle:**
- ⚠️ **Priorisierung:** Antragsbewertung nach Punkten
- ⚠️ **Scoring:** Risikoanalyse (0-100 Punkte)
- ⚠️ **Gewichtung:** Mehrere Kriterien kombinieren

**Beispiel:** Förderanträge
```
Bewertung = 0.4 * Innovation + 0.3 * Wirtschaftlichkeit + 0.3 * Nachhaltigkeit
IF Bewertung > 70 THEN Förderung_empfohlen
```

**Einschränkung:** Verwaltungsprozesse sind meist diskret (Ja/Nein), nicht analog (stufenlos).

---

#### 6. **Fehlerbehandlung / Diagnose**

**SPS-Konzept:**
```
Fehlerreaktion:
- Alarm auslösen
- Prozess anhalten
- Safe State aktivieren
- Fehler protokollieren
```

**VPB-Übertragung:** ⚠️ **TEILWEISE VORHANDEN**

Aktuell:
```json
{
  "connection_type": "ESCALATION",
  "description": "Bei Fehler eskalieren"
}
```

Könnte erweitert werden:
```json
{
  "element_type": "ERROR_HANDLER",
  "error_types": ["Timeout", "Unvollständig", "Ablehnung"],
  "reactions": {
    "Timeout": "Erinnerung_senden",
    "Unvollständig": "Nachforderung_starten",
    "Ablehnung": "Bescheid_erstellen"
  }
}
```

**Verwaltungs-Anwendungsfälle:**
- ✅ **Fehlende Dokumente:** Automatische Nachforderung
- ✅ **Fristüberschreitung:** Eskalation an Vorgesetzten
- ✅ **Ablehnung:** Alternative Prozesse (Widerspruch)
- ✅ **Systemfehler:** Fallback-Prozess

---

### ❌ GERINGE/KEINE RELEVANZ

#### 7. **Echtzeitverarbeitung (zyklische Programmabarbeitung)**

**SPS-Konzept:**
```
Zyklus: 10ms, 100ms, 1s
Reaktionszeit: <1ms
```

**VPB-Übertragung:** ❌ **NICHT RELEVANT**

**Begründung:**
- Verwaltungsprozesse sind **ereignisgesteuert**, nicht zyklisch
- Zeitskalen: Tage/Wochen, nicht Millisekunden
- Keine Echtzeit-Anforderungen

---

#### 8. **Digitale Ein-/Ausgänge (I/O-Signale)**

**SPS-Konzept:**
```
Eingänge: Taster, Sensoren, Schalter (24V)
Ausgänge: Ventile, Motoren, Lampen (24V)
```

**VPB-Übertragung:** ❌ **NICHT RELEVANT**

**Begründung:**
- Verwaltung arbeitet mit **Dokumenten**, nicht Hardware-Signalen
- Keine physischen Aktoren/Sensoren

**Ausnahme:** Smart City / IoT-Integration
- Parkplatzsensoren → Gebührenbescheid
- Abfallcontainer-Füllstand → Leerung beauftragen

---

#### 9. **Feldbus-Kommunikation (Profibus, Modbus, EtherCAT)**

**SPS-Konzept:**
```
SPS ↔ Feldgeräte via Feldbus
Dezentrale Peripherie
```

**VPB-Übertragung:** ❌ **NICHT RELEVANT**

**Begründung:**
- Verwaltung nutzt **Standard-IT-Protokolle** (HTTP, REST, SOAP)
- Keine industriellen Feldbusse

---

## ✅ Empfohlene Erweiterungen für VPB

### 1. **STATE-Element (Zustandsautomat)**

**Neu zu implementieren:**
```json
{
  "element_type": "STATE",
  "state_name": "In_Prüfung",
  "entry_actions": ["Status_setzen", "E-Mail_senden"],
  "exit_actions": ["Zeitstempel_setzen"],
  "allowed_transitions": [
    {"to": "Genehmigt", "condition": "alle_Prüfungen_OK"},
    {"to": "Abgelehnt", "condition": "Prüfung_negativ"},
    {"to": "Nachforderung", "condition": "Dokumente_fehlen"}
  ]
}
```

**Vorteile:**
- ✅ Explizite Statusmodellierung
- ✅ Zustandsübergänge mit Bedingungen
- ✅ Entry/Exit-Actions (wie SPS GRAFCET)
- ✅ Historie-Tracking

---

### 2. **CONDITION-Element (Bedingungsprüfung)**

**Neu zu implementieren:**
```json
{
  "element_type": "CONDITION",
  "condition_type": "AND",
  "checks": [
    {"field": "Gebühren_bezahlt", "operator": "==", "value": true},
    {"field": "Dokumente_vollständig", "operator": "==", "value": true},
    {"field": "Frist_Tage", "operator": "<=", "value": 90}
  ],
  "on_true": "weiter_zu_Genehmigung",
  "on_false": "weiter_zu_Ablehnung"
}
```

**Vorteile:**
- ✅ Explizite Bedingungslogik (wie SPS IF-THEN)
- ✅ Mehrfachbedingungen (AND, OR, NOT)
- ✅ Vergleichsoperatoren (==, !=, <, >, <=, >=)
- ✅ Testbarkeit

---

### 3. **COUNTER-Element (Zähler)**

**Neu zu implementieren:**
```json
{
  "element_type": "COUNTER",
  "counter_type": "UP",
  "start_value": 0,
  "max_value": 3,
  "reset_on_max": true,
  "on_max_reached": "Eskalation_starten"
}
```

**Verwaltungs-Anwendungsfälle:**
- ✅ **Erinnerungs-Zähler:** Nach 3 Mahnungen → Eskalation
- ✅ **Wiederholungs-Limit:** Max. 2 Nachforderungen
- ✅ **Versuchs-Zähler:** Max. 3 Anmeldeversuche

---

### 4. **ERROR_HANDLER-Element (Fehlerbehandlung)**

**Neu zu implementieren:**
```json
{
  "element_type": "ERROR_HANDLER",
  "error_sources": ["Timeout", "Validation_Error", "Missing_Data"],
  "handlers": {
    "Timeout": {
      "action": "Erinnerung_senden",
      "retry_count": 3,
      "escalate_after": 3
    },
    "Validation_Error": {
      "action": "Nachforderung_starten",
      "notify": "Antragsteller"
    },
    "Missing_Data": {
      "action": "Prozess_pausieren",
      "notify": "Sachbearbeiter"
    }
  }
}
```

**Vorteile:**
- ✅ Strukturierte Fehlerbehandlung (wie SPS Fehlerorganisation)
- ✅ Unterschiedliche Reaktionen je Fehlertyp
- ✅ Retry-Logik
- ✅ Eskalationsmechanismen

---

### 5. **INTERLOCK-Element (Verriegelung/Freigabe)**

**Neu zu implementieren:**
```json
{
  "element_type": "INTERLOCK",
  "interlock_type": "AND",
  "requirements": [
    {"check": "Benutzer_berechtigt", "role": "Sachgebietsleiter"},
    {"check": "Budget_verfügbar", "min_amount": 1000},
    {"check": "Frist_eingehalten", "max_days": 30}
  ],
  "on_locked": "Ablehnung_Fehlende_Berechtigung",
  "on_unlocked": "Freigabe_erteilt"
}
```

**Verwaltungs-Anwendungsfälle:**
- ✅ **Berechtigungs-Gates:** Nur bestimmte Rollen dürfen weiter
- ✅ **Budget-Gates:** Nur bei verfügbarem Budget freigeben
- ✅ **Compliance-Gates:** Nur mit DSGVO-Einwilligung

---

## 📊 Vergleichstabelle: SPS vs VPB

| SPS-Element | VPB-Status | Relevanz | Empfehlung |
|-------------|------------|----------|------------|
| **Timer (TON, TOF, TP)** | ✅ Vorhanden (TIME_LOOP, TIMER) | ⭐⭐⭐⭐⭐ | Bereits optimal |
| **Counter (CTU, CTD)** | ❌ Fehlt | ⭐⭐⭐⭐ | **Implementieren** |
| **Zustandsautomat (GRAFCET)** | ⚠️ Teilweise (via GATEWAY) | ⭐⭐⭐⭐⭐ | **STATE-Element hinzufügen** |
| **Sequenzen (SFC)** | ✅ Vorhanden (SEQUENCE) | ⭐⭐⭐⭐⭐ | Bereits optimal |
| **Verzweigungen (Branch)** | ✅ Vorhanden (GATEWAY) | ⭐⭐⭐⭐⭐ | Bereits optimal |
| **Parallelität (Parallel)** | ✅ Vorhanden (AND_CONNECTOR) | ⭐⭐⭐⭐⭐ | Bereits optimal |
| **Interlocks (Safety)** | ⚠️ Teilweise (via GATEWAY) | ⭐⭐⭐⭐ | **INTERLOCK-Element hinzufügen** |
| **Fehlerbehandlung** | ⚠️ Teilweise (ESCALATION) | ⭐⭐⭐⭐ | **ERROR_HANDLER hinzufügen** |
| **Bedingungen (IF-THEN)** | ⚠️ Implizit (GATEWAY) | ⭐⭐⭐⭐ | **CONDITION-Element hinzufügen** |
| **Analog-Verarbeitung (PID)** | ❌ Fehlt | ⭐⭐ | Niedrige Priorität |
| **I/O-Signale** | ❌ N/A | ⭐ | Nicht relevant |
| **Echtzeit-Zyklen** | ❌ N/A | ⭐ | Nicht relevant |
| **Feldbus** | ❌ N/A | ⭐ | Nicht relevant |

**Legende:**
- ⭐⭐⭐⭐⭐ = Sehr hohe Relevanz
- ⭐⭐⭐⭐ = Hohe Relevanz
- ⭐⭐⭐ = Mittlere Relevanz
- ⭐⭐ = Geringe Relevanz
- ⭐ = Keine Relevanz

---

## 🎯 Prioritäten für VPB-Erweiterung

### **Priorität 1: HOHE RELEVANZ** (kurzfristig)

1. **COUNTER-Element** 
   - Erinnerungszähler, Wiederholungslimits
   - Relativ einfach zu implementieren
   
2. **CONDITION-Element**
   - Explizite Bedingungslogik (besser als versteckt in GATEWAY)
   - Erhöht Lesbarkeit und Testbarkeit

3. **ERROR_HANDLER-Element**
   - Strukturierte Fehlerbehandlung
   - Eskalationsmechanismen

### **Priorität 2: MITTLERE RELEVANZ** (mittelfristig)

4. **STATE-Element**
   - Explizite Zustandsmodellierung
   - Komplexer, aber hoher Mehrwert

5. **INTERLOCK-Element**
   - Berechtigungs-/Budget-Gates
   - Compliance-Prüfungen

### **Priorität 3: GERINGE RELEVANZ** (langfristig/optional)

6. **Analog-Scoring**
   - Nur für spezielle Anwendungsfälle (Förderanträge)
   
7. **IoT-Integration**
   - Nur für Smart-City-Szenarien

---

## 💡 Praktische Beispiele

### Beispiel 1: Baugenehmigung mit SPS-Konzepten

**Aktuell (VPB Basic):**
```
START → Antrag_prüfen → GATEWAY(vollständig?) → Genehmigung → END
                              ↓ (Nein)
                         Nachforderung → zurück zu Prüfung
```

**Mit SPS-Konzepten erweitert:**
```
START → [STATE: Eingegangen]
    ↓ Entry: Zeitstempel_setzen, E-Mail_bestätigen
    ↓
[INTERLOCK: Vollständigkeit]
    ├─ Check: Bauzeichnung_vorhanden
    ├─ Check: Grundstücksbescheinigung_vorhanden
    └─ Check: Gebühren_bezahlt
    ↓ (Alle OK)
[STATE: In_Prüfung]
    ↓ Entry: Sachbearbeiter_zuweisen
    ↓
[Parallel: Fachprüfung + Rechtsprüfung + Umweltprüfung]
    ↓
[STATE: Prüfung_abgeschlossen]
    ↓
[CONDITION: Genehmigungsfähig?]
    ├─ TRUE → [STATE: Genehmigt]
    └─ FALSE → [STATE: Abgelehnt]
    ↓
[TIMER: 90 Tage]
    ↓ On_Timeout → Automatische_Ablehnung (§13 Abs.2 BauGB)
```

---

### Beispiel 2: Zuschussantrag mit Zähler und Fehlerbehandlung

```
START → [STATE: Antrag_eingegangen]
    ↓
[COUNTER: Nachforderungen]
    ├─ Max: 3
    └─ Reset: False
    ↓
[CONDITION: Dokumente_vollständig?]
    ├─ TRUE → [STATE: Bewilligung]
    └─ FALSE → [COUNTER: +1]
                ↓ (Count < 3)
             Nachforderung_senden
                ↓ (Count == 3)
             [ERROR_HANDLER: Max_Nachforderungen]
                → Ablehnung_wegen_Unvollständigkeit
```

---

## 📝 Fazit

### ✅ Sehr gut übertragbar

- **Timer/Counter:** Fristen, Wiedervorlagen, Eskalationen
- **Zustandsautomaten:** Statusverfolgung, Workflows
- **Sequenzen:** Lineare und verzweigte Prozesse
- **Parallelität:** Gleichzeitige Prüfungen
- **Interlocks:** Berechtigungen, Compliance-Gates

### ⚠️ Teilweise übertragbar

- **Analog-Verarbeitung:** Nur für Scoring/Bewertung
- **Fehlerbehandlung:** Konzept ja, aber angepasst

### ❌ Nicht übertragbar

- **Echtzeit-Anforderungen:** Verwaltung ist nicht zeitkritisch
- **I/O-Signale:** Keine Hardware-Anbindung
- **Feldbus:** Verwaltung nutzt Standard-IT

### 🚀 Empfohlene Implementierung

**Phase 1 (Q1 2026):**
1. COUNTER-Element
2. CONDITION-Element
3. ERROR_HANDLER-Element

**Phase 2 (Q2 2026):**
4. STATE-Element (komplexer)
5. INTERLOCK-Element

**Phase 3 (Q3 2026):**
6. Analog-Scoring (optional)
7. IoT-Integration (Smart City)

---

**Ende der Analyse**
