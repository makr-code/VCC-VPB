# VPB Process Designer - XML-basierte Implementation

## ✅ Vollständige Umstellung auf VPB-XML-Format

### 🎯 Umgesetzte Features:

**1. XML-basierte Prozessspeicherung (eEPK-kompatibel):**
- **VPB-XML Schema** nach UDS3-Standard
- **Namespaces**: `urn:uds3:vpb:1.0`, DMN, eEPK-Kompatibilität
- **Strukturierte Metadaten** mit Rechtsbezug und Zuständigkeiten
- **4D-Geodaten-Integration** für räumliche Verwaltungsprozesse

**2. Beispielprozess: Baugenehmigungsverfahren:**
- **13 Prozess-Elemente** mit VPB-spezifischen Typen
- **DMN-Integration** für Entscheidungslogik
- **UDS3-Wissensbasis-Referenzen** zu Rechtsprechung
- **Compliance** mit BauO NRW und VwVfG

**3. VPB Process Designer Anpassungen:**
- **XML Load/Save** mit Backward-Compatibility zu JSON
- **Datei-Dialoge** unterstützen .vpb.xml Format
- **Notebook-System** mit Canvas und Tabellen-Ansicht bleibt erhalten
- **Grid-System** und moderne GUI bleiben funktional

**4. Multi-Format XML-Export (neu 2025-09-28):**
- **BPMN 2.0**-Kompatibilität inkl. BPMN-Diagramm (BPMN-DI) für Layout-Koordinaten
- **eEPK**-Export mit Events, Funktionen, Konnektoren und Layout
- **ATOK**-Export für bestehende Tools als Fallback

### 🗂️ XML-Struktur Beispiel:

```xml
<?xml version="1.0"?>
<vpb:Process xmlns:vpb="urn:uds3:vpb:1.0" 
             xmlns:dmn="https://www.omg.org/spec/DMN/20191111/MODEL/"
             processId="BAUANTRAG_VERFAHREN_001" version="1.0">
             
  <vpb:ProcessMetadata>
    <vpb:Name>Baugenehmigungsverfahren (vereinfacht)</vpb:Name>
    <vpb:LegalContext>BAURECHT</vpb:LegalContext>
    <vpb:LegalBasis>BauO NRW, VwVfG</vpb:LegalBasis>
    <vpb:ResponsibleAuthority>Untere Bauaufsichtsbehörde</vpb:ResponsibleAuthority>
    <vpb:TargetProcessingDays>60</vpb:TargetProcessingDays>
  </vpb:ProcessMetadata>
  
  <vpb:ProcessElements>
    <vpb:Event elementId="E001" type="START_EVENT" x="100" y="200">
      <vpb:Name>Bauantrag eingereicht</vpb:Name>
      <vpb:Description>Antragsteller reicht Bauantrag bei der zuständigen Behörde ein</vpb:Description>
      <vpb:GeoRelevance>true</vpb:GeoRelevance>
      <vpb:AdminLevel>4</vpb:AdminLevel>
    </vpb:Event>
    
    <vpb:LegalCheckpoint elementId="LC001" x="300" y="200">
      <vpb:Name>Formale Vollständigkeitsprüfung</vpb:Name>
      <vpb:LegalBasis>§ 66 BauO NRW</vpb:LegalBasis>
      <vpb:DeadlineDays>14</vpb:DeadlineDays>
      <vpb:ResponsibleAuthority>Bauaufsichtsamt</vpb:ResponsibleAuthority>
    </vpb:LegalCheckpoint>
    
    <vpb:Gateway elementId="G001" type="XOR_CONNECTOR" x="500" y="200">
      <vpb:Name>Unterlagen vollständig?</vpb:Name>
      <vpb:DecisionLogic>
        <dmn:Decision decisionId="VOLLSTÄNDIGKEIT_CHECK">
          <dmn:DecisionTable>
            <dmn:Rule>
              <dmn:InputEntry>Unterlagen_komplett == true</dmn:InputEntry>
              <dmn:OutputEntry>VOLLSTÄNDIG</dmn:OutputEntry>
            </dmn:Rule>
          </dmn:DecisionTable>
        </dmn:Decision>
      </vpb:DecisionLogic>
    </vpb:Gateway>
    
    <vpb:Function elementId="F002" x="700" y="200">
      <vpb:Name>Materielle Prüfung durchführen</vpb:Name>
      <vpb:LegalBasis>§ 70 BauO NRW</vpb:LegalBasis>
      <vpb:DeadlineDays>30</vpb:DeadlineDays>
      <vpb:KnowledgeBaseRefs>
        <vpb:KBRef refId="UDS3_BAURECHT_KOMMENTAR_MUENCH"/>
        <vpb:KBRef refId="BVERWG_2023_BAURECHT_SAMMLUNG"/>
      </vpb:KnowledgeBaseRefs>
    </vpb:Function>
    
    <vpb:GeoContext elementId="GEO001" x="700" y="120">
      <vpb:Name>4D-Geodaten-Abfrage</vpb:Name>
      <vpb:GeoData>
        <vpb:DataSource>ALKIS</vpb:DataSource>
        <vpb:DataSource>XPlanung</vpb:DataSource>
        <vpb:DataSource>3D-Stadtmodell</vpb:DataSource>
      </vpb:GeoData>
    </vpb:GeoContext>
  </vpb:ProcessElements>
  
  <vpb:ProcessFlows>
    <vpb:SequenceFlow flowId="SF001" sourceRef="E001" targetRef="LC001" type="SEQUENCE">
      <vpb:Description>Antrag eingereicht → Rechtsprüfung</vpb:Description>
    </vpb:SequenceFlow>
    <vpb:SequenceFlow flowId="IF001" sourceRef="F002" targetRef="GEO001" type="INFORMATION">
      <vpb:Description>Materielle Prüfung → Geodaten-Abfrage</vpb:Description>
    </vpb:SequenceFlow>
  </vpb:ProcessFlows>
</vpb:Process>
```

