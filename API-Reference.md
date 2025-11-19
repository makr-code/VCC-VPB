# API Reference / API-Referenz

**Version:** 0.5.0  
**API Version:** 1.0.0  
**Target:** Developers / Entwickler  
**Base URL:** `http://localhost:8000`

---

## Overview / Übersicht

Die VPB REST API bietet vollständiges CRUD für Prozesse mit UDS3 Polyglot Persistence und SAGA Pattern für verteilte Transaktionen.

The VPB REST API provides complete CRUD for processes with UDS3 Polyglot Persistence and SAGA pattern for distributed transactions.

---

## Quick Start / Schnellstart

### Start API Server

```bash
# Development mode with auto-reload
uvicorn api.uds3_vpb_fastapi:app --reload

# Production mode
uvicorn api.uds3_vpb_fastapi:app --host 0.0.0.0 --port 8000
```

### API Documentation

**Interactive API Docs:**
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **OpenAPI Schema:** http://localhost:8000/api/openapi.json

---

## Authentication

**Status (v0.5.0):** No authentication required (development)

**Future (v1.0):**
- API Key authentication
- OAuth 2.0
- JWT tokens

---

## Endpoints Overview / Endpunkte-Übersicht

### VPB Process Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/uds3/vpb/processes` | List all processes |
| POST | `/api/uds3/vpb/processes` | Create new process |
| GET | `/api/uds3/vpb/processes/{id}` | Get process by ID |
| PUT | `/api/uds3/vpb/processes/{id}` | Update process |
| DELETE | `/api/uds3/vpb/processes/{id}` | Delete process |
| GET | `/api/uds3/vpb/search` | Semantic search |
| GET | `/api/uds3/vpb/health` | Health check |

### SAGA Transaction Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/uds3/saga/transactions` | List transactions |
| GET | `/api/uds3/saga/transactions/{id}` | Get transaction status |

### Root Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |

---

## Detailed Endpoint Documentation

### 1. List Processes

**Endpoint:** `GET /api/uds3/vpb/processes`

**Description:**  
Ruft Liste aller VPB Prozesse ab mit optionalen Filtern.  
Retrieves list of all VPB processes with optional filters.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain` | string | "vpb" | App domain filter |
| `status` | string | null | Status filter (draft, active, archived) |
| `authority` | string | null | Authority filter |
| `limit` | integer | 100 | Max results (1-1000) |
| `offset` | integer | 0 | Pagination offset |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/uds3/vpb/processes?limit=10&status=active"
```

**Response 200 OK:**
```json
{
  "success": true,
  "processes": [
    {
      "process_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Baugenehmigung Standard",
      "description": "Standardverfahren für Baugenehmigung",
      "authority": "Bauamt Stadt XYZ",
      "status": "active",
      "created_at": "2025-11-19T12:00:00Z",
      "updated_at": "2025-11-19T12:30:00Z"
    }
  ],
  "count": 1,
  "offset": 0,
  "limit": 10,
  "timestamp": "2025-11-19T14:00:00Z"
}
```

---

### 2. Get Process by ID

**Endpoint:** `GET /api/uds3/vpb/processes/{process_id}`

**Description:**  
Ruft einzelnen Prozess nach UUID ab.  
Retrieves single process by UUID.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `process_id` | string (UUID) | Yes | Process UUID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain` | string | "vpb" | App domain |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/uds3/vpb/processes/550e8400-e29b-41d4-a716-446655440000"
```

**Response 200 OK:**
```json
{
  "success": true,
  "process": {
    "process_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Baugenehmigung Standard",
    "description": "Standardverfahren für Baugenehmigung",
    "authority": "Bauamt Stadt XYZ",
    "legal_basis": ["BauGB §29-38", "LBO §58"],
    "status": "active",
    "process_data": {
      "elements": [
        {
          "id": "elem1",
          "type": "COUNTER",
          "name": "Antragszähler",
          "properties": {"max": 100}
        }
      ],
      "connections": []
    },
    "created_at": "2025-11-19T12:00:00Z",
    "updated_at": "2025-11-19T12:30:00Z"
  },
  "domain": "vpb",
  "timestamp": "2025-11-19T14:00:00Z"
}
```

**Response 404 Not Found:**
```json
{
  "success": false,
  "error": "Process not found",
  "message": "No process found with id: 550e8400-...",
  "timestamp": "2025-11-19T14:00:00Z"
}
```

---

### 3. Create Process

**Endpoint:** `POST /api/uds3/vpb/processes`

