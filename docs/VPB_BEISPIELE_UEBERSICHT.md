# VPB-Beispielprozesse - Übersicht

## Verfügbare Beispielprozesse

### 1. Baugenehmigungsverfahren (Einfach)
**Datei:** `beispielprozess_baugenehmigung_*.vpb.xml`
**Generator:** `vpb_beispielprozess_generator.py`

**Prozess-Statistik:**
- 11 Prozess-Elemente
- 11 Verbindungen
- 3 verschiedene Behörden
- Lineare Prozessstruktur mit wenigen Verzweigungen

**Elemente:**
- Start Event: Bauantrag eingereicht
- Legal Checkpoints: Formale Vollständigkeitsprüfung
- Gateways: Entscheidungspunkte für Vollständigkeit und Genehmigungsfähigkeit
- Funktionen: Materielle Prüfung, Genehmigung erteilen/ablehnen
- Geo Context: 4D-Geodaten-Abfrage
- End Events: Genehmigt/Abgelehnt

**Beteiligte Behörden:**
- Bauaufsichtsamt
- Katasteramt/Vermessungsamt
- Planungsamt

### 2. Gewerbeanmeldungsprozess (Komplex)
**Datei:** `gewerbeanmeldung_komplex_*.vpb.xml`
**Generator:** `vpb_gewerbeanmeldung_generator.py`

**Prozess-Statistik:**
- 19 Prozess-Elemente
- 23 Verbindungen (20 Sequence + 3 Information Flows)
- 5 verschiedene Behörden
- 4 parallele Prüfverfahren
- 2 DMN-Entscheidungstabellen
- 4D-Geodaten Integration

**Komplexe Strukturen:**
- **Parallele Prüfverfahren:** AND-Gateway für gleichzeitige Bearbeitung
- **Multiple Entscheidungspunkte:** XOR-Gateways für verschiedene Pfade
- **Branchenabhängige Verzweigungen:** Verschiedene Wege je nach Gewerbeart
- **Informationsflüsse:** Geodaten werden an mehrere Prüfstellen weitergeleitet

**Beteiligte Behörden:**
- Gewerbeamt (Hauptverantwortung)
- Bauaufsichtsamt (Bauliche Prüfung)
- Umweltamt (Emissionsschutz)
- Feuerwehr/Brandschutzamt (Brandschutz)
- Katasteramt/Planungsamt (Geodaten)

**Rechtliche Grundlagen:**
- Gewerbeordnung (GewO)
- Bauordnung NRW (BauO NRW)
- Bundes-Immissionsschutzgesetz (BImSchG)
- Vermessungsgesetz NRW (VermG)
- Raumordnungsgesetz (ROG)

## VPB-Features demonstriert

### Grundlegende VPB-Elemente:
- ✅ **Start/End Events:** Prozessbeginn und -ende
- ✅ **Functions:** Verwaltungsaufgaben und -tätigkeiten
- ✅ **Legal Checkpoints:** Rechtsprüfungen mit Rechtsgrundlagen
- ✅ **Gateways:** XOR- und AND-Konnektoren für Entscheidungen
- ✅ **Geo Context:** 4D-Geodaten-Integration

### Verwaltungsrechtliche Properties:
- ✅ **Competent Authority:** Zuständige Behörde je Element
- ✅ **Legal Basis:** Rechtsgrundlagen (§-Referenzen)
- ✅ **Deadline Days:** Bearbeitungsfristen in Tagen
- ✅ **Process Classification:** Verwaltungsakt-Kategorisierung

### Technische Integration:
- ✅ **XML-basiertes VPB-Format** mit Namespaces
- ✅ **DMN-Integration** für Entscheidungslogik
- ✅ **eEPK-Kompatibilität** für Standards-Compliance
- ✅ **UDS3 Knowledge Base** Referenzen

## Verwendung im VPB Process Designer

### XML-Dateien laden:
1. VPB Process Designer starten: `python vpb_process_designer.py`
2. Menü: Datei → Prozess laden
3. VPB-XML-Datei auswählen
4. Prozess wird automatisch geparst und visualisiert

### Features im Designer:
- **Grafische Ansicht:** Canvas mit Drag & Drop
- **Tabellarische Ansicht:** Strukturierte Elementliste
- **Grid-System:** Snap-to-Grid für exakte Positionierung
- **Modern GUI:** Professional Styling mit TTK
- **Console-Panel:** Live-Logging mit Statusmeldungen

## Erweiterungsmöglichkeiten

### Weitere Beispielprozesse:
- **Führerscheinantrag:** KFZ-Zulassung mit TÜV-Integration
- **Sozialleistungsantrag:** Mehrstufiger Prüfprozess
- **Umweltgenehmigung:** Komplexe UVP-Verfahren
- **Planfeststellung:** Große Infrastrukturprojekte

### Technische Erweiterungen:
- **BPMN-Export:** Kompatibilität zu Standard-Tools
- **Workflow-Engine:** Ausführbare Prozesse
- **API-Integration:** Anbindung an Verwaltungssysteme
- **Compliance-Checker:** Automatische Rechtsprüfung

## Logging und Debugging

Beide Beispiele sind vollständig mit Logging ausgestattet:
- **Log-Datei:** `vpb_process_designer.log`
- **Debug-Level:** Detaillierte Element- und Verbindungserstellung
- **Error-Handling:** Strukturierte Fehlerbehandlung
- **Erfolgsmeldungen:** "Prozess erfolgreich geladen: X Elemente, Y Verbindungen"

---
*Generiert am 22. August 2025 - UDS3 VPB Development Team*
