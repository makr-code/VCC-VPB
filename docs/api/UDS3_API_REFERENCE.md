# UDS3 VPB API Reference

**Version:** 1.1.0  
**API Base URL:** `/api/uds3`  
**OpenAPI Docs:** `/api/docs`  
**ReDoc:** `/api/redoc`

---

## Overview

The UDS3 VPB API provides REST endpoints for managing VPB (Verwaltungsprozess-Beschreibungssprache) processes with polyglot persistence support (PostgreSQL, Neo4j, ChromaDB) and SAGA transaction pattern.

**Features:**
- Full CRUD operations for processes
- SAGA transaction management for distributed consistency
- Semantic search via ChromaDB embeddings
- Health monitoring for backend services
- Automatic OpenAPI/Swagger documentation

---

## Quick Reference

### Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API welcome |
| GET | `/api/uds3/vpb/processes` | List all processes |
| POST | `/api/uds3/vpb/processes` | Create process (SAGA) |
| GET | `/api/uds3/vpb/processes/{id}` | Get process |
| PUT | `/api/uds3/vpb/processes/{id}` | Update process (SAGA) |
| DELETE | `/api/uds3/vpb/processes/{id}` | Delete process (SAGA) |
| GET | `/api/uds3/vpb/search` | Semantic search |
| GET | `/api/uds3/vpb/health` | Health check |
| GET | `/api/uds3/saga/transactions` | List transactions |
| GET | `/api/uds3/saga/transactions/{id}` | Get transaction status |

---

## Detailed Endpoint Documentation

For complete endpoint documentation with examples, request/response schemas, and error handling, refer to the interactive OpenAPI documentation at:

- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

---

## Quick Start Examples

### 1. List Processes
```bash
curl "http://localhost:8000/api/uds3/vpb/processes?limit=10"
```

### 2. Create Process
```bash
curl -X POST "http://localhost:8000/api/uds3/vpb/processes" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "description": "Test Process", "status": "draft"}'
```

### 3. Search Processes
```bash
curl "http://localhost:8000/api/uds3/vpb/search?q=Baugenehmigung"
```

### 4. Health Check
```bash
curl "http://localhost:8000/api/uds3/vpb/health"
```

---

**For complete documentation, see:** http://localhost:8000/api/docs

**Last Updated:** 2025-11-17  
**Status:** ✅ Production Ready
