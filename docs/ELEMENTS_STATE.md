# STATE Element - Zustandsautomaten

**Version:** 1.0  
**Status:** ✅ Released  
**Element-Typ:** `STATE`  
**Kategorie:** SPS-Logik / State Machines

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [State-Typen](#state-typen)
3. [Transitions](#transitions)
4. [Entry/Exit Actions](#entryexit-actions)
5. [Timeout-Mechanismus](#timeout-mechanismus)
6. [Verwendungsbeispiele](#verwendungsbeispiele)
7. [Best Practices](#best-practices)
8. [Eigenschaften-Referenz](#eigenschaften-referenz)
9. [Validierungsregeln](#validierungsregeln)
10. [FAQ](#faq)

---

## Übersicht

### Was ist STATE?

Das **STATE** Element ermöglicht die Modellierung von **Zustandsautomaten** (State Machines) in VPB-Prozessen. Ein State repräsentiert einen definierten Zustand in einem Workflow mit:

- **Event-basierte Übergänge**: Wechsel zwischen States durch Events
- **Entry/Exit Actions**: Automatische Aktionen beim Betreten/Verlassen
- **Timeout-Handling**: Automatischer Übergang nach Zeitablauf
- **Conditional Transitions**: Bedingungsbasierte Zustandswechsel

### Einsatzgebiete

- **Workflow-Management**: Antragsstatus (Eingereicht → In Prüfung → Genehmigt)
- **Genehmigungs-Prozesse**: Mehrstufige Freigabeworkflows
- **Ticket-Systeme**: Status-Tracking (Offen → In Bearbeitung → Geschlossen)
- **Prozess-Orchestrierung**: Koordination komplexer Abläufe
- **Fehlerbehandlung**: Strukturierte Error-States mit Recovery

### Visuelle Darstellung

```
   ╱‾‾‾‾‾‾‾‾‾‾‾╲
  │  ▶️ Start   │  ← House/Pentagon-Form (5-Ecken)
   ╲___________╱   ← Icon zeigt State-Type
       │
       ↓ submit
   ╱‾‾‾‾‾‾‾‾‾‾‾╲
  │  ⬤ Review   │  ← NORMAL State
  │  Trans: 2    │  ← Zeigt Transition-Count
   ╲___________╱
       ├─── approve ──→ 🏁 Approved (FINAL)
       └─── reject ───→ 🏁 Rejected (FINAL)
```

**Farben:**
- Füllung: `#E8F5E9` (helles Grün)
- Rahmen: `#4CAF50` (kräftiges Grün)
- Icons: ▶️ (INITIAL), 🏁 (FINAL), ❌ (ERROR), ⬤ (NORMAL)

---

## State-Typen

### 1. INITIAL (Initialer State)

**Beschreibung:** Der Einstiegspunkt der State Machine. Hier beginnt der Workflow.

**Eigenschaften:**
- ▶️ Icon zur Kennzeichnung
- Sollte **keine eingehenden** Verbindungen haben (Entry Point)
- **Nur ein INITIAL State** pro State Machine erlaubt
- Typischerweise mit ausgehenden Transitions zu NORMAL States

**Wann verwenden?**
- Start eines Antragsprozesses
- Initialer Status bei Ticket-Erstellung
- Workflow-Beginn

**Beispiel:**
```json
{
  "element_id": "state_submitted",
  "element_type": "STATE",
  "state_name": "Eingereicht",
  "state_type": "INITIAL",
  "state_entry_action": "log_submission",
  "state_transitions": [
    {
      "event": "start_review",
      "target": "state_review",
      "condition": ""
    }
  ]
}
```

**Validierung:**
- ✅ Genau ein INITIAL State pro Dokument
- ⚠️ Warnung bei eingehenden Verbindungen

---

### 2. NORMAL (Standard State)

**Beschreibung:** Regulärer Zwischenzustand im Workflow. Die meisten States sind vom Typ NORMAL.

**Eigenschaften:**
- ⬤ Icon zur Kennzeichnung
- Kann beliebig viele ein- und ausgehende Transitions haben
- Typischer Arbeitsschritt oder Wartezustand
- Unterstützt Timeouts für automatische Übergänge

**Wann verwenden?**
- Bearbeitungszustände ("In Prüfung", "In Bearbeitung")
- Wartezustände ("Wartet auf Rückmeldung")
- Zwischenschritte in mehrstufigen Prozessen

**Beispiel:**
```json
{
  "element_id": "state_review",
  "element_type": "STATE",
  "state_name": "In Prüfung",
  "state_type": "NORMAL",
  "state_entry_action": "assign_reviewer",
  "state_exit_action": "log_decision",
  "state_transitions": [
    {
      "event": "approve",
      "target": "state_approved",
      "condition": "valid==true"
    },
    {
      "event": "reject",
      "target": "state_rejected",
      "condition": ""
    },
    {
      "event": "request_info",
      "target": "state_info_requested",
      "condition": ""
    }
  ],
  "state_timeout": 3600,
  "state_timeout_target": "state_timeout_error"
}
```

**Validierung:**
- ℹ️ Info wenn keine Transitions definiert

---

### 3. FINAL (Endzustand)

**Beschreibung:** Endpunkt der State Machine. Workflow ist abgeschlossen.

**Eigenschaften:**
- 🏁 Icon zur Kennzeichnung
- Sollte **keine ausgehenden** Verbindungen haben (End Point)
- Mehrere FINAL States möglich (verschiedene Ergebnisse)
- Markiert erfolgreichen oder definitiven Abschluss

**Wann verwenden?**
- Erfolgreicher Abschluss ("Genehmigt", "Abgeschlossen")
- Endgültige Ablehnung ("Abgelehnt", "Zurückgezogen")
- Finale Entscheidungen

**Beispiel:**
```json
{
  "element_id": "state_approved",
  "element_type": "STATE",
  "state_name": "Genehmigt",
  "state_type": "FINAL",
  "state_entry_action": "send_approval_notification",
  "state_transitions": []
}
```

**Validierung:**
- ⚠️ Warnung bei ausgehenden Verbindungen

---

### 4. ERROR (Fehlerzustand)

**Beschreibung:** Spezieller State für Fehlerbehandlung und Ausnahmesituationen.

**Eigenschaften:**
- ❌ Icon zur Kennzeichnung
- Für Timeout-Fälle, Validierungsfehler, Exceptions
- Kann Transitions zu Recovery-States oder FINAL States haben
- Ermöglicht strukturierte Fehlerbehandlung

**Wann verwenden?**
- Timeout-Behandlung
- Validierungsfehler
- System-Fehler
- Ausnahmesituationen

**Beispiel:**
```json
{
  "element_id": "state_timeout",
  "element_type": "STATE",
  "state_name": "Timeout-Fehler",
  "state_type": "ERROR",
  "state_entry_action": "notify_timeout",
  "state_transitions": [
    {
      "event": "retry",
      "target": "state_review",
      "condition": "retry_count < 3"
    },
    {
      "event": "escalate",
      "target": "state_escalated",
      "condition": ""
    }
  ]
}
```

**Validierung:**
- ℹ️ Info wenn keine Transitions definiert

---

## Transitions

### Grundkonzept

**Transitions** definieren die Übergänge zwischen States. Jede Transition besteht aus:

1. **Event**: Auslöser des Übergangs (z.B. "submit", "approve", "cancel")
2. **Target**: Ziel-State (Element-ID)
3. **Condition**: Optional - Bedingung für den Übergang

### Event-basierte Transitions

Events sind benannte Auslöser für Zustandswechsel:

```json
{
  "event": "submit",
  "target": "state_review",
  "condition": ""
}
```

**Typische Events:**
- **submit**: Einreichung/Absenden
- **approve**: Genehmigung
- **reject**: Ablehnung
- **cancel**: Abbruch
- **retry**: Wiederholung
- **escalate**: Eskalation
- **complete**: Abschluss

### Conditional Transitions

Transitions mit Bedingungen werden nur ausgeführt, wenn die Condition `true` ist:

```json
{
  "event": "approve",
  "target": "state_approved",
  "condition": "amount < 10000 && valid==true"
}
```

**Condition-Syntax:**
- Einfache Expressions: `valid==true`
- Vergleiche: `amount < 10000`
- Logische Operatoren: `&&`, `||`, `!`
- Feldverweise: `status`, `amount`, `priority`

**Beispiel mit mehreren bedingten Transitions:**
```json
"state_transitions": [
  {
    "event": "approve",
    "target": "state_auto_approved",
    "condition": "amount < 1000"
  },
  {
    "event": "approve",
    "target": "state_manager_review",
    "condition": "amount >= 1000 && amount < 10000"
  },
  {
    "event": "approve",
    "target": "state_director_review",
    "condition": "amount >= 10000"
  }
]
```

### Transition-Reihenfolge

Wenn mehrere Transitions dasselbe Event haben:
1. Prüfe Conditions in der Reihenfolge der Definition
2. Erste Transition mit `true` Condition wird ausgeführt
3. Ohne Condition = immer `true`

**Best Practice:** Definiere spezifischste Bedingung zuerst!

---

## Entry/Exit Actions

### Konzept

**Entry Actions** und **Exit Actions** sind automatische Operationen beim Zustandswechsel:

- **Entry Action**: Wird ausgeführt, wenn der State betreten wird
- **Exit Action**: Wird ausgeführt, wenn der State verlassen wird

### Verwendung

**Zwei Arten von Actions:**

1. **Element-Referenz**: ID eines anderen Elements (z.B. TASK)
2. **Script/Expression**: Inline-Code oder Funktionsaufruf

### Element-Referenz

```json
{
  "state_entry_action": "task_assign_reviewer",
  "state_exit_action": "task_log_decision"
}
```

Referenziert andere Prozess-Elemente, die ausgeführt werden sollen.

### Script/Expression

```json
{
  "state_entry_action": "console.log('Entering review state')",
  "state_exit_action": "notifyReviewer(element.state_name)"
}
```

Direkte Script-Ausführung (abhängig von Runtime-Umgebung).

### Typische Entry Actions

- **Benachrichtigungen senden**
  ```json
  "state_entry_action": "sendEmail('reviewer@example.com', 'New submission')"
  ```

- **Verantwortliche zuweisen**
  ```json
  "state_entry_action": "assignTo('team_lead')"
  ```

- **Zeitstempel setzen**
  ```json
  "state_entry_action": "setTimestamp('entered_review_at')"
  ```

- **Logging**
  ```json
  "state_entry_action": "log('State: Review started')"
  ```

### Typische Exit Actions

- **Entscheidung protokollieren**
  ```json
  "state_exit_action": "logDecision(decision_reason)"
  ```

- **Ressourcen freigeben**
  ```json
  "state_exit_action": "releaseResources()"
  ```

- **Status aktualisieren**
  ```json
  "state_exit_action": "updateStatus('completed')"
  ```

- **Statistiken erfassen**
  ```json
  "state_exit_action": "recordDuration(start_time)"
  ```

### Best Practices

✅ **DO:**
- Kurze, fokussierte Actions
- Idempotente Operationen (mehrfach ausführbar)
- Fehlerbehandlung in Actions
- Logging für Nachvollziehbarkeit

❌ **DON'T:**
- Lange, blockierende Operationen
- State-Änderungen innerhalb von Actions
- Unbehandelte Exceptions
- Side-Effects ohne Logging

---

## Timeout-Mechanismus

### Konzept

Der **Timeout-Mechanismus** ermöglicht automatische Zustandsübergänge nach einer definierten Zeit.

**Anwendungsfälle:**
- Automatische Eskalation bei langen Wartezeiten
- Timeout bei fehlender Rückmeldung
- Service Level Agreements (SLA) durchsetzen
- Automatische Prozessfortführung

### Konfiguration

```json
{
  "state_timeout": 3600,
  "state_timeout_target": "state_timeout_error"
}
```

- **state_timeout**: Zeit in Sekunden (0 = kein Timeout)
- **state_timeout_target**: Ziel-State bei Timeout (Element-ID)

### Verhalten

1. State wird betreten
2. Timeout-Timer startet (falls `state_timeout > 0`)
3. Bei normalem Übergang: Timer wird gestoppt
4. Nach `state_timeout` Sekunden: Automatischer Übergang zu `state_timeout_target`

### Beispiel: SLA-Überwachung

```json
{
  "element_id": "state_first_review",
  "state_name": "Erst-Prüfung",
  "state_type": "NORMAL",
  "state_timeout": 86400,
  "state_timeout_target": "state_escalated",
  "state_transitions": [
    {
      "event": "approve",
      "target": "state_approved",
      "condition": ""
    },
    {
      "event": "reject",
      "target": "state_rejected",
      "condition": ""
    }
  ]
}
```

**Erklärung:**
- Normale Bearbeitung: approve/reject innerhalb 24h
- Bei Timeout (>24h): Automatische Eskalation zu `state_escalated`

### Timeout-Hierarchie

**Kombination mit Transitions:**

```json
{
  "state_timeout": 7200,
  "state_timeout_target": "state_warning",
  "state_transitions": [
    {
      "event": "complete",
      "target": "state_done",
      "condition": ""
    }
  ]
}
```

- **Event-Transition** hat Vorrang (sofortige Ausführung)
- **Timeout** nur wenn keine Event-Transition erfolgt

### Best Practices Timeouts

✅ **Sinnvolle Timeout-Werte:**
- Kurze Prozesse: 300-1800s (5-30 min)
- Standard-Review: 3600-86400s (1-24h)
- Langläufer: 86400-604800s (1-7 Tage)

✅ **Timeout-Targets:**
- ERROR State für Fehlerbehandlung
- NORMAL State für Eskalation
- Benachrichtigungs-Tasks

❌ **Vermeiden:**
- Zu kurze Timeouts (< 60s für manuelle Prozesse)
- FINAL State als Timeout-Target (kein Abschluss bei Timeout!)
- Keine Timeout-Behandlung bei zeitkritischen Prozessen

---

## Verwendungsbeispiele

### Beispiel 1: Einfacher Genehmigungs-Workflow

**Szenario:** Urlaubsantrag mit 2-stufiger Genehmigung

```
▶️ Eingereicht → ⬤ Vorgesetzen-Prüfung → ⬤ HR-Prüfung → 🏁 Genehmigt
                                                       ↘ 🏁 Abgelehnt
```

**State Definitions:**

```json
{
  "states": [
    {
      "element_id": "state_submitted",
      "state_name": "Eingereicht",
      "state_type": "INITIAL",
      "state_entry_action": "notifyManager",
      "state_transitions": [
        {
          "event": "assign",
          "target": "state_manager_review",
          "condition": ""
        }
      ]
    },
    {
      "element_id": "state_manager_review",
      "state_name": "Vorgesetzten-Prüfung",
      "state_type": "NORMAL",
      "state_timeout": 172800,
      "state_timeout_target": "state_timeout_escalation",
      "state_transitions": [
        {
          "event": "approve",
          "target": "state_hr_review",
          "condition": ""
        },
        {
          "event": "reject",
          "target": "state_rejected",
          "condition": ""
        }
      ]
    },
    {
      "element_id": "state_hr_review",
      "state_name": "HR-Prüfung",
      "state_type": "NORMAL",
      "state_timeout": 86400,
      "state_timeout_target": "state_timeout_escalation",
      "state_transitions": [
        {
          "event": "approve",
          "target": "state_approved",
          "condition": ""
        },
        {
          "event": "reject",
          "target": "state_rejected",
          "condition": ""
        }
      ]
    },
    {
      "element_id": "state_approved",
      "state_name": "Genehmigt",
      "state_type": "FINAL",
      "state_entry_action": "sendApprovalEmail"
    },
    {
      "element_id": "state_rejected",
      "state_name": "Abgelehnt",
      "state_type": "FINAL",
      "state_entry_action": "sendRejectionEmail"
    },
    {
      "element_id": "state_timeout_escalation",
      "state_name": "Timeout-Eskalation",
      "state_type": "ERROR",
      "state_entry_action": "escalateToDirector"
    }
  ]
}
```

---

### Beispiel 2: Ticket-System mit Prioritäten

**Szenario:** Support-Ticket mit prioritätsbasiertem Routing

```
▶️ Offen → ⬤ Triage → ⬤ In Bearbeitung → 🏁 Gelöst
                    ↘ ⬤ Eskaliert
```

**State Definitions mit Conditional Transitions:**

```json
{
  "states": [
    {
      "element_id": "state_open",
      "state_name": "Offen",
      "state_type": "INITIAL",
      "state_entry_action": "createTicket",
      "state_transitions": [
        {
          "event": "assign",
          "target": "state_triage",
          "condition": ""
        }
      ]
    },
    {
      "element_id": "state_triage",
      "state_name": "Triage",
      "state_type": "NORMAL",
      "state_transitions": [
        {
          "event": "route",
          "target": "state_escalated",
          "condition": "priority=='critical' || priority=='high'"
        },
        {
          "event": "route",
          "target": "state_in_progress",
          "condition": "priority=='normal' || priority=='low'"
        }
      ]
    },
    {
      "element_id": "state_in_progress",
      "state_name": "In Bearbeitung",
      "state_type": "NORMAL",
      "state_timeout": 14400,
      "state_timeout_target": "state_escalated",
      "state_transitions": [
        {
          "event": "resolve",
          "target": "state_resolved",
          "condition": ""
        },
        {
          "event": "escalate",
          "target": "state_escalated",
          "condition": ""
        }
      ]
    },
    {
      "element_id": "state_escalated",
      "state_name": "Eskaliert",
      "state_type": "NORMAL",
      "state_entry_action": "notifySeniorSupport",
      "state_transitions": [
        {
          "event": "resolve",
          "target": "state_resolved",
          "condition": ""
        }
      ]
    },
    {
      "element_id": "state_resolved",
      "state_name": "Gelöst",
      "state_type": "FINAL",
      "state_entry_action": "notifyCustomer"
    }
  ]
}
```

---

### Beispiel 3: Komplexer Approval-Prozess

**Szenario:** Beschaffungsantrag mit Betragsabhängigkeit

```
▶️ Eingereicht → ⬤ Automatische Prüfung
                         ↓ <1000€
                    🏁 Auto-Genehmigt
                         ↓ 1000-10000€
                    ⬤ Manager-Genehmigung → 🏁 Genehmigt
                         ↓ >10000€                ↓
                    ⬤ Direktor-Genehmigung ------┘
                                                  ↓
                                            🏁 Abgelehnt
```

**State Definitions:**

```json
{
  "states": [
    {
      "element_id": "state_submitted",
      "state_name": "Eingereicht",
      "state_type": "INITIAL",
      "state_transitions": [
        {
          "event": "check",
          "target": "state_validation",
          "condition": ""
        }
      ]
    },
    {
      "element_id": "state_validation",
      "state_name": "Automatische Prüfung",
      "state_type": "NORMAL",
      "state_entry_action": "validateRequest",
      "state_transitions": [
        {
          "event": "validate",
          "target": "state_auto_approved",
          "condition": "amount < 1000"
        },
        {
          "event": "validate",
          "target": "state_manager_approval",
          "condition": "amount >= 1000 && amount < 10000"
        },
        {
          "event": "validate",
          "target": "state_director_approval",
          "condition": "amount >= 10000"
        },
        {
          "event": "invalid",
          "target": "state_rejected",
          "condition": ""
        }
      ]
    },
    {
      "element_id": "state_auto_approved",
      "state_name": "Auto-Genehmigt",
      "state_type": "FINAL",
      "state_entry_action": "processSmallPurchase"
    },
    {
      "element_id": "state_manager_approval",
      "state_name": "Manager-Genehmigung",
      "state_type": "NORMAL",
      "state_timeout": 172800,
      "state_timeout_target": "state_director_approval",
      "state_transitions": [
        {
          "event": "approve",
          "target": "state_approved",
          "condition": ""
        },
        {
          "event": "reject",
          "target": "state_rejected",
          "condition": ""
        }
      ]
    },
    {
      "element_id": "state_director_approval",
      "state_name": "Direktor-Genehmigung",
      "state_type": "NORMAL",
      "state_timeout": 259200,
      "state_timeout_target": "state_timeout_error",
      "state_transitions": [
        {
          "event": "approve",
          "target": "state_approved",
          "condition": ""
        },
        {
          "event": "reject",
          "target": "state_rejected",
          "condition": ""
        }
      ]
    },
    {
      "element_id": "state_approved",
      "state_name": "Genehmigt",
      "state_type": "FINAL",
      "state_entry_action": "processPurchase"
    },
    {
      "element_id": "state_rejected",
      "state_name": "Abgelehnt",
      "state_type": "FINAL",
      "state_entry_action": "notifyRejection"
    },
    {
      "element_id": "state_timeout_error",
      "state_name": "Timeout-Fehler",
      "state_type": "ERROR",
      "state_entry_action": "escalateTimeout"
    }
  ]
}
```

---

## Best Practices

### State Design

✅ **DO: Klare State-Namen**
```json
// Gut
"state_name": "In Prüfung"
"state_name": "Wartet auf Rückmeldung"
"state_name": "Genehmigt"

// Schlecht
"state_name": "State1"
"state_name": "S2"
"state_name": "OK"
```

✅ **DO: Aussagekräftige State-Typen nutzen**
- Genau **ein INITIAL** State
- **Mehrere FINAL** States für verschiedene Ergebnisse
- **ERROR** States für Fehlerbehandlung
- **NORMAL** für alle Zwischenschritte

❌ **DON'T: Zu viele States**
- Halte State Machine überschaubar (< 15 States)
- Gruppiere ähnliche Zustände
- Verwende Hierarchien bei Bedarf

---

### Transition Design

✅ **DO: Konsistente Event-Namen**
```json
// Gut - durchgängige Verben
"submit", "approve", "reject", "escalate", "complete"

// Schlecht - inkonsistente Benennung
"do_submit", "approved", "NO", "goToNext"
```

✅ **DO: Spezifische Conditions zuerst**
```json
"state_transitions": [
  { "event": "approve", "target": "high_value", "condition": "amount > 10000" },
  { "event": "approve", "target": "normal", "condition": "amount > 1000" },
  { "event": "approve", "target": "low_value", "condition": "" }
]
```

❌ **DON'T: Überlappende Conditions ohne Reihenfolge**
```json
// Problematisch - welche wird gewählt?
{ "condition": "amount > 1000" },
{ "condition": "amount > 5000" }
```

---

### Action Design

✅ **DO: Idempotente Actions**
```javascript
// Gut - kann mehrfach ausgeführt werden
state_entry_action: "setStatus('in_review')"

// Problematisch - nicht idempotent
state_entry_action: "counter++"
```

✅ **DO: Fehlerbehandlung in Actions**
```javascript
state_entry_action: "try { notifyReviewer() } catch(e) { log(e) }"
```

❌ **DON'T: State-Änderungen in Actions**
```javascript
// NIEMALS - führt zu unvorhersehbarem Verhalten!
state_entry_action: "changeState('other_state')"
```

---

### Timeout-Strategie

✅ **DO: Sinnvolle Timeout-Werte**
- Berücksichtige reale Bearbeitungszeiten
- Setze Buffer für unvorhergesehene Verzögerungen
- Dokumentiere SLA-Vorgaben

✅ **DO: Timeout-Behandlung planen**
```json
"state_timeout": 86400,
"state_timeout_target": "state_escalation",  // → Eskalation
// NICHT: "state_timeout_target": "state_final"  // → Fehlerhafter Abschluss
```

❌ **DON'T: Zu aggressive Timeouts**
```json
// Problematisch für manuelle Prozesse
"state_timeout": 60  // 1 Minute - zu kurz!
```

---

### State Machine Design

✅ **DO: Ein INITIAL State**
- Klarer Einstiegspunkt
- Validierung prüft automatisch

✅ **DO: Mehrere FINAL States**
```
🏁 Approved
🏁 Rejected
🏁 Cancelled
🏁 Expired
```

✅ **DO: ERROR States für Recovery**
```
❌ Timeout → [retry] → ⬤ Review
         → [escalate] → ⬤ Escalation
```

❌ **DON'T: Zirkuläre Abhängigkeiten ohne Exit**
```
⬤ State A → ⬤ State B → ⬤ State A → ...
// Endlosschleife! Füge FINAL oder ERROR State hinzu.
```

---

## Eigenschaften-Referenz

### Basis-Properties (geerbt von VPBElement)

| Property | Typ | Beschreibung |
|----------|-----|-------------|
| `element_id` | string | Eindeutige ID des Elements |
| `element_type` | string | Immer `"STATE"` |
| `name` | string | Interner Name (VPBElement) |
| `x`, `y` | int | Position auf Canvas |
| `description` | string | Optional: Beschreibung |

### STATE-spezifische Properties

| Property | Typ | Default | Pflicht | Beschreibung |
|----------|-----|---------|---------|-------------|
| `state_name` | string | `""` | ✅ | Display-Name des States |
| `state_type` | string | `"NORMAL"` | ✅ | State-Type: NORMAL, INITIAL, FINAL, ERROR |
| `state_entry_action` | string | `""` | ❌ | Action beim Betreten (Element-ID oder Script) |
| `state_exit_action` | string | `""` | ❌ | Action beim Verlassen (Element-ID oder Script) |
| `state_transitions` | List[Dict] | `[]` | ❌ | Liste von Transition-Definitionen |
| `state_timeout` | int | `0` | ❌ | Timeout in Sekunden (0 = kein Timeout) |
| `state_timeout_target` | string | `""` | ❌ | Ziel-State bei Timeout (Element-ID) |

### Transition-Struktur

```typescript
interface Transition {
  event: string;       // Event-Name (z.B. "submit", "approve")
  target: string;      // Ziel-State Element-ID
  condition: string;   // Optional: Bedingung (Expression)
}
```

**Beispiel:**
```json
{
  "event": "approve",
  "target": "state_approved",
  "condition": "amount < 10000 && valid==true"
}
```

---

## Validierungsregeln

Der **StateValidator** prüft STATE-Elemente auf korrekte Konfiguration:

### ERROR-Level Regeln

❌ **Regel 1: State-Name nicht leer**
```
STATE element must have a name
```
- Jeder State muss einen `state_name` haben
- Leer oder nur Whitespace → ERROR

❌ **Regel 2: State-Type gültig**
```
Invalid state type 'XYZ'
```
- Nur erlaubt: `NORMAL`, `INITIAL`, `FINAL`, `ERROR`
- Andere Werte → ERROR

❌ **Regel 3: Nur ein INITIAL State**
```
Multiple INITIAL states found (N total)
```
- Pro Dokument nur ein INITIAL State erlaubt
- Mehrere → ERROR bei allen INITIAL States

### WARNING-Level Regeln

⚠️ **Regel 4: Transitions haben gültige Ziele**
```
Transition #N target 'xyz' does not exist
Transition #N target 'xyz' is not a STATE element
```
- Target muss existieren
- Target sollte STATE-Element sein

⚠️ **Regel 5: Timeout-Target bei Timeout > 0**
```
Timeout is set (Ns) but no timeout target defined
Timeout target 'xyz' does not exist
Timeout target 'xyz' is not a STATE element
```
- Wenn Timeout gesetzt: Target sollte definiert sein
- Target muss existieren und STATE sein

⚠️ **Regel 6: INITIAL ohne eingehende Verbindungen**
```
INITIAL state has N incoming connection(s)
```
- INITIAL sollte Entry Point sein (keine Incoming)

⚠️ **Regel 7: FINAL ohne ausgehende Verbindungen**
```
FINAL state has N outgoing connection(s)
```
- FINAL sollte End Point sein (keine Outgoing)

### INFO-Level Regeln

ℹ️ **Regel 8: Entry/Exit Actions**
```
Entry action references element 'xyz' (TYPE)
Entry action uses script/expression: '...'
Exit action references element 'xyz' (TYPE)
Exit action uses script/expression: '...'
```
- Informiert über gesetzte Actions
- Unterscheidet Element-Referenz vs. Script

ℹ️ **Regel 9: NORMAL/ERROR sollten Transitions haben**
```
NORMAL state has no transitions defined
ERROR state has no transitions defined
```
- NORMAL States ohne Transitions = Endpunkt?
- ERROR States ohne Transitions = kein Recovery?

---

## FAQ

### Allgemein

**Q: Wie viele States kann ich maximal haben?**  
A: Technisch unbegrenzt, aber für Übersichtlichkeit empfehlen wir < 15 States pro State Machine. Bei komplexeren Workflows können Sie hierarchische Strukturen oder mehrere verknüpfte State Machines verwenden.

**Q: Kann ich einen State mehrfach verwenden?**  
A: Nein, jeder State ist eindeutig durch seine `element_id` identifiziert. Für ähnliche Zustände in verschiedenen Workflows erstellen Sie separate STATE-Elemente.

**Q: Was passiert wenn keine Transition zu einem Event existiert?**  
A: Der State bleibt unverändert. Logging sollte erfolgen, aber kein Fehler wird geworfen. Best Practice: Definiere alle möglichen Events explizit.

---

### State-Typen

**Q: Muss ich einen INITIAL State haben?**  
A: Ja, jede State Machine sollte einen INITIAL State haben. Der Validator prüft, dass genau ein INITIAL State existiert.

**Q: Kann ich mehrere FINAL States haben?**  
A: Ja! FINAL States repräsentieren verschiedene Endergebnisse (Approved, Rejected, Cancelled, etc.). Das ist üblich und empfohlen.

**Q: Wann sollte ich ERROR statt FINAL verwenden?**  
A: ERROR für Ausnahmesituationen mit möglichem Recovery (Timeout → Retry). FINAL für definitive Abschlüsse (Approved, Rejected).

**Q: Kann ein INITIAL State auch FINAL sein?**  
A: Nein, State-Types sind exklusiv. Ein State kann nur einen Type haben. Für Sofort-Abschlüsse: INITIAL → Transition → FINAL.

---

### Transitions

**Q: Wie viele Transitions kann ein State haben?**  
A: Unbegrenzt. Best Practice: < 10 Transitions für Lesbarkeit.

**Q: Was passiert bei mehreren Transitions mit gleichem Event?**  
A: Die erste Transition mit erfüllter Condition wird ausgeführt. Wichtig: Reihenfolge beachten!

**Q: Kann ich zu demselben State zurück-transitionieren?**  
A: Ja, "Loop-back" Transitions sind erlaubt:
```json
{
  "event": "retry",
  "target": "state_current",  // Zurück zu sich selbst
  "condition": "retry_count < 3"
}
```

**Q: Werden Exit und Entry Actions bei Loop-back ausgeführt?**  
A: Ja! Exit Action beim Verlassen, Entry Action beim erneuten Betreten.

**Q: Kann ich direkt von INITIAL zu FINAL springen?**  
A: Ja, das ist erlaubt. Beispiel: Auto-Approval bei Kleinstbeträgen.

---

### Actions

**Q: Welche Sprache verwende ich für Actions?**  
A: Das hängt von Ihrer Runtime-Umgebung ab. Typischerweise JavaScript/Python. Dokumentieren Sie die verwendete Sprache in Ihrem Projekt.

**Q: Können Actions einen Transition-Wechsel auslösen?**  
A: Nein! Actions sollten KEINE State-Änderungen vornehmen. Events triggern Transitions, nicht Actions.

**Q: Was passiert wenn eine Action fehlschlägt?**  
A: Das hängt von Ihrer Implementierung ab. Best Practice: Try-Catch mit Logging, aber State-Übergang wird nicht verhindert.

**Q: Können Entry und Exit Actions parallel laufen?**  
A: Nein. Reihenfolge: Exit Action des alten States → Transition → Entry Action des neuen States.

---

### Timeouts

**Q: Was passiert wenn Timeout und Event gleichzeitig auftreten?**  
A: Event-Transitions haben Vorrang. Timeout greift nur wenn KEIN Event-Übergang erfolgt.

**Q: Kann ich Timeout dynamisch ändern?**  
A: Nicht direkt im STATE-Element. Sie müssten den Timeout-Wert programmatisch anpassen (abhängig von Runtime).

**Q: Was ist der maximale Timeout-Wert?**  
A: Technisch unbegrenzt (int), aber sinnvoll: < 30 Tage (2592000s). Für längere Perioden nutzen Sie externe Scheduler.

**Q: Kann ein Timeout zu einem ERROR State führen?**  
A: Ja, das ist ein typischer Use-Case:
```json
"state_timeout": 3600,
"state_timeout_target": "state_timeout_error"
```

---

### Integration

**Q: Wie funktioniert STATE mit CONDITION?**  
A: CONDITION prüft Bedingungen für Verzweigungen. STATE + Conditional Transitions kann Conditions intern handhaben. Nutzen Sie CONDITION für komplexere Logik außerhalb der State Machine.

**Q: Kann ich STATE mit ERROR_HANDLER kombinieren?**  
A: Ja! ERROR_HANDLER behandelt Exceptions, STATE behandelt Workflow-States. Beispiel: ERROR_HANDLER um States für Retry-Logik.

**Q: Wie integriere ich STATE in bestehende Prozesse?**  
A: STATE-Elemente können wie andere Elemente verbunden werden. Start: Verbindung zu INITIAL State. Ende: Von FINAL States zu Folge-Prozessen.

---

### Debugging

**Q: Wie sehe ich welcher State aktiv ist?**  
A: Das hängt von Ihrer Runtime ab. Empfehlung: Logging in Entry/Exit Actions, Status-Dashboard für aktive States.

**Q: Wie debugge ich Transition-Probleme?**  
A: 
1. Validierung prüfen (alle Targets existieren?)
2. Conditions loggen (wird Condition erfüllt?)
3. Event-Namen prüfen (Tippfehler?)
4. Reihenfolge der Transitions beachten

**Q: Warum wird meine Transition nicht ausgeführt?**  
A: Häufigste Ursachen:
- Condition ist `false`
- Event-Name stimmt nicht überein
- Frühere Transition mit gleichem Event wurde gewählt
- Target existiert nicht (siehe Validierung)

---

## Roadmap v1.1

Geplante Features für zukünftige Versionen:

### History States
```json
{
  "state_type": "HISTORY",
  "state_name": "Last State"
}
```
Merkt sich letzten besuchten State für Resume-Funktionalität.

### Parallel States
```json
{
  "state_type": "PARALLEL",
  "parallel_states": ["state_a", "state_b", "state_c"]
}
```
Mehrere States gleichzeitig aktiv (z.B. parallele Genehmigungen).

### Hierarchische States
```json
{
  "state_type": "COMPOSITE",
  "sub_states": ["state_sub1", "state_sub2"]
}
```
States können andere States enthalten (State-Hierarchien).

### Transition Guards
```json
{
  "event": "approve",
  "target": "state_approved",
  "guard": "checkPermissions(user)"
}
```
Programmatische Guards zusätzlich zu Conditions.

### State Data/Context
```json
{
  "state_data": {
    "last_modified": "2025-10-18",
    "assigned_to": "user123",
    "custom_field": "value"
  }
}
```
State-spezifische Daten persistent speichern.

### Advanced Timeouts
```json
{
  "state_timeout": "2h",
  "timeout_strategy": "exponential_backoff",
  "timeout_actions": ["warn_15min", "warn_5min"]
}
```
Flexiblere Timeout-Konfiguration mit Zwischenwarnungen.

---

## Zusammenfassung

Das **STATE** Element ist ein mächtiges Werkzeug für:

✅ **Workflow-Modellierung** mit klaren Zuständen  
✅ **Event-basierte Übergänge** mit Conditions  
✅ **Automatische Actions** beim State-Wechsel  
✅ **Timeout-Handling** für SLA-Enforcement  
✅ **Strukturierte Fehlerbehandlung** mit ERROR States  

**Nächste Schritte:**
1. Erstellen Sie Ihren ersten STATE-Workflow
2. Testen Sie Transitions und Actions
3. Fügen Sie Timeout-Logik hinzu
4. Erweitern Sie mit ERROR States

**Support:**
- Dokumentation: `docs/ELEMENTS_STATE.md`
- Tests: `tests/test_state_element.py`, `tests/test_state_validation.py`
- Beispiele: `processes/test_state_canvas.vpb.json`

---

**Version 1.0** | Erstellt: 2025-10-18 | VPB Process Designer