### 🔧 VPB-Element-Typen:

| Element | XML-Tag | Beschreibung |
|---------|---------|--------------|
| **Start/End Events** | `<vpb:Event>` | Prozessstart/-ende mit Geo-Relevanz |
| **Funktionen** | `<vpb:Function>` | Verwaltungstätigkeiten mit Rechtsgrundlage |
| **Rechtsprüfung** | `<vpb:LegalCheckpoint>` | Compliance-Prüfungen |
| **Entscheidungen** | `<vpb:Gateway>` | DMN-basierte Entscheidungslogik |
| **Geodaten** | `<vpb:GeoContext>` | 4D-räumliche Bezüge |

### 🎨 VPB Process Designer Features:

**Dual-View System:**
- **🎨 Grafischer Editor**: Drag & Drop mit Grid-System
- **📊 Prozess-Tabelle**: Strukturierte Datenansicht

**XML-Integration:**
- **Speichern**: .vpb.xml Format (primär)
- **Laden**: .vpb.xml + .vpb.json (Backward-Compatibility)
- **Export**: CSV, Markdown, BPMN 2.0, eEPK, ATOK

**Moderne GUI:**
- **Toolbar**: Hamburger-Menü, Grid-Controls, View-Toggle
- **Console**: VPB-Befehle mit Grid-Steuerung
- **Status**: Live-Updates für Elemente und Verbindungen

### 📁 Dateien:

- `vpb_process_designer.py` - Haupt-Designer (XML-basiert)
- `vpb_beispielprozess_generator.py` - XML-Beispielprozess-Generator  
- `beispielprozess_baugenehmigung_*.vpb.xml` - Generierte Beispiele
- `UDS3_VERWALTUNGSPROZESS_BESCHREIBUNGSSPRACHE_VPB.md` - VPB-Standard

### 🚀 Verwendung:

1. **Beispielprozess erstellen:**
   ```bash
   python vpb_beispielprozess_generator.py
   ```

2. **VPB Designer starten:**
   ```bash
   python vpb_process_designer.py
   ```

3. **XML-Datei laden:**
   - Datei → Öffnen → beispielprozess_baugenehmigung_*.vpb.xml
   - Oder Console: `load beispielprozess_baugenehmigung`

### 💡 Vorteile der XML-Implementation:

- **Standards-Konformität** mit eEPK und BPMN
- **Rechtliche Nachverfolgbarkeit** durch Metadaten
- **Tool-Interoperabilität** mit anderen BPM-Systemen
- **Validierung** gegen XSD-Schema möglich
- **Erweiterbarkeit** für weitere Verwaltungsdomänen

Die VPB-XML-Implementation ist jetzt vollständig einsatzbereit und entspricht den deutschen Verwaltungsstandards! 🎯✨