**Description:**  
Erstellt neuen Prozess mit SAGA Transaction über alle UDS3 Backends.  
Creates new process with SAGA transaction across all UDS3 backends.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain` | string | "vpb" | App domain |

**Request Body:**
```json
{
  "name": "Baugenehmigung Standard",
  "description": "Standardverfahren für Baugenehmigung",
  "authority": "Bauamt Stadt XYZ",
  "legal_basis": ["BauGB §29-38", "LBO §58"],
  "status": "draft",
  "process_data": {
    "elements": [
      {
        "id": "elem1",
        "type": "COUNTER",
        "name": "Antragszähler",
        "properties": {
          "initial_value": 0,
          "max": 100
        },
        "position": {"x": 100, "y": 100}
      },
      {
        "id": "elem2",
        "type": "CONDITION",
        "name": "Prüfung",
        "properties": {
          "condition": "count < 50"
        },
        "position": {"x": 300, "y": 100}
      }
    ],
    "connections": [
      {
        "id": "conn1",
        "source": "elem1",
        "target": "elem2",
        "type": "normal"
      }
    ]
  }
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/uds3/vpb/processes" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Baugenehmigung Standard",
    "description": "Standardverfahren für Baugenehmigung",
    "authority": "Bauamt Stadt XYZ",
    "legal_basis": ["BauGB §29-38"],
    "status": "draft",
    "process_data": {"elements": [], "connections": []}
  }'
```

**Response 201 Created:**
```json
{
  "success": true,
  "process_id": "550e8400-e29b-41d4-a716-446655440000",
  "domain": "vpb",
  "transaction": {
    "transaction_id": "tx-abc123",
    "state": "COMMITTED",
    "backends": ["postgresql", "neo4j", "chromadb"]
  },
  "message": "Process created successfully",
  "timestamp": "2025-11-19T14:00:00Z"
}
```

**Response 500 Error (with Rollback):**
```json
{
  "success": false,
  "error": "Failed to create process",
  "rollback": {
    "transaction_id": "tx-abc123",
    "state": "ROLLED_BACK",
    "compensated_backends": ["neo4j", "postgresql"]
  },
  "message": "ChromaDB connection failed",
  "timestamp": "2025-11-19T14:00:00Z"
}
```

---

### 4. Update Process

**Endpoint:** `PUT /api/uds3/vpb/processes/{process_id}`

**Description:**  
Aktualisiert existierenden Prozess mit SAGA Transaction.  
Updates existing process with SAGA transaction.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `process_id` | string (UUID) | Yes | Process UUID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain` | string | "vpb" | App domain |

**Request Body:**  
All fields optional (partial update):
```json
{
  "name": "Baugenehmigung Standard V2",
  "description": "Updated description",
  "status": "active",
  "process_data": {
    "elements": [...],
    "connections": [...]
  }
}
```

**Example Request:**
```bash
curl -X PUT "http://localhost:8000/api/uds3/vpb/processes/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

**Response 200 OK:**
```json
{
  "success": true,
  "process_id": "550e8400-e29b-41d4-a716-446655440000",
  "transaction": {
    "transaction_id": "tx-def456",
    "state": "COMMITTED"
  },
  "message": "Process updated successfully",
  "timestamp": "2025-11-19T14:00:00Z"
}
```

---

### 5. Delete Process

**Endpoint:** `DELETE /api/uds3/vpb/processes/{process_id}`

**Description:**  
Löscht Prozess (soft delete per default).  
Deletes process (soft delete by default).

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `process_id` | string (UUID) | Yes | Process UUID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain` | string | "vpb" | App domain |
| `soft_delete` | boolean | true | Soft delete (mark as deleted) vs hard delete |

**Example Request:**
```bash
# Soft delete (default)
curl -X DELETE "http://localhost:8000/api/uds3/vpb/processes/550e8400-e29b-41d4-a716-446655440000"

# Hard delete
curl -X DELETE "http://localhost:8000/api/uds3/vpb/processes/550e8400-e29b-41d4-a716-446655440000?soft_delete=false"
```

**Response 200 OK:**
```json
{
  "success": true,
  "process_id": "550e8400-e29b-41d4-a716-446655440000",
  "soft_delete": true,
  "transaction": {
    "transaction_id": "tx-ghi789",
    "state": "COMMITTED"
  },
  "message": "Process deleted successfully",
  "timestamp": "2025-11-19T14:00:00Z"
}
```

---

### 6. Semantic Search

**Endpoint:** `GET /api/uds3/vpb/search`

