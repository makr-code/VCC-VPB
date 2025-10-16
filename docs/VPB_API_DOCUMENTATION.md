# VPB API Endpoints - Dokumentation

## Übersicht der verfügbaren VPB Modi

Die erweiterte FastAPI bietet jetzt umfassende VPB (Verwaltungsprozess-Beschreibungssprache) Unterstützung mit verschiedenen Betriebsmodi.

## 🔍 Verfügbare Modi abrufen

**Endpoint:** `GET /vpb/modes`

**Beschreibung:** Liefert eine Übersicht aller verfügbaren VPB Modi mit deren Status

**Response:**
```json
{
  "modes": [
    {
      "mode": "ASK",
      "display_name": "VPB Prozess Abfrage", 
      "description": "Stellt Fragen zu Verwaltungsprozessen und erhält detaillierte Antworten",
      "status": "implemented",
      "endpoint": "/vpb/ask",
      "parameters": ["question", "analysis_depth", "include_suggestions"],
      "example": "Wie läuft ein Baugenehmigungsverfahren ab?"
    },
    {
      "mode": "EDIT",
      "display_name": "Prozess Editor",
      "description": "Bearbeitet und modifiziert bestehende VPB Prozesse", 
      "status": "development",
      "endpoint": "/vpb/process/edit",
      "parameters": ["process_id", "modifications", "validation"],
      "example": "Prozess XYZ um Rechtsgrundlage erweitern"
    }
    // ... weitere Modi
  ],
  "total_count": 8,
  "active_mode": "ASK",
  "timestamp": "2025-08-26T16:41:16.061181"
}
```

## 📋 VPB Modi im Detail

### 1. ASK Modus
**Endpoint:** `POST /vpb/ask`
**Status:** ✅ Implementiert
**Beschreibung:** Beantwortet Fragen zu Verwaltungsprozessen

**Request:**
```json
{
  "question": "Wie funktioniert ein Baugenehmigungsverfahren?",
  "analysis_depth": "standard",
  "include_suggestions": true,
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "answer": "Detaillierte Antwort zum Verwaltungsprozess...",
  "process_found": true,
  "details": {
    "analysis_depth": "standard",
    "matched_processes": ["Baugenehmigung", "Planungsverfahren"]
  },
  "sources": [
    {
      "type": "vpb_process", 
      "name": "Baugenehmigungsverfahren",
      "confidence": 0.92
    }
  ],
  "suggestions": ["Rechtsgrundlage § 35 BauGB beachten"],
  "processing_time_seconds": 1.234,
  "timestamp": "2025-08-26T16:41:16.061181"
}
```

### 2. EDIT Modus  
**Endpoint:** `POST /vpb/edit`
**Status:** 🔨 In Entwicklung
**Beschreibung:** Bearbeitet bestehende VPB Prozesse

### 3. AGENT Modus
**Endpoint:** `POST /vpb/agent`
**Status:** 📋 Geplant
**Beschreibung:** Intelligenter Agent für komplexe VPB Aufgaben

### 4. VPB Core System
**Endpoint:** `POST /vpb/core` 
**Status:** ✅ Verfügbar (wenn VPB installiert)
**Beschreibung:** Direkter Zugriff auf VPB Kernsystem

### 5. ANALYZE Modus
**Endpoint:** `POST /vpb/analyze`
**Status:** 🔨 In Entwicklung
**Beschreibung:** Analysiert Prozesse auf Compliance und Effizienz

### 6. TEMPLATE System
**Endpoint:** `POST /vpb/template`
**Status:** 🔨 In Entwicklung  
**Beschreibung:** Verwaltet VPB Prozess-Templates

### 7. EXPORT System
**Endpoint:** `POST /vpb/export`
**Status:** 📋 Geplant
**Beschreibung:** Exportiert Prozesse in verschiedene Formate

### 8. COMPLIANCE Check
**Endpoint:** `POST /vpb/compliance`
**Status:** 📋 Geplant
**Beschreibung:** Überprüft rechtliche Konformität

## 🛠️ Zentraler Prozess-Handler

**Endpoint:** `POST /vpb/process`

**Beschreibung:** Zentraler Endpoint für alle VPB Prozess-Operationen

**Request:**
```json
{
  "process_type": "create|edit|analyze|validate",
  "data": {
    "name": "Beispiel Prozess",
    "type": "application_process"
  },
  "mode": "standard",
  "session_id": "optional-session-id"  
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "process_id": "vpb_a1b2c3d4",
    "status": "created", 
    "elements": [],
    "connections": []
  },
  "process_id": "vpb_a1b2c3d4",
  "message": "Prozess erfolgreich erstellt in Modus: standard",
  "timestamp": "2025-08-26T16:41:16.061181"
}
```

## 📚 Verfügbare Process Types

- `create` - Neuen Prozess erstellen
- `edit` - Bestehenden Prozess bearbeiten  
- `analyze` - Prozess analysieren
- `validate` - Prozess validieren

## 🔧 Integration mit VPB Process Designer

Die API ist vollständig mit dem VPB Process Designer integriert:

- **Toolbar Integration:** CRUD-Operationen über Toolbar-Buttons
- **Kontextmenü:** Rechtsklick-Menü für alle Element-Operationen
- **Tastatur-Shortcuts:** Vollständige Keyboard-Navigation
- **LLM-Integration:** Template-Generierung und -Bearbeitung über Ollama

## 📖 Dokumentation

- **Swagger UI:** http://localhost:5000/docs
- **ReDoc:** http://localhost:5000/redoc
- **OpenAPI Spec:** http://localhost:5000/openapi.json

## 🚀 Verwendung

```bash
# Server starten
python api_endpoint.py

# Modi abrufen
curl http://localhost:5000/vpb/modes

# Prozess-Frage stellen
curl -X POST http://localhost:5000/vpb/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Wie funktioniert eine Baugenehmigung?"}'
```

## Status-Legende

- ✅ **Implemented:** Vollständig implementiert und getestet
- 🔨 **Development:** In aktiver Entwicklung
- 📋 **Planning:** Geplant für zukünftige Versionen
- ❌ **Unavailable:** Nicht verfügbar (Abhängigkeiten fehlen)
