#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Element Info/Help System
========================

Provides detailed information about VPB process elements.
Used in Properties Panel to show context-sensitive help.
"""

ELEMENT_INFO = {
    # SPS Logic Elements
    "COUNTER": {
        "title": "🔢 Zähler (Counter)",
        "description": "Zählt Durchläufe, Ereignisse oder Wiederholungen in Ihrem Prozess.",
        "when_to_use": [
            "Begrenzen Sie Wiederholungen (z.B. max. 3 Mahnungen)",
            "Eskalieren Sie nach X Versuchen",
            "Kontrollieren Sie Freigabe-Runden",
            "Überwachen Sie Schwellenwerte"
        ],
        "how_it_works": [
            "Bei jedem Durchlauf wird der Zähler erhöht (UP) oder verringert (DOWN)",
            "Bei Erreichen des Maximums kann automatisch eskaliert werden",
            "Optional: Automatisches Zurücksetzen für Endlos-Loops"
        ],
        "key_features": [
            "3 Typen: UP (aufwärts), DOWN (abwärts), UP_DOWN (bidirektional)",
            "Automatische Eskalation via 'Element bei Max'",
            "Visuell: Zeigt aktuellen Wert auf Canvas (z.B. '2/3')",
            "Validierung: Prüft Verbindungen und Wert-Bereiche"
        ],
        "examples": [
            "Mahnungsprozess: Max. 3 Mahnungen, dann Inkasso",
            "Freigabe-Workflow: Max. 5 Ablehnungen erlaubt",
            "Monitoring: Alle 10 Durchläufe Report erstellen"
        ],
        "tips": [
            "💡 Verwenden Sie 'Reset bei Max' für Endlos-Prozesse",
            "⚠️ Maximum muss größer als Start sein",
            "🎯 'Element bei Max' ermöglicht direkte Eskalation ohne Gateway"
        ]
    },
    
    "CONDITION": {
        "title": "🔀 Bedingung (Condition)",
        "description": "Prüft eine oder mehrere Bedingungen und verzweigt den Prozess basierend auf TRUE/FALSE.",
        "when_to_use": [
            "Entscheidungen basierend auf Feld-Werten treffen",
            "Komplexe Bedingungen mit mehreren Checks kombinieren",
            "Prozess in TRUE- und FALSE-Pfade aufteilen",
            "Alternative zu manuellen Gateway-Konstruktionen"
        ],
        "how_it_works": [
            "Jeder Check prüft: Feld-Wert Operator Vergleichswert (z.B. 'betrag <= 5000')",
            "Mehrere Checks werden mit AND (alle müssen wahr sein) oder OR (einer muss wahr sein) kombiniert",
            "TRUE-Fall: Springt zu 'TRUE Target'-Element",
            "FALSE-Fall: Springt zu 'FALSE Target'-Element"
        ],
        "key_features": [
            "Beliebig viele Checks kombinierbar",
            "8 Operatoren: ==, !=, <, >, <=, >=, contains, regex",
            "4 Datentypen: string, number, date, boolean",
            "AND/OR-Logik für flexible Bedingungen",
            "Visuell: Zeigt Anzahl Checks auf Canvas (z.B. '2 Checks')"
        ],
        "examples": [
            "Betrag prüfen: 'betrag <= 5000' AND 'status == neu' → Automatische Genehmigung",
            "Priorität: 'priority == high' OR 'urgent == true' → Express-Bearbeitung",
            "Datum: 'deadline < 2025-12-31' → Frist-Warnung"
        ],
        "tips": [
            "💡 AND = Alle Bedingungen müssen erfüllt sein (strenger)",
            "💡 OR = Mindestens eine Bedingung muss erfüllt sein (lockerer)",
            "⚠️ Mindestens 1 Check ist erforderlich",
            "🎯 TRUE und FALSE Targets sollten immer gesetzt sein",
            "📊 Bei vielen Checks: Erwägen Sie Aufteilung in mehrere CONDITION-Elemente"
        ]
    },
    
    "ERROR_HANDLER": {
        "title": "⚠️ Fehlerbehandlung (Error Handler)",
        "description": "Behandelt Fehler strukturiert mit Retry-Logik, Fallback-Pfaden oder Eskalation.",
        "when_to_use": [
            "Netzwerk-Operationen mit temporären Ausfällen",
            "API-Aufrufe mit Timeouts oder Rate-Limiting",
            "Datenbankverbindungen mit Retry-Bedarf",
            "Kritische Prüfungen mit Compliance-Anforderungen",
            "Nicht-kritische Fehler, die geloggt werden sollen"
        ],
        "how_it_works": [
            "RETRY: Wiederholt fehlgeschlagene Operationen automatisch (1-100x)",
            "FALLBACK: Wechselt zu alternativen Ausführungspfaden bei Fehlern",
            "NOTIFY: Loggt Fehler, fährt aber im Prozess fort",
            "ABORT: Beendet Prozess sofort bei kritischen Fehlern",
            "Konfigurierbare Retry-Verzögerung (1-3600 Sekunden)",
            "Separate Targets für Erfolg und Fehler"
        ],
        "key_features": [
            "4 Handler-Typen: RETRY, FALLBACK, NOTIFY, ABORT",
            "Retry-Count: 0-100 Versuche",
            "Retry-Delay: Wartezeit zwischen Versuchen (1-3600s)",
            "Timeout pro Versuch definierbar",
            "On-Error-Target: Wohin nach Fehler springen",
            "On-Success-Target: Wohin nach Erfolg springen",
            "Fehler-Logging aktivierbar",
            "Visuell: Rotes Oktagon mit ⚠️ Symbol"
        ],
        "examples": [
            "API-Call mit Retry: RETRY-Typ, 3 Versuche, 60s Delay → Bei Erfolg weiter, bei Fehler Support-Eskalation",
            "Datenbank-Fallback: FALLBACK-Typ → Bei Fehler auf Cache-DB ausweichen",
            "Monitoring: NOTIFY-Typ → Fehler loggen, Prozess läuft weiter",
            "Compliance: ABORT-Typ → Bei Rechtsverstoß sofortiger Prozess-Stopp"
        ],
        "tips": [
            "💡 RETRY für temporäre Probleme (Netzwerk, API Rate Limits)",
            "💡 FALLBACK für redundante Systeme (Primär/Sekundär-Quellen)",
            "💡 NOTIFY für nicht-kritische Fehler (Performance-Monitoring)",
            "💡 ABORT für kritische Fehler (Security, Compliance)",
            "⚠️ Exponential Backoff empfohlen: 1s → 2s → 4s → 8s",
            "🎯 On-Error und On-Success Targets immer setzen für klare Flows",
            "📊 Max. 3-5 Retries bei API-Calls (mehr = unnötige Last)"
        ]
    },
    
    "STATE": {
        "title": "🟢 Zustand (State)",
        "description": "Modelliert Zustandsautomaten (State Machines) mit Transitionen zwischen definierten States.",
        "when_to_use": [
            "Workflow-Management mit klaren Status (Neu → In Prüfung → Genehmigt)",
            "Genehmigungs-Prozesse mit mehreren Stufen",
            "Ticket-Systeme (Offen → In Bearbeitung → Geschlossen)",
            "Prozess-Orchestrierung mit komplexen Zuständen",
            "Fehlerbehandlung mit strukturierten Error-States"
        ],
        "how_it_works": [
            "Jeder STATE repräsentiert einen definierten Zustand im Workflow",
            "Transitionen definieren erlaubte Übergänge zwischen States",
            "Entry-Actions werden beim Betreten eines States ausgeführt",
            "Exit-Actions werden beim Verlassen eines States ausgeführt",
            "Timeout kann automatischen Übergang auslösen",
            "Bedingungen steuern, welche Transition gewählt wird"
        ],
        "key_features": [
            "4 State-Typen: INITIAL (Start), NORMAL (Standard), FINAL (Ende), ERROR (Fehler)",
            "Transitionen mit Bedingungen und Labels",
            "Entry-Actions: Code beim Betreten des States",
            "Exit-Actions: Code beim Verlassen des States",
            "Timeout: Automatischer Übergang nach X Sekunden",
            "State-Name eindeutig identifiziert den Zustand",
            "Visuell: Grünes abgerundetes Rechteck mit Icon (▶️/⬤/🏁/❌)"
        ],
        "examples": [
            "Antrags-Workflow: INITIAL 'eingereicht' → NORMAL 'in_pruefung' → NORMAL 'nachforderung' → FINAL 'genehmigt' / ERROR 'abgelehnt'",
            "Ticket-System: INITIAL 'neu' → NORMAL 'zugewiesen' → NORMAL 'in_bearbeitung' → FINAL 'geschlossen'",
            "Bestellprozess: 'neu' → 'bezahlt' → 'versandt' → 'zugestellt' → 'abgeschlossen'",
            "Mit Timeout: State 'wartend' mit 3600s Timeout → automatisch zu 'eskaliert'"
        ],
        "tips": [
            "💡 INITIAL State = Einstiegspunkt (nur einer pro State Machine)",
            "💡 NORMAL States = Haupt-Workflow-Zustände",
            "💡 FINAL State = Erfolgreicher Abschluss",
            "💡 ERROR State = Fehler-/Abbruch-Zustand",
            "⚠️ Genau ein INITIAL State pro Prozess erforderlich",
            "⚠️ State-Namen müssen eindeutig sein (keine Duplikate)",
            "🎯 Mindestens eine Transition für nicht-FINAL States",
            "📊 Transition-Bedingungen sollten alle Fälle abdecken (vollständig)",
            "🔄 Entry/Exit-Actions für Logging, Benachrichtigungen, Cleanup"
        ]
    },
    
    "INTERLOCK": {
        "title": "🔒 Sperre (Interlock)",
        "description": "Synchronisiert Ressourcen-Zugriff mit MUTEX (exklusiv) oder SEMAPHORE (begrenzt parallel).",
        "when_to_use": [
            "Datenbank-Connection-Pools (max. N gleichzeitige Verbindungen)",
            "API Rate Limiting (max. X Requests pro Zeiteinheit)",
            "Dateizugriffe (exklusives Schreiben, paralleles Lesen)",
            "Kritische Sektionen (nur ein Prozess gleichzeitig)",
            "Ressourcen-Koordination zwischen parallelen Prozessen"
        ],
        "how_it_works": [
            "MUTEX: Nur ein Prozess gleichzeitig (max_count = 1)",
            "SEMAPHORE: Begrenzte Anzahl gleichzeitiger Zugriffe (max_count > 1)",
            "Resource-ID identifiziert die gemeinsame Ressource",
            "Lock wird vor Ressourcen-Nutzung erworben",
            "Bei Nicht-Verfügbarkeit: Warte oder springe zu 'Locked Target'",
            "Auto-Release: Lock wird automatisch nach Element freigegeben",
            "Timeout: Maximale Wartezeit in Sekunden"
        ],
        "key_features": [
            "2 Typen: MUTEX (exklusiv) und SEMAPHORE (begrenzt parallel)",
            "Resource-ID: Eindeutiger Name der zu schützenden Ressource",
            "Max-Count: Maximale gleichzeitige Zugriffe (MUTEX=1, SEMAPHORE>1)",
            "Timeout: Maximale Wartezeit (0 = unbegrenzt, >0 = Sekunden)",
            "Locked-Target: Wohin springen, wenn Lock nicht verfügbar",
            "Auto-Release: Automatisches Freigeben nach Element (empfohlen)",
            "Visuell: Orange abgerundetes Rechteck mit 🔒/🔓 Symbol",
            "Deadlock-Prevention: Warnung bei mehreren Locks"
        ],
        "examples": [
            "DB-Pool: SEMAPHORE, resource_id='db_pool', max_count=5 → Max. 5 DB-Verbindungen gleichzeitig",
            "API Rate-Limit: SEMAPHORE, resource_id='api_rate', max_count=10 → Max. 10 API-Calls parallel",
            "Datei-Schreiben: MUTEX, resource_id='config.json', max_count=1 → Exklusiver Schreibzugriff",
            "Kritische Sektion: MUTEX, resource_id='payment_processing', timeout=30 → Nur ein Payment gleichzeitig"
        ],
        "tips": [
            "💡 MUTEX = Exklusiver Zugriff (max_count immer 1)",
            "💡 SEMAPHORE = Begrenzte parallele Zugriffe (max_count > 1)",
            "💡 Resource-ID muss eindeutig sein für jede Ressource",
            "💡 Auto-Release=true empfohlen (automatisches Freigeben)",
            "⚠️ Timeout=0 = Unbegrenztes Warten (kann Deadlocks verursachen)",
            "⚠️ Mehrere INTERLOCKs mit gleicher Resource-ID koordinieren sich",
            "🎯 Locked-Target für Alternative bei Nicht-Verfügbarkeit setzen",
            "📊 Deadlock-Vermeidung: Immer in gleicher Reihenfolge locken",
            "🔄 Timeout zwischen 5-300 Sekunden je nach Szenario"
        ]
    },
    
    # BPMN Basic Elements
    "START_EVENT": {
        "title": "▶️ Start-Ereignis",
        "description": "Markiert den Beginn eines Prozesses oder Teilprozesses.",
        "when_to_use": [
            "Am Anfang jedes Hauptprozesses",
            "Als Einstiegspunkt für Subprozesse",
            "Nach einer Verzweigung als neuer Start-Punkt"
        ],
        "how_it_works": [
            "Kennzeichnet den initialen Auslöser des Prozesses",
            "Kann mit Trigger-Ereignissen verbunden sein (Antrag, Timer, Signal)",
            "Startet den Prozessfluss"
        ],
        "key_features": [
            "Visuell: Grüner Kreis",
            "Keine eingehenden Verbindungen erlaubt",
            "Mindestens eine ausgehende Verbindung empfohlen"
        ]
    },
    
    "END_EVENT": {
        "title": "⏹️ End-Ereignis",
        "description": "Markiert das Ende eines Prozesses oder Teilprozesses.",
        "when_to_use": [
            "Am Ende jedes Hauptprozesses",
            "Nach Abschluss aller Aktivitäten",
            "Bei verschiedenen Prozess-Ausgängen (Erfolg, Abbruch, Fehler)"
        ],
        "how_it_works": [
            "Beendet den Prozessfluss",
            "Kann Ergebnis-Status enthalten",
            "Terminiert aktive Prozess-Instanz"
        ],
        "key_features": [
            "Visuell: Roter Kreis mit dickem Rand",
            "Keine ausgehenden Verbindungen erlaubt",
            "Mindestens eine eingehende Verbindung empfohlen"
        ]
    },
    
    "FUNCTION": {
        "title": "📋 Funktion/Aktivität",
        "description": "Repräsentiert eine Aufgabe, Tätigkeit oder Funktion im Prozess.",
        "when_to_use": [
            "Für jeden Arbeitsschritt oder Aktivität",
            "Manuelle oder automatisierte Aufgaben",
            "Verarbeitung, Prüfung, Bearbeitung"
        ],
        "key_features": [
            "Visuell: Abgerundetes Rechteck",
            "Kann Verantwortliche und Fristen enthalten",
            "Ein- und ausgehende Verbindungen erlaubt"
        ]
    },
    
    "GATEWAY": {
        "title": "◇ Gateway/Entscheidung",
        "description": "Verzweigungspunkt im Prozess für Entscheidungen oder parallele Pfade.",
        "when_to_use": [
            "Für einfache Ja/Nein-Entscheidungen",
            "Parallele Ausführung (AND-Gateway)",
            "Alternativen (XOR-Gateway)",
            "Optional: Mehrfach-Wahl (OR-Gateway)"
        ],
        "tips": [
            "💡 Für komplexe Bedingungen: Verwenden Sie CONDITION-Element",
            "⚠️ AND-Gateway: Alle Pfade müssen zusammengeführt werden",
            "🎯 XOR-Gateway: Genau ein Pfad wird gewählt"
        ]
    },
    
    # EPK/VPB Elements
    "EVENT": {
        "title": "⚡ Ereignis",
        "description": "Repräsentiert ein Ereignis, das einen Zustand oder eine Situation beschreibt.",
        "when_to_use": [
            "Als Auslöser für Prozessschritte",
            "Zwischen Funktionen als Zustandsbeschreibung",
            "Für Trigger-Ereignisse (Antrag eingegangen, Frist abgelaufen)"
        ],
        "how_it_works": [
            "Beschreibt einen eingetretenen Zustand",
            "EPK-Regel: Ereignis → Funktion → Ereignis",
            "Keine Entscheidungslogik (passiv)"
        ],
        "key_features": [
            "Visuell: Rotes Oval",
            "Passives Element (beschreibend)",
            "Wichtig für EPK-konforme Modellierung"
        ],
        "examples": [
            "Antrag eingegangen",
            "Prüfung abgeschlossen",
            "Frist abgelaufen",
            "Genehmigung erteilt"
        ],
        "tips": [
            "💡 Ereignisse beschreiben WAS passiert ist (Vergangenheit)",
            "💡 Funktionen beschreiben WAS getan wird (Tätigkeit)",
            "⚠️ EPK: Immer Ereignis-Funktion-Ereignis abwechselnd"
        ]
    },
    
    "GROUP": {
        "title": "📦 Gruppe/Container",
        "description": "Gruppiert mehrere Elemente visuell zu einer logischen Einheit.",
        "when_to_use": [
            "Zusammengehörige Prozessschritte gruppieren",
            "Teilprozesse visuell abgrenzen",
            "Verantwortlichkeitsbereiche markieren",
            "Komplexe Prozesse strukturieren"
        ],
        "how_it_works": [
            "Wählen Sie mehrere Elemente aus",
            "Menü 'Bearbeiten' → 'Gruppe aus Auswahl bilden'",
            "Gestrichelter Rahmen umschließt Mitglieder",
            "Mitglieder bleiben editierbar"
        ],
        "key_features": [
            "Visuell: Grauer gestrichelter Rahmen",
            "Nur visuell (keine funktionale Logik)",
            "Kann benannt werden",
            "Mitglieder einzeln verschiebbar"
        ],
        "examples": [
            "Genehmigungs-Workflow gruppieren",
            "Alle Prüfschritte zusammenfassen",
            "Abteilungs-spezifische Schritte markieren"
        ],
        "tips": [
            "💡 Für Zeitsteuerung: Verwenden Sie TIME_LOOP statt GROUP",
            "💡 Auflösen: Gruppe auswählen → 'Gruppe auflösen'",
            "⚠️ Nur zur visuellen Strukturierung, keine Ausführungslogik"
        ]
    },
    
    "ORGANIZATION_UNIT": {
        "title": "🏢 Organisationseinheit",
        "description": "Repräsentiert eine organisatorische Einheit (Abteilung, Team, Rolle).",
        "when_to_use": [
            "Zuständigkeiten kennzeichnen",
            "Verantwortliche Stelle markieren",
            "Organisationsstrukturen abbilden"
        ],
        "key_features": [
            "Visuell: Graues Rechteck",
            "Kann mit Funktionen verbunden werden",
            "Zeigt Verantwortlichkeiten"
        ],
        "examples": [
            "Sachbearbeitung",
            "Teamleitung",
            "Rechtsabteilung",
            "Buchhaltung"
        ]
    },
    
    "INFORMATION_OBJECT": {
        "title": "📄 Informationsobjekt",
        "description": "Repräsentiert Dokumente, Daten oder Informationen im Prozess.",
        "when_to_use": [
            "Dokumente als Input/Output markieren",
            "Datenobjekte visualisieren",
            "Informationsflüsse verdeutlichen"
        ],
        "key_features": [
            "Visuell: Gelbe Raute",
            "Wird oft mit Funktionen verbunden",
            "Zeigt Daten-Dependencies"
        ],
        "examples": [
            "Antragsformular",
            "Genehmigungsbescheid",
            "Prüfbericht",
            "Akte"
        ]
    },
    
    "AND_CONNECTOR": {
        "title": "∧ UND-Verknüpfung",
        "description": "Parallele Verzweigung oder Zusammenführung - ALLE Pfade werden ausgeführt.",
        "when_to_use": [
            "Parallele Bearbeitung mehrerer Aufgaben",
            "Alle Pfade müssen durchlaufen werden",
            "Synchronisation nach paralleler Ausführung"
        ],
        "how_it_works": [
            "Split: Ein Eingang → Mehrere Ausgänge (alle parallel)",
            "Join: Mehrere Eingänge → Ein Ausgang (wartet auf alle)",
            "Alle Zweige werden ausgeführt"
        ],
        "key_features": [
            "Visuell: Grüner Kreis mit '+' oder '∧'",
            "Split: Startet parallele Pfade",
            "Join: Wartet auf alle Pfade"
        ],
        "examples": [
            "Parallele Prüfung durch mehrere Stellen",
            "Gleichzeitige Benachrichtigungen",
            "Mehrere Dokumente parallel erstellen"
        ],
        "tips": [
            "💡 Nach AND-Split immer AND-Join verwenden",
            "⚠️ Join wartet auf ALLE Pfade (kann Deadlock verursachen)",
            "🎯 Für unabhängige parallele Tasks"
        ]
    },
    
    "OR_CONNECTOR": {
        "title": "∨ ODER-Verknüpfung",
        "description": "Bedingte Verzweigung - EIN ODER MEHRERE Pfade werden ausgeführt.",
        "when_to_use": [
            "Mehrere optionale Pfade",
            "Einer oder mehrere Zweige aktiv",
            "Flexible Verzweigung"
        ],
        "how_it_works": [
            "Mindestens ein Pfad wird gewählt",
            "Mehrere Pfade können gleichzeitig aktiv sein",
            "Flexibler als XOR, strukturierter als AND"
        ],
        "key_features": [
            "Visuell: Oranger Kreis mit 'O' oder '∨'",
            "1 bis N Pfade aktiv",
            "Seltener verwendet als XOR/AND"
        ]
    },
    
    "XOR_CONNECTOR": {
        "title": "⊕ Exklusiv-ODER (XOR)",
        "description": "Exklusive Verzweigung - GENAU EIN Pfad wird gewählt.",
        "when_to_use": [
            "Entweder-Oder Entscheidungen",
            "Genau eine Alternative wählen",
            "Status-basierte Verzweigung"
        ],
        "how_it_works": [
            "Genau ein Ausgang wird gewählt",
            "Basiert auf Bedingungen oder Daten",
            "Klassische If-Then-Else Logik"
        ],
        "key_features": [
            "Visuell: Rote Raute mit 'X' oder '⊕'",
            "Exakt ein Pfad aktiv",
            "Häufigster Gateway-Typ"
        ],
        "examples": [
            "Genehmigt → JA oder NEIN",
            "Betrag: Hoch, Mittel, Niedrig (nur eines)",
            "Status: Neu, In Bearbeitung, Abgeschlossen"
        ],
        "tips": [
            "💡 Für komplexe Bedingungen: CONDITION-Element verwenden",
            "⚠️ Alle Ausgangs-Bedingungen müssen eindeutig sein",
            "🎯 Default-Pfad vorsehen für unerwartete Fälle"
        ]
    },
    
    "SUBPROCESS": {
        "title": "🔗 Subprozess (Referenz)",
        "description": "Referenziert einen anderen Prozess, der hier ausgeführt wird.",
        "when_to_use": [
            "Wiederverwendbare Prozess-Teile",
            "Komplexe Prozesse modularisieren",
            "Referenz auf externe Prozesse"
        ],
        "key_features": [
            "Visuell: Gestricheltes Rechteck",
            "Verweist auf separaten Prozess",
            "Kann Parameter übergeben"
        ],
        "examples": [
            "Standard-Prüfverfahren",
            "Wiederverwendbare Genehmigungs-Workflows",
            "Gemeinsame Benachrichtigungs-Prozesse"
        ]
    },
    
    "LEGAL_CHECKPOINT": {
        "title": "⚖️ Rechtsprüfung",
        "description": "Kennzeichnet eine rechtliche Prüfung oder Compliance-Check.",
        "when_to_use": [
            "Rechtmäßigkeitsprüfungen",
            "Compliance-Checks",
            "Gesetzeskonformitäts-Prüfung"
        ],
        "key_features": [
            "Visuell: Lila Hexagon",
            "Markiert rechtliche Prüfpunkte",
            "Wichtig für Nachvollziehbarkeit"
        ],
        "examples": [
            "Datenschutz-Prüfung (DSGVO)",
            "Vergaberechts-Konformität",
            "Formelle Rechtmäßigkeit"
        ]
    },
    
    "DEADLINE": {
        "title": "⏱️ Frist",
        "description": "Markiert eine zeitliche Deadline oder Frist im Prozess.",
        "when_to_use": [
            "Gesetzliche Fristen kennzeichnen",
            "SLA-Zeitpunkte markieren",
            "Zeitkritische Punkte hervorheben"
        ],
        "key_features": [
            "Visuell: Oranges Rechteck",
            "Kann Datum/Dauer enthalten",
            "Wichtig für Fristenkontrolle"
        ],
        "examples": [
            "Widerspruchsfrist (1 Monat)",
            "Bearbeitungsfrist (2 Wochen)",
            "Bescheid-Zustellung (3 Tage)"
        ]
    },
    
    "COMPETENCY_CHECK": {
        "title": "✓ Zuständigkeitsprüfung",
        "description": "Prüft die örtliche, sachliche oder funktionale Zuständigkeit.",
        "when_to_use": [
            "Zuständigkeitsklärung",
            "Weiterleitung an richtige Stelle",
            "Kompetenzprüfung"
        ],
        "key_features": [
            "Visuell: Lila Rechteck",
            "Prüft Zuständigkeit",
            "Kann Weiterleitungen auslösen"
        ],
        "examples": [
            "Örtliche Zuständigkeit prüfen",
            "Fachliche Zuständigkeit klären",
            "An zuständige Behörde weiterleiten"
        ]
    },
    
    "GEO_CONTEXT": {
        "title": "🌍 Geo-Kontext",
        "description": "Verknüpft Prozessschritt mit geografischem Kontext.",
        "when_to_use": [
            "Standort-abhängige Prozesse",
            "Regionale Besonderheiten",
            "Geodaten-Bezüge"
        ],
        "key_features": [
            "Visuell: Blaues Rechteck",
            "Kann Koordinaten enthalten",
            "Zeigt räumlichen Bezug"
        ],
        "examples": [
            "Baugebiet (Flurstück)",
            "Zuständigkeitsbereich",
            "Geografische Referenz"
        ]
    },
    
    # Time Elements
    "TIMER": {
        "title": "⏰ Timer/Zeitgeber",
        "description": "Wartet für eine bestimmte Zeit oder bis zu einem Termin.",
        "when_to_use": [
            "Wartezeiten (z.B. 14 Tage bis Mahnung)",
            "Termingebundene Aktionen",
            "Verzögerungen im Prozess"
        ],
        "key_features": [
            "Visuell: Uhr-Symbol",
            "Definiert Wartezeit in Tagen/Stunden",
            "Kann relativen oder absoluten Zeitpunkt haben"
        ]
    },
    
    "TIME_LOOP": {
        "title": "🔁 Zeitschleife",
        "description": "Wiederholt einen Prozess-Teil in regelmäßigen Intervallen oder nach Plan.",
        "when_to_use": [
            "Regelmäßige Prüfungen (täglich, wöchentlich)",
            "Monitoring-Prozesse",
            "Periodische Reports",
            "Cron-basierte Ausführung"
        ],
        "key_features": [
            "4 Loop-Typen: Interval, Cron, Date, Relative",
            "Max. Iterationen definierbar",
            "Visuell: Kreispfeil-Symbol"
        ]
    }
}


def get_element_info(element_type: str) -> dict:
    """
    Get info/help for an element type.
    
    Args:
        element_type: Type of element (e.g., "COUNTER", "CONDITION")
        
    Returns:
        Dictionary with info sections or default message
    """
    return ELEMENT_INFO.get(element_type, {
        "title": f"ℹ️ {element_type}",
        "description": "Prozess-Element",
        "when_to_use": ["Noch keine detaillierte Hilfe verfügbar."],
        "how_it_works": [],
        "key_features": [],
        "examples": [],
        "tips": []
    })


def format_element_help(element_type: str) -> str:
    """
    Format element info as readable text for display.
    
    Args:
        element_type: Type of element
        
    Returns:
        Formatted help text
    """
    info = get_element_info(element_type)
    
    lines = []
    lines.append(info["title"])
    lines.append("=" * 50)
    lines.append("")
    
    if info["description"]:
        lines.append(info["description"])
        lines.append("")
    
    if info["when_to_use"]:
        lines.append("📌 WANN VERWENDEN:")
        for item in info["when_to_use"]:
            lines.append(f"  • {item}")
        lines.append("")
    
    if info["how_it_works"]:
        lines.append("⚙️ WIE ES FUNKTIONIERT:")
        for item in info["how_it_works"]:
            lines.append(f"  • {item}")
        lines.append("")
    
    if info["key_features"]:
        lines.append("✨ HAUPTFUNKTIONEN:")
        for item in info["key_features"]:
            lines.append(f"  • {item}")
        lines.append("")
    
    if info["examples"]:
        lines.append("💡 BEISPIELE:")
        for item in info["examples"]:
            lines.append(f"  • {item}")
        lines.append("")
    
    if info["tips"]:
        lines.append("🎓 TIPPS & HINWEISE:")
        for item in info["tips"]:
            lines.append(f"  {item}")
        lines.append("")
    
    return "\n".join(lines)