**Description:**  
Semantische Suche mit ChromaDB Vector Embeddings.  
Semantic search using ChromaDB vector embeddings.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | required | Search query (natural language) |
| `domain` | string | "vpb" | App domain |
| `top_k` | integer | 5 | Number of results (1-100) |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/uds3/vpb/search?q=Baugenehmigung&top_k=3"
```

**Response 200 OK:**
```json
{
  "success": true,
  "results": [
    {
      "process_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Baugenehmigung Standard",
      "description": "Standardverfahren...",
      "similarity_score": 0.89,
      "metadata": {
        "authority": "Bauamt Stadt XYZ",
        "status": "active"
      }
    },
    {
      "process_id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Bauvoranfrage",
      "description": "Voranfrage...",
      "similarity_score": 0.76,
      "metadata": {...}
    }
  ],
  "query": "Baugenehmigung",
  "domain": "vpb",
  "top_k": 3,
  "timestamp": "2025-11-19T14:00:00Z"
}
```

---

### 7. Health Check

**Endpoint:** `GET /api/uds3/vpb/health`

**Description:**  
Überprüft Status aller UDS3 Backends.  
Checks health status of all UDS3 backends.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/uds3/vpb/health"
```

**Response 200 OK:**
```json
{
  "status": "healthy",
  "backends": {
    "postgresql": true,
    "neo4j": true,
    "chromadb": true
  },
  "saga_enabled": true,
  "timestamp": "2025-11-19T14:00:00Z"
}
```

**Response 503 Service Unavailable:**
```json
{
  "status": "unhealthy",
  "backends": {
    "postgresql": true,
    "neo4j": false,
    "chromadb": true
  },
  "saga_enabled": true,
  "timestamp": "2025-11-19T14:00:00Z"
}
```

---

### 8. List SAGA Transactions

**Endpoint:** `GET /api/uds3/saga/transactions`

**Description:**  
Liste aller SAGA Transaktionen mit optionalem Filter.  
List all SAGA transactions with optional filter.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `state` | string | null | Filter by state (pending, in_progress, committed, rolled_back, failed) |
| `limit` | integer | 100 | Max results |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/uds3/saga/transactions?state=failed&limit=10"
```

**Response 200 OK:**
```json
{
  "success": true,
  "transactions": [
    {
      "transaction_id": "tx-abc123",
      "operation": "create_process",
      "state": "COMMITTED",
      "started_at": "2025-11-19T12:00:00Z",
      "completed_at": "2025-11-19T12:00:02Z",
      "steps": [
        {"backend": "postgresql", "status": "executed"},
        {"backend": "neo4j", "status": "executed"},
        {"backend": "chromadb", "status": "executed"}
      ]
    }
  ],
  "count": 1,
  "filter_state": "committed",
  "timestamp": "2025-11-19T14:00:00Z"
}
```

---

### 9. Get Transaction Status

**Endpoint:** `GET /api/uds3/saga/transactions/{transaction_id}`

**Description:**  
Ruft Status einer spezifischen SAGA Transaction ab.  
Retrieves status of a specific SAGA transaction.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `transaction_id` | string | Yes | Transaction ID |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/uds3/saga/transactions/tx-abc123"
```

**Response 200 OK:**
```json
{
  "success": true,
  "transaction": {
    "transaction_id": "tx-abc123",
    "operation": "create_process",
    "state": "COMMITTED",
    "process_id": "550e8400-e29b-41d4-a716-446655440000",
    "started_at": "2025-11-19T12:00:00Z",
    "completed_at": "2025-11-19T12:00:02Z",
    "duration_ms": 2000,
    "steps": [
      {
        "backend": "postgresql",
        "status": "executed",
        "timestamp": "2025-11-19T12:00:00Z"
      },
      {
        "backend": "neo4j",
        "status": "executed",
        "timestamp": "2025-11-19T12:00:01Z"
      },
      {
        "backend": "chromadb",
        "status": "executed",
        "timestamp": "2025-11-19T12:00:02Z"
      }
    ]
  },
  "timestamp": "2025-11-19T14:00:00Z"
}
```

**Response 404 Not Found:**
```json
{
  "success": false,
  "error": "Transaction not found",
  "message": "No transaction found with id: tx-abc123",
  "timestamp": "2025-11-19T14:00:00Z"
}
```

---

### 10. Root Endpoint

**Endpoint:** `GET /`

