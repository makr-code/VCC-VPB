# ERROR_HANDLER Element - Fehlerbehandlung

**Version:** 1.0  
**Status:** ✅ Released  
**Element-Typ:** `ERROR_HANDLER`  
**Kategorie:** SPS-Logik / Fehlerbehandlung

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Handler-Typen](#handler-typen)
3. [Retry-Strategien](#retry-strategien)
4. [Timeout-Konfiguration](#timeout-konfiguration)
5. [Branching-Logik](#branching-logik)
6. [Verwendungsbeispiele](#verwendungsbeispiele)
7. [Best Practices](#best-practices)
8. [Eigenschaften-Referenz](#eigenschaften-referenz)
9. [Validierungsregeln](#validierungsregeln)
10. [FAQ](#faq)

---

## Übersicht

### Was ist ERROR_HANDLER?

Das **ERROR_HANDLER** Element ermöglicht robuste Fehlerbehandlung in VPB-Prozessen. Es bietet vier verschiedene Strategien zur Behandlung von Fehlersituationen:

- **RETRY**: Wiederhole fehlgeschlagene Operationen automatisch
- **FALLBACK**: Verwende alternative Ausführungspfade bei Fehlern
- **NOTIFY**: Informiere über Fehler, fahre aber fort
- **ABORT**: Beende den Prozess sofort bei Fehlern

### Einsatzgebiete

- **Netzwerk-Operationen**: Automatisches Retry bei temporären Verbindungsproblemen
- **API-Aufrufe**: Wiederholung bei Timeouts oder Rate-Limiting
- **Dateizugriffe**: Fallback auf alternative Speicherorte
- **Kritische Prüfungen**: Sofortiger Abbruch bei Compliance-Verstößen
- **Monitoring**: Benachrichtigung bei nicht-kritischen Fehlern

### Visuelle Darstellung

```
   ┌─────────────┐
  ╱               ╲
 │  ⚠️ RETRY      │  ← Octagon-Form (8-Ecken)
 │  Retries: 3    │  ← Zeigt Handler-Type und Retry-Count
  ╲               ╱
   └─────────────┘
```

**Farben:**
- Füllung: `#FFEBEE` (helles Rot)
- Rahmen: `#D32F2F` (kräftiges Rot)
- Icon: ⚠️ (Warnsymbol)

---

## Handler-Typen

### 1. RETRY (Wiederholung)

**Beschreibung:** Wiederholt eine fehlgeschlagene Operation automatisch mit konfigurierbaren Verzögerungen.

**Wann verwenden?**
- Temporäre Netzwerkprobleme
- API Rate Limits
- Datenbankverbindungen
- Externe Service-Aufrufe

**Konfiguration:**
```json
{
  "error_handler_type": "RETRY",
  "error_handler_retry_count": 3,
  "error_handler_retry_delay": 60,
  "error_handler_timeout": 300,
  "error_handler_on_error_target": "escalation_step",
  "error_handler_on_success_target": "next_step"
}
```

**Verhalten:**
1. Operation wird ausgeführt
2. Bei Fehler: Warte `retry_delay` Sekunden
3. Führe erneut aus (max. `retry_count` mal)
4. Bei Erfolg → `on_success_target`
5. Nach allen Versuchen fehlgeschlagen → `on_error_target`

**Exponential Backoff (empfohlen):**
- Versuch 1: Sofort
- Versuch 2: Nach 60s
- Versuch 3: Nach 120s
- Versuch 4: Nach 240s

*Hinweis: Aktuell ist nur konstante Verzögerung implementiert. Exponential Backoff ist für v1.1 geplant.*

---

### 2. FALLBACK (Alternative)

**Beschreibung:** Bei Fehler wird automatisch ein alternativer Ausführungspfad gewählt.

**Wann verwenden?**
- Primär/Sekundär Datenquellen
- Redundante Services
- Graceful Degradation
- Cache-Fallbacks

**Konfiguration:**
```json
{
  "error_handler_type": "FALLBACK",
  "error_handler_retry_count": 0,
  "error_handler_on_error_target": "fallback_path",
  "error_handler_on_success_target": "normal_path"
}
```

**Beispiel-Szenario:**
```
Primäre Datenbank
    ↓ (Fehler)
ERROR_HANDLER (FALLBACK)
    ├─ Erfolg → Weiter mit normalen Daten
    └─ Fehler → Cache-Datenbank verwenden
```

**Best Practice:**
- Teste beide Pfade regelmäßig
- Dokumentiere Unterschiede zwischen Primär/Fallback
- Logge Fallback-Nutzung für Monitoring

---

### 3. NOTIFY (Benachrichtigung)

**Beschreibung:** Loggt Fehler und sendet Benachrichtigungen, stoppt aber nicht den Prozess.

**Wann verwenden?**
- Nicht-kritische Fehler
- Monitoring und Logging
- Audit-Trails
- Performance-Tracking

**Konfiguration:**
```json
{
  "error_handler_type": "NOTIFY",
  "error_handler_log_errors": true,
  "error_handler_on_success_target": "continue_process"
}
```

**Verhalten:**
1. Operation wird ausgeführt
2. Bei Fehler: Logge Fehler, sende Notification
3. Prozess läuft normal weiter (kein Abbruch)

**Benachrichtigungs-Kanäle (konfigurierbar):**
- Log-Dateien
- E-Mail
- Slack/Teams
- Monitoring-Systeme (Prometheus, etc.)

---

### 4. ABORT (Sofortiger Abbruch)

**Beschreibung:** Stoppt den gesamten Prozess sofort bei Fehlern.

**Wann verwenden?**
- Kritische Compliance-Verstöße
- Sicherheitsrisiken
- Datenintegrität gefährdet
- Fatale Systemfehler

**Konfiguration:**
```json
{
  "error_handler_type": "ABORT",
  "error_handler_timeout": 0,
  "error_handler_log_errors": true
}
```

**Verhalten:**
1. Operation wird ausgeführt
2. Bei Fehler: Sofortiger Prozessabbruch
3. Cleanup-Routinen werden NICHT ausgeführt
4. Status: `ABORTED` mit Fehlerdetails

**Wichtig:**
- Verwende ABORT nur für wirklich kritische Fehler
- Überlege Cleanup-Mechanismen (z.B. finally-Blöcke)
- Dokumentiere Abort-Gründe für Post-Mortem

---

## Retry-Strategien

### Konstante Verzögerung

**Standard-Implementierung (v1.0):**
```
Versuch 1: t=0s
Versuch 2: t=60s
Versuch 3: t=120s
Versuch 4: t=180s
```

**Konfiguration:**
```json
{
  "error_handler_retry_delay": 60  // Konstant 60 Sekunden
}
```

**Vorteile:**
- Einfach zu verstehen
- Vorhersehbare Verzögerungen
- Gut bei konstanten Lastprofilen

**Nachteile:**
- Kann bei temporären Problemen suboptimal sein
- Keine Anpassung an Fehlertyp

---

### Exponential Backoff

**Geplant für v1.1:**
```
Versuch 1: t=0s
Versuch 2: t=1s
Versuch 3: t=2s
Versuch 4: t=4s
Versuch 5: t=8s
```

**Formel:** `delay = base_delay * 2^(attempt - 1)`

**Vorteile:**
- Reduziert Last auf fehlerhafte Services
- Bessere Chance auf Erholung
- Standard in Cloud-APIs

---

### Jitter (Zufallskomponente)

**Geplant für v1.2:**
```python
import random
actual_delay = retry_delay * (0.5 + random.random())
```

**Vorteile:**
- Verhindert "Thundering Herd" Problem
- Verteilt Last bei vielen gleichzeitigen Retries
- Empfohlen für verteilte Systeme

---

### Retry-Count Empfehlungen

| Fehlertyp | Empfohlene Retries | Delay | Grund |
|-----------|-------------------|-------|-------|
| Netzwerk-Timeout | 3-5 | 30-60s | Temporäre Störungen |
| API Rate Limit | 2-3 | 60-120s | Service-Throttling |
| Datenbankverbindung | 5-10 | 10-30s | Kurze Ausfälle |
| Datei-Locks | 10-20 | 1-5s | Schnelle Freigabe |
| externe API | 2-4 | 60-300s | Länger Ausfälle möglich |

---

## Timeout-Konfiguration

### Timeout-Werte

**Parameter:** `error_handler_timeout` (in Sekunden)

**Werte:**
- `0`: Kein Timeout (unbegrenzte Wartezeit)
- `> 0`: Maximale Wartezeit in Sekunden

### Timeout-Verhalten

```
Operation gestartet (t=0s)
    ↓
Zeit läuft (0s ... timeout)
    ↓
├─ Operation fertig vor Timeout → Erfolg
└─ Timeout erreicht → Fehler → Retry/Fallback/etc.
```

### Timeout pro Versuch vs. Gesamt-Timeout

**Aktuelles Verhalten (v1.0):**
- Timeout gilt **pro Versuch**
- Gesamt-Timeout = `timeout * retry_count`

**Beispiel:**
```json
{
  "error_handler_timeout": 60,
  "error_handler_retry_count": 3
}
```
- Versuch 1: Max. 60s
- Versuch 2: Max. 60s
- Versuch 3: Max. 60s
- **Gesamt: Max. 180s**

### Timeout = 0 (Kein Timeout)

**Warnung:** Validator warnt bei `timeout = 0`

**Wann sinnvoll:**
- Interaktive Benutzeraktionen
- Unvorhersehbare Verarbeitungszeiten
- Batch-Jobs ohne Zeitbegrenzung

**Risiken:**
- Prozess kann "hängen"
- Ressourcen-Verschwendung
- Schlechte User Experience

**Empfehlung:**
Setze immer einen vernünftigen Timeout (z.B. 300s = 5 Minuten)

---

## Branching-Logik

### On-Error-Target

**Parameter:** `error_handler_on_error_target`

**Wann wird aufgerufen:**
- Nach allen Retry-Versuchen fehlgeschlagen
- Bei ABORT-Handler sofort
- Bei FALLBACK wenn Fehler auftritt

**Beispiel:**
```json
{
  "error_handler_on_error_target": "escalation_step"
}
```

**Use Cases:**
- Eskalation an Support-Team
- Fehler-Logging Element
- Cleanup-Operationen
- Alternative Prozess-Pfade

**Wichtig:**
- Target muss existieren (sonst Validierungsfehler)
- Kann leer sein (Prozess endet dann)
- Bei RETRY/FALLBACK stark empfohlen

---

### On-Success-Target

**Parameter:** `error_handler_on_success_target`

**Wann wird aufgerufen:**
- Operation erfolgreich (auch nach Retries)
- Bei NOTIFY immer (Fehler = Erfolg)

**Beispiel:**
```json
{
  "error_handler_on_success_target": "continue_normal_flow"
}
```

**Use Cases:**
- Normaler Prozessfluss
- Erfolgs-Logging
- Metrik-Tracking
- Benachrichtigungen

**Optional:**
- Kann leer sein
- Warnung vom Validator bei einigen Handler-Typen

---

### Verzweigungsbeispiel

```
[Vorheriger Schritt]
        ↓
[ERROR_HANDLER: RETRY]
        ├─ Erfolg (nach 0-3 Retries)
        │     ↓
        │  [Normaler Pfad] (on_success_target)
        │     ↓
        │  [Weiterer Prozess...]
        │
        └─ Fehler (nach 3 Retries)
              ↓
           [Eskalation] (on_error_target)
              ↓
           [Support-Ticket erstellen]
```

---

## Verwendungsbeispiele

### Beispiel 1: Netzwerk-API mit Retry

**Szenario:** Externe API aufrufen, bei Fehler 3x wiederholen

```json
{
  "element_id": "api_call_handler",
  "element_type": "ERROR_HANDLER",
  "name": "API Retry Handler",
  "x": 400,
  "y": 300,
  "error_handler_type": "RETRY",
  "error_handler_retry_count": 3,
  "error_handler_retry_delay": 60,
  "error_handler_timeout": 300,
  "error_handler_on_error_target": "api_error_notification",
  "error_handler_on_success_target": "process_api_response",
  "error_handler_log_errors": true
}
```

**Prozessfluss:**
```
[API Call Vorbereitung]
        ↓
[ERROR_HANDLER: RETRY]
    ↓ (Versuch 1) → Fehler → Warte 60s
    ↓ (Versuch 2) → Fehler → Warte 60s
    ↓ (Versuch 3) → Fehler → Warte 60s
    ↓ (Versuch 4) → Erfolg!
        ↓
[API Response Verarbeiten]
```

---

### Beispiel 2: Datenbank-Fallback

**Szenario:** Primäre DB nicht erreichbar → Cache-DB verwenden

```json
{
  "element_id": "db_fallback",
  "element_type": "ERROR_HANDLER",
  "name": "Database Fallback",
  "error_handler_type": "FALLBACK",
  "error_handler_retry_count": 1,
  "error_handler_retry_delay": 10,
  "error_handler_timeout": 30,
  "error_handler_on_error_target": "use_cache_database",
  "error_handler_on_success_target": "continue_with_fresh_data"
}
```

**Prozessfluss:**
```
[Query Primary Database]
        ↓
[ERROR_HANDLER: FALLBACK]
        ├─ Erfolg → [Frische Daten verwenden]
        └─ Fehler → [Cache-Datenbank abfragen]
                         ↓
                    [Hinweis: Daten möglicherweise veraltet]
```

---

### Beispiel 3: Compliance-Prüfung mit Abort

**Szenario:** Bei Compliance-Verstoß Prozess sofort stoppen

```json
{
  "element_id": "compliance_check",
  "element_type": "ERROR_HANDLER",
  "name": "Compliance Checkpoint",
  "error_handler_type": "ABORT",
  "error_handler_timeout": 0,
  "error_handler_log_errors": true
}
```

**Prozessfluss:**
```
[Compliance-Prüfung durchführen]
        ↓
[ERROR_HANDLER: ABORT]
        ├─ Bestanden → [Weiter mit Prozess]
        └─ Verstoß → [PROZESS ABGEBROCHEN]
                         ↓
                    [Fehlerreport an Compliance-Team]
                    [Kein weiterer Code ausgeführt]
```

---

### Beispiel 4: Monitoring mit Notify

**Szenario:** Fehler loggen, aber Prozess fortsetzen

```json
{
  "element_id": "non_critical_monitor",
  "element_type": "ERROR_HANDLER",
  "name": "Performance Monitor",
  "error_handler_type": "NOTIFY",
  "error_handler_log_errors": true,
  "error_handler_on_success_target": "continue_process"
}
```

**Prozessfluss:**
```
[Performance-kritische Operation]
        ↓
[ERROR_HANDLER: NOTIFY]
        ├─ Erfolg → [Weiter]
        └─ Fehler → [Logge Fehler] → [Weiter trotzdem]
                         ↓
                    (Prozess wird NICHT unterbrochen)
```

---

### Beispiel 5: Komplexes Szenario mit mehreren Handlern

**Szenario:** Datei hochladen mit Retry, Fallback auf lokale Speicherung, Notify bei lokalem Save

```json
// Handler 1: Upload Retry
{
  "element_id": "upload_retry",
  "element_type": "ERROR_HANDLER",
  "name": "Cloud Upload Retry",
  "error_handler_type": "RETRY",
  "error_handler_retry_count": 3,
  "error_handler_retry_delay": 30,
  "error_handler_timeout": 120,
  "error_handler_on_error_target": "local_save_fallback",
  "error_handler_on_success_target": "upload_success_log"
}

// Handler 2: Lokaler Fallback
{
  "element_id": "local_save_fallback",
  "element_type": "ERROR_HANDLER",
  "name": "Local Storage Fallback",
  "error_handler_type": "FALLBACK",
  "error_handler_on_error_target": "critical_error_abort",
  "error_handler_on_success_target": "local_save_notify"
}

// Handler 3: Benachrichtigung
{
  "element_id": "local_save_notify",
  "element_type": "ERROR_HANDLER",
  "name": "Local Save Notification",
  "error_handler_type": "NOTIFY",
  "error_handler_on_success_target": "continue_process"
}
```

**Prozessfluss:**
```
[Datei vorbereiten]
        ↓
[Upload zu Cloud] → ERROR_HANDLER (RETRY, 3x)
        ├─ Erfolg nach max. 3 Versuchen
        │     ↓
        │  [Upload Success Log]
        │     ↓
        │  [Weiter mit Prozess]
        │
        └─ Fehler nach 3 Versuchen
              ↓
           [Lokale Speicherung] → ERROR_HANDLER (FALLBACK)
              ├─ Erfolg
              │     ↓
              │  [Local Save Notification] → ERROR_HANDLER (NOTIFY)
              │     ↓
              │  [Admin benachrichtigen]
              │     ↓
              │  [Weiter mit Prozess]
              │
              └─ Fehler
                    ↓
                 [Critical Error] → ERROR_HANDLER (ABORT)
                    ↓
                 [PROZESS ABGEBROCHEN]
```

---

## Best Practices

### 1. Wähle den richtigen Handler-Typ

✅ **DO:**
- RETRY für temporäre, wiederholbare Fehler
- FALLBACK für verfügbare Alternativen
- NOTIFY für nicht-kritische Fehler
- ABORT nur für kritische, nicht-behebbare Fehler

❌ **DON'T:**
- RETRY bei permanenten Fehlern (verschwendet Zeit)
- ABORT bei behebbaren Problemen
- NOTIFY bei kritischen Sicherheitsproblemen

---

### 2. Setze realistische Retry-Counts

✅ **DO:**
```json
{
  "error_handler_retry_count": 3,  // Vernünftig für APIs
  "error_handler_retry_delay": 60
}
```

❌ **DON'T:**
```json
{
  "error_handler_retry_count": 100,  // Zu viel!
  "error_handler_retry_delay": 1     // Zu kurz!
}
```

**Faustregel:**
- Netzwerk: 3-5 Retries
- Datenbank: 5-10 Retries
- Datei-Locks: 10-20 Retries

---

### 3. Verwende immer Timeouts

✅ **DO:**
```json
{
  "error_handler_timeout": 300  // 5 Minuten
}
```

❌ **DON'T:**
```json
{
  "error_handler_timeout": 0  // Kein Timeout = Risiko
}
```

**Empfohlene Werte:**
- Schnelle API: 30-60s
- Normale Operation: 120-300s
- Batch-Job: 600-3600s

---

### 4. Definiere klare Error/Success Targets

✅ **DO:**
```json
{
  "error_handler_on_error_target": "escalation_step",
  "error_handler_on_success_target": "continue_process"
}
```

❌ **DON'T:**
```json
{
  "error_handler_on_error_target": "",  // Was passiert bei Fehler?
  "error_handler_on_success_target": "" // Unklar!
}
```

---

### 5. Logge Fehler für Monitoring

✅ **DO:**
```json
{
  "error_handler_log_errors": true  // Immer aktiviert
}
```

**Warum?**
- Post-Mortem Analysen
- Muster-Erkennung
- Proaktive Wartung
- Compliance-Nachweise

---

### 6. Teste Error-Pfade

✅ **DO:**
- Simuliere Fehler in Test-Umgebung
- Teste alle Retry-Szenarien
- Validiere Timeout-Verhalten
- Prüfe Logging-Ausgaben

❌ **DON'T:**
- Nur Happy-Path testen
- Error-Handler als "Set and Forget"
- Produktions-Fehler als erste Tests

**Test-Checkliste:**
- [ ] Retry funktioniert nach X Versuchen
- [ ] Timeout greift nach Y Sekunden
- [ ] Error-Target wird erreicht
- [ ] Success-Target wird erreicht
- [ ] Logs werden korrekt geschrieben

---

### 7. Dokumentiere Error-Handling-Strategien

✅ **DO:**
```json
{
  "name": "Payment API Retry (3x60s)",
  "description": "Wiederholt Zahlungs-API Aufruf bei Timeout. Nach 3 Fehlversuchen → Manuelle Prüfung"
}
```

**Dokumentiere:**
- Warum dieser Handler-Typ?
- Welche Fehler werden erwartet?
- Was passiert bei Erfolg/Fehler?
- Wer wird benachrichtigt?

---

### 8. Verwende Metrics und Monitoring

**Empfohlene Metriken:**
- Anzahl Retries pro Element
- Durchschnittliche Retry-Dauer
- Error-Rate nach Retries
- Timeout-Häufigkeit
- Fallback-Nutzung

**Integration:**
```json
{
  "error_handler_log_errors": true,
  "metrics_enabled": true,
  "alert_threshold": {
    "error_rate": 0.05,  // 5% Error-Rate → Alert
    "retry_count_avg": 2  // Durchschnitt > 2 → Untersuchen
  }
}
```

---

## Eigenschaften-Referenz

### Alle ERROR_HANDLER Properties

| Property | Typ | Default | Pflicht | Beschreibung |
|----------|-----|---------|---------|--------------|
| `element_id` | string | - | ✅ | Eindeutige Element-ID |
| `element_type` | string | `"ERROR_HANDLER"` | ✅ | Immer "ERROR_HANDLER" |
| `name` | string | - | ✅ | Anzeigename |
| `x` | integer | - | ✅ | X-Koordinate |
| `y` | integer | - | ✅ | Y-Koordinate |
| `error_handler_type` | string | `"RETRY"` | ❌ | RETRY, FALLBACK, NOTIFY, ABORT |
| `error_handler_retry_count` | integer | `3` | ❌ | Anzahl Wiederholungen (0-100) |
| `error_handler_retry_delay` | integer | `60` | ❌ | Verzögerung in Sekunden (1-3600) |
| `error_handler_timeout` | integer | `300` | ❌ | Timeout in Sekunden (0=kein) |
| `error_handler_on_error_target` | string | `""` | ❌ | Element-ID für Fehlerfall |
| `error_handler_on_success_target` | string | `""` | ❌ | Element-ID für Erfolgsfall |
| `error_handler_log_errors` | boolean | `true` | ❌ | Fehler loggen? |

---

### Property-Details

#### `error_handler_type`

**Werte:** `"RETRY"`, `"FALLBACK"`, `"NOTIFY"`, `"ABORT"`

**Standard:** `"RETRY"`

**Validierung:** Muss einer der 4 Werte sein (Fehler bei ungültigem Wert)

---

#### `error_handler_retry_count`

**Bereich:** `0` bis `100`

**Standard:** `3`

**Validierung:**
- ✅ `>= 0` (OK)
- ❌ `< 0` (Fehler)

**Spezialfälle:**
- `0`: Keine Retries (nur 1 Versuch)
- `> 10`: Warnung (möglicherweise zu viel)

---

#### `error_handler_retry_delay`

**Bereich:** `1` bis `3600` Sekunden

**Standard:** `60` (1 Minute)

**Validierung:**
- ✅ `> 0` wenn `retry_count > 0` (OK)
- ❌ `<= 0` wenn `retry_count > 0` (Fehler)

**Empfehlungen:**
- API-Calls: 30-120s
- Datenbank: 10-60s
- Datei-Zugriff: 1-10s

---

#### `error_handler_timeout`

**Bereich:** `0` bis `∞` Sekunden

**Standard:** `300` (5 Minuten)

**Validierung:**
- ✅ `>= 0` (OK)
- ⚠️ `= 0` (Warnung: Kein Timeout)
- ❌ `< 0` (Fehler)

**Spezialfälle:**
- `0`: Kein Timeout (unbegrenzt)
- Sehr hoch (> 3600): Warnung

---

#### `error_handler_on_error_target`

**Typ:** Element-ID (String)

**Optional:** Ja

**Validierung:**
- Element muss existieren (Fehler wenn nicht)
- Warnung wenn leer bei RETRY/FALLBACK

**Beispiel:** `"escalation_step"`

---

#### `error_handler_on_success_target`

**Typ:** Element-ID (String)

**Optional:** Ja

**Validierung:**
- Warnung wenn Element nicht existiert
- Info wenn leer

**Beispiel:** `"continue_process"`

---

#### `error_handler_log_errors`

**Typ:** Boolean

**Standard:** `true`

**Empfehlung:** Immer `true` (für Debugging & Monitoring)

---

## Validierungsregeln

### Regel 1: Handler-Type gültig [ERROR]

**Beschreibung:** `error_handler_type` muss einer der 4 erlaubten Werte sein.

**Erlaubte Werte:** `"RETRY"`, `"FALLBACK"`, `"NOTIFY"`, `"ABORT"`

**Beispiel Fehler:**
```
❌ ERROR: Invalid handler type 'CUSTOM'
Suggestion: Use one of: RETRY, FALLBACK, NOTIFY, ABORT
```

---

### Regel 2: Retry-Count >= 0 [ERROR]

**Beschreibung:** Retry-Count darf nicht negativ sein.

**Beispiel Fehler:**
```
❌ ERROR: Retry count cannot be negative (current: -5)
Suggestion: Set retry count to 0 or higher
```

---

### Regel 3: Delay > 0 bei Retries [ERROR]

**Beschreibung:** Wenn `retry_count > 0`, muss `retry_delay > 0` sein.

**Beispiel Fehler:**
```
❌ ERROR: Retry delay must be positive when retry count > 0 (current: 0)
Suggestion: Set retry delay to a positive value (e.g., 60 seconds)
```

---

### Regel 4: Timeout >= 0 [ERROR/WARNING]

**Beschreibung:** Timeout darf nicht negativ sein. Bei 0 wird Warnung ausgegeben.

**Beispiel Fehler:**
```
❌ ERROR: Timeout cannot be negative (current: -10)
Suggestion: Set timeout to 0 (no timeout) or a positive value
```

**Beispiel Warnung:**
```
⚠️ WARNING: Timeout is disabled (0 = no timeout)
Suggestion: Consider setting a timeout to prevent indefinite waits
```

---

### Regel 5: Error-Target existiert [ERROR]

**Beschreibung:** Wenn `on_error_target` gesetzt ist, muss das Element existieren.

**Beispiel Fehler:**
```
❌ ERROR: Error target element 'nonexistent_step' does not exist
Suggestion: Select an existing element as error target or leave empty
```

---

### Regel 6: Success-Target existiert [WARNING]

**Beschreibung:** Wenn `on_success_target` gesetzt ist, sollte das Element existieren.

**Beispiel Warnung:**
```
⚠️ WARNING: Success target element 'missing_step' does not exist
Suggestion: Select an existing element as success target or leave empty
```

---

### Regel 7: Eingehende Verbindungen [WARNING]

**Beschreibung:** ERROR_HANDLER sollte eingehende Verbindungen haben.

**Beispiel Warnung:**
```
⚠️ WARNING: ERROR_HANDLER has no incoming connections
Suggestion: Connect an element to this ERROR_HANDLER to activate it
```

---

## FAQ

### F: Wann sollte ich RETRY vs. FALLBACK verwenden?

**A:** 
- **RETRY**: Wenn der Fehler temporär ist und dieselbe Operation wiederholt werden kann (z.B. Netzwerk-Timeout)
- **FALLBACK**: Wenn eine alternative Methode verfügbar ist (z.B. Cache statt Live-Datenbank)

---

### F: Was ist der Unterschied zwischen Timeout und Retry-Delay?

**A:**
- **Timeout**: Maximale Wartezeit **pro Versuch**
- **Retry-Delay**: Pause **zwischen** Versuchen

Beispiel:
```
timeout = 60s, retry_delay = 30s, retry_count = 2

Versuch 1: Max 60s → Fehler
Pause: 30s
Versuch 2: Max 60s → Fehler
Pause: 30s
Versuch 3: Max 60s → Erfolg

Gesamt: Max 180s + 60s = 240s
```

---

### F: Kann ich ERROR_HANDLER verschachteln?

**A:** Ja! Du kannst ERROR_HANDLERs hintereinanderschalten:

```
[Operation] 
    ↓
[RETRY Handler] (3 Versuche)
    ↓ (bei Fehler)
[FALLBACK Handler] (Alternative)
    ↓ (bei Fehler)
[NOTIFY Handler] (Benachrichtigung)
    ↓ (bei Fehler)
[ABORT Handler] (Kritischer Fehler)
```

---

### F: Was passiert wenn on_error_target leer ist?

**A:** Der Prozess endet an dieser Stelle. Das ist OK für:
- End-of-Flow Szenarien
- NOTIFY Handler (Prozess endet sowieso nicht)
- Explizite Prozess-Beendigungen

Validator gibt Warnung bei RETRY/FALLBACK.

---

### F: Wie teste ich ERROR_HANDLER im Development?

**A:** 

1. **Simuliere Fehler:**
```python
if os.getenv("SIMULATE_ERROR") == "true":
    raise Exception("Simulated error for testing")
```

2. **Verwende kurze Delays:**
```json
{
  "error_handler_retry_delay": 5,  // Nur 5s statt 60s
  "error_handler_retry_count": 2   // Nur 2 statt 3
}
```

3. **Logging aktivieren:**
```json
{
  "error_handler_log_errors": true
}
```

4. **Monitoring Dashboard:** Schaue Logs in Echtzeit

---

### F: Kann ich Retry-Delay dynamisch anpassen?

**A:** In v1.0 ist nur konstante Verzögerung möglich. Geplant für v1.1:

```json
{
  "error_handler_retry_strategy": "exponential_backoff",
  "error_handler_retry_base_delay": 10,
  "error_handler_retry_max_delay": 300
}
```

---

### F: Was zählt als "Fehler"?

**A:** 
- **Python:** Alle Exceptions (außer explizit gefangene)
- **HTTP:** Status Codes >= 400
- **Datenbank:** Verbindungsfehler, Timeouts
- **Custom:** Definierbar über error_conditions

---

### F: Gibt es Performance-Overhead durch ERROR_HANDLER?

**A:** Minimal:
- **Happy Path (kein Fehler):** < 1ms Overhead
- **Mit Retry:** Verzögerung = retry_delay * retry_count
- **Logging:** ~5-10ms pro Log-Eintrag

**Optimierung:**
- Verwende angemessene retry_counts
- Async-Logging (geplant v1.1)
- Batching von Metriken

---

### F: Wie kombiniere ich ERROR_HANDLER mit CONDITION?

**A:** Perfekte Kombination für komplexe Logik:

```
[Operation ausführen]
        ↓
[ERROR_HANDLER: RETRY] (technische Fehler)
        ↓ (Success)
[CONDITION] (Ergebnis-Prüfung)
        ├─ TRUE → [Weiter]
        └─ FALSE → [ERROR_HANDLER: NOTIFY] (fachlicher Fehler)
```

---

### F: Unterstützt ERROR_HANDLER Circuit Breaker Pattern?

**A:** Nicht in v1.0. Geplant für v1.2:

```json
{
  "error_handler_circuit_breaker_enabled": true,
  "error_handler_circuit_breaker_threshold": 5,
  "error_handler_circuit_breaker_timeout": 300
}
```

**Circuit Breaker Logik:**
- Nach 5 Fehlern in Folge → "Open" (stoppt Retries)
- Warte 300s
- Versuche 1x → "Half-Open"
- Erfolg → "Closed" (normal)
- Fehler → "Open" (wieder warten)

---

### F: Kann ich ERROR_HANDLER für Validierung verwenden?

**A:** Nicht empfohlen. Verwende stattdessen:
- **CONDITION** für fachliche Validierung
- **ERROR_HANDLER** für technische Fehler

**Beispiel:**
```
✅ CONDITION: "Betrag > 0"
❌ ERROR_HANDLER mit Retry für "Betrag > 0"
```

---

## Versionsverlauf

### v1.0 (Initial Release - 18.10.2025)

**Features:**
- ✅ 4 Handler-Typen (RETRY, FALLBACK, NOTIFY, ABORT)
- ✅ Retry-Configuration (Count, Delay, Timeout)
- ✅ Branching (on_error_target, on_success_target)
- ✅ Error-Logging
- ✅ Validierung (7 Regeln)
- ✅ Properties Panel Integration
- ✅ Canvas Rendering (Octagon)

**Tests:**
- ✅ 10/10 Schema-Tests
- ✅ 10/10 Validierungs-Tests
- ✅ App-Integration erfolgreich

---

### v1.1 (Geplant - Q1 2026)

**Geplante Features:**
- Exponential Backoff Retry-Strategie
- Jitter für verteilte Systeme
- Async-Logging für Performance
- Metrics & Monitoring Integration
- Gesamt-Timeout (zusätzlich zu per-attempt)
- Custom Error-Conditions

---

### v1.2 (Geplant - Q2 2026)

**Geplante Features:**
- Circuit Breaker Pattern
- Adaptive Retry (lerne aus Fehlermustern)
- Error-Correlation (gruppiere zusammenhängende Fehler)
- Advanced Notifications (Webhook, Slack, Teams)
- Retry-Queue für Batch-Processing

---

## Weiterführende Ressourcen

### Verwandte Elemente

- **CONDITION**: Fachliche Verzweigungslogik
- **COUNTER**: Schleifenzähler und Limits
- **STATE**: Zustandsverwaltung (geplant)
- **INTERLOCK**: Wechselseitige Ausschluss-Logik (geplant)

### Externe Links

- [AWS Retry Best Practices](https://docs.aws.amazon.com/general/latest/gr/api-retries.html)
- [Google Cloud Retry Strategies](https://cloud.google.com/apis/design/errors#error_retries)
- [Circuit Breaker Pattern (Martin Fowler)](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Exponential Backoff Algorithm](https://en.wikipedia.org/wiki/Exponential_backoff)

### Code-Beispiele

Siehe auch:
- `tests/test_error_handler_element.py` - Unit Tests
- `tests/test_error_handler_validation_simple.py` - Validierungs-Tests
- `processes/test_error_handler_canvas.vpb.json` - Beispiel-Prozess

---

## Support & Feedback

**Fragen oder Probleme?**
- GitHub Issues: `VCC-VPB/issues`
- Dokumentation: `docs/ELEMENTS_*.md`
- Examples: `processes/*.vpb.json`

**Feedback willkommen!**
Dieses Element ist neu (v1.0). Wir freuen uns über:
- Bug-Reports
- Feature-Requests
- Best-Practice Vorschläge
- Use-Case Beschreibungen

---

**Dokumentation aktualisiert:** 18.10.2025  
**ERROR_HANDLER Version:** 1.0  
**Status:** ✅ Production Ready
