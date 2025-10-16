# VPB Process Designer - Intelligentes Pfeil-System

## Übersicht
Das erweiterte Pfeil-System für den VPB Process Designer implementiert intelligente Positionierung und Auswahl von Verbindungen zwischen Prozess-Elementen.

## Implementierte Features

### 1. Pfeil-Auswahl System
- **Klickbare Pfeile**: Alle Verbindungen sind nun klickbar und auswählbar
- **Visuelle Hervorhebung**: Ausgewählte Verbindungen werden rot hervorgehoben (5px Breite)
- **Normale Verbindungen**: Standardfarbe blau (#2E86AB, 3px Breite)
- **Sidebar-Integration**: Ausgewählte Verbindungen zeigen Details in der rechten Sidebar

### 2. Intelligente Pfeil-Positionierung
- **Kollisionsvermeidung**: Automatische Erkennung von Überlappungen zwischen mehreren Verbindungen
- **Offset-System**: Mehrere Verbindungen zwischen denselben Elementen werden mit 15px Abstand positioniert
- **Optimale Verbindungspunkte**: Automatische Berechnung der besten Anknüpfungspunkte an Elementen

### 3. Verschiedene Routing-Modi
- **Gerade Linien** (`straight`): Direkte Verbindung zwischen Elementen
- **Kurvige Linien** (`curved`): Bézier-Kurven für ästhetische Verbindungen
- **Intelligentes Routing** (`smart`): Automatische Wegfindung um Hindernisse

### 4. Verbindungs-Kontextmenü
- **Rechtsklick auf Pfeile**: Eigenes Kontextmenü für Verbindungen
- **Bearbeiten**: Eigenschaften der Verbindung ändern
- **Routing-Optionen**: 
  - Routing neu berechnen
  - Gerade Linie erzwingen
  - Kurvige Linie erzwingen
- **Löschen**: Verbindung mit Bestätigung entfernen

### 5. Verbindungs-Metadaten Panel
- **Eigenschaften-Anzeige**: Vollständige Details der ausgewählten Verbindung
- **Bearbeitbare Felder**: Label, Bedingung, Stil
- **Readonly-Felder**: ID, Verbindungstyp, Koordinaten
- **Aktions-Buttons**: Bearbeiten, Löschen, Erweiterte Eigenschaften

## Technische Implementation

### Kern-Methoden

```python
# Auswahl-System
_select_connection(connection_id)    # Verbindung auswählen
_deselect_connection()               # Verbindung deselektieren
_clear_element_selection()           # Element-Auswahl aufheben

# Intelligente Positionierung  
_calculate_optimal_connection_points()  # Optimale Anknüpfungspunkte
_get_connection_point_on_side()         # Punkt an Elementseite mit Offset

# Routing-System
_draw_straight_connection()          # Gerade Verbindung
_draw_curved_connection()            # Kurvige Verbindung mit Bézier
_draw_smart_connection()             # Intelligentes Routing mit Kollisionsvermeidung

# Kollisionserkennung
_is_path_clear()                     # Prüft freien Pfad
_line_intersects_rectangle()         # Linien-Rechteck-Kollision
_calculate_route_with_waypoints()    # Route mit Wegpunkten
```

### Verbindungstypen mit automatischem Offset
- **Geschäftsgang** (SEQUENCE_FLOW)
- **Information** (MESSAGE_FLOW) 
- **Zuordnung** (ASSOCIATION)
- **Rechtsweg** (LEGAL_FLOW)
- **Dokument** (DOCUMENT_FLOW)
- **Und weitere VPB-spezifische Typen**

### Offset-Algorithmus
```python
# Mehrfach-Verbindungen zwischen gleichen Elementen
connection_offset = len(existing_connections) * 15  # 15px Abstand

# Alternierende positive/negative Offsets
if len(existing_connections) % 2 == 0:
    connection_offset = connection_offset     # Positiv
else:
    connection_offset = -connection_offset    # Negativ
```

## Verwendung

### Verbindung auswählen
1. **Linksklick** auf einen Pfeil
2. Pfeil wird rot hervorgehoben
3. Details erscheinen in rechter Sidebar

### Verbindung bearbeiten
1. **Rechtsklick** auf einen Pfeil
2. Kontextmenü öffnet sich
3. "Bearbeiten..." wählen
4. Dialog zur Eigenschaftsänderung

### Mehrere Verbindungen erstellen
1. Verschiedene Verbindungstypen zwischen gleichen Elementen erstellen
2. System positioniert automatisch mit Offset
3. Keine Überlappung der Pfeile

### Routing ändern
1. Rechtsklick auf Verbindung
2. Routing-Option wählen:
   - "Routing neu berechnen" 
   - "Gerade Linie erzwingen"
   - "Kurvige Linie erzwingen"

## Vorteile

1. **Bessere Übersichtlichkeit**: Mehrere Verbindungen überlagern sich nicht mehr
2. **Interaktivität**: Pfeile sind vollwertige UI-Elemente mit Eigenschaften
3. **Flexibilität**: Verschiedene Darstellungsarten je nach Kontext
4. **CRUD-Vollständigkeit**: Verbindungen können erstellt, gelesen, bearbeitet und gelöscht werden
5. **Intelligenz**: Automatische Kollisionsvermeidung und Optimierung

## Zukünftige Erweiterungen

1. **Erweiterte Pathfinding**: A*-Algorithmus für komplexe Layouts
2. **Animierte Übergänge**: Sanfte Bewegungen bei Routing-Änderungen
3. **Verbindungs-Templates**: Vordefinierte Routing-Muster
4. **Gruppen-Operations**: Mehrere Verbindungen gleichzeitig bearbeiten
5. **Export-Integration**: Routing-Informationen in BPMN/EPK-Export