**Description:**  
API Information und Verfügbare Endpunkte.  
API information and available endpoints.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/"
```

**Response 200 OK:**
```json
{
  "message": "UDS3 VPB API",
  "version": "1.0.0",
  "description": "REST API für VPB Process Designer mit UDS3 Polyglot Persistence",
  "endpoints": {
    "docs": "/api/docs",
    "redoc": "/api/redoc",
    "openapi": "/api/openapi.json",
    "health": "/api/uds3/vpb/health"
  },
  "backends": ["PostgreSQL", "Neo4j", "ChromaDB"],
  "features": ["CRUD Operations", "SAGA Transactions", "Semantic Search"]
}
```

---

## Error Handling / Fehlerbehandlung

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET/PUT/DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Invalid input data |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error (SAGA rollback triggered) |
| 503 | Service Unavailable | Backend unavailable |

### Error Response Format

**Standard Error:**
```json
{
  "success": false,
  "error": "Error type",
  "message": "Detailed error message",
  "timestamp": "2025-11-19T14:00:00Z"
}
```

**Error with SAGA Rollback:**
```json
{
  "success": false,
  "error": "Transaction failed",
  "rollback": {
    "transaction_id": "tx-abc123",
    "state": "ROLLED_BACK",
    "compensated_backends": ["neo4j", "postgresql"],
    "failed_backend": "chromadb"
  },
  "message": "ChromaDB connection timeout",
  "timestamp": "2025-11-19T14:00:00Z"
}
```

---

## Rate Limiting

**Status (v0.5.0):** No rate limiting

**Future:**
- 100 requests / minute per IP
- 1000 requests / hour per API key

---

## Versioning / Versionierung

**Current Version:** 1.0.0

**Future Versions:**
- API versioning via URL: `/api/v2/...`
- Backward compatibility guaranteed
- Deprecation warnings

---

## CORS Configuration

**Development:**
```python
allow_origins=["*"]  # All origins allowed
```

**Production (Recommended):**
```python
allow_origins=[
    "https://vpb.example.com",
    "https://covina.example.com"
]
```

---

## Examples / Beispiele

### Complete Workflow

**1. Create Process:**
```bash
curl -X POST "http://localhost:8000/api/uds3/vpb/processes" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Process", "status": "draft", "process_data": {}}'
# Response: {"process_id": "550e8400-..."}
```

**2. Update Process:**
```bash
curl -X PUT "http://localhost:8000/api/uds3/vpb/processes/550e8400-..." \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

**3. Search:**
```bash
curl -X GET "http://localhost:8000/api/uds3/vpb/search?q=Test&top_k=5"
```

**4. Get Process:**
```bash
curl -X GET "http://localhost:8000/api/uds3/vpb/processes/550e8400-..."
```

**5. Delete Process:**
```bash
curl -X DELETE "http://localhost:8000/api/uds3/vpb/processes/550e8400-..."
```

---

## Client Libraries / Client-Bibliotheken

### Python

```python
import requests

class VPBClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def create_process(self, process_data):
        response = requests.post(
            f"{self.base_url}/api/uds3/vpb/processes",
            json=process_data
        )
        return response.json()
    
    def get_process(self, process_id):
        response = requests.get(
            f"{self.base_url}/api/uds3/vpb/processes/{process_id}"
        )
        return response.json()
    
    def search(self, query, top_k=5):
        response = requests.get(
            f"{self.base_url}/api/uds3/vpb/search",
            params={"q": query, "top_k": top_k}
        )
        return response.json()

# Usage
client = VPBClient()
result = client.create_process({
    "name": "My Process",
    "status": "draft",
    "process_data": {}
})
print(f"Created: {result['process_id']}")
```

### JavaScript

```javascript
class VPBClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async createProcess(processData) {
        const response = await fetch(`${this.baseUrl}/api/uds3/vpb/processes`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(processData)
        });
        return await response.json();
    }
    
    async getProcess(processId) {
        const response = await fetch(`${this.baseUrl}/api/uds3/vpb/processes/${processId}`);
        return await response.json();
    }
    
    async search(query, topK = 5) {
        const response = await fetch(
            `${this.baseUrl}/api/uds3/vpb/search?q=${query}&top_k=${topK}`
        );
        return await response.json();
    }
}

// Usage
const client = new VPBClient();
const result = await client.createProcess({
    name: 'My Process',
    status: 'draft',
    process_data: {}
});
console.log(`Created: ${result.process_id}`);
```

---

## Related Documentation

- **[[UDS3-Backend]]** - Backend architecture and SAGA pattern
- **[[Architecture]]** - Overall system architecture
- **[[Development-Guide]]** - Setup development environment
- **[[System-Integration]]** - Integration with Covina, Veritas, etc.

---

## External Resources

- **OpenAPI Spec:** http://localhost:8000/api/openapi.json
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **FastAPI Documentation:** https://fastapi.tiangolo.com/

---

[[Home]] | [[Architecture]] | [[UDS3-Backend]]
