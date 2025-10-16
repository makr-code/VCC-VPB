# vpb_api_server.py – Flask-API (UDS3 Backend)

WICHTIG: Backend-Server für eine umfangreichere Umgebung. Der Minimal-Designer läuft ohne dieses Backend.

## Zweck
Stellt REST-Endpoints für Prozesse bereit (CRUD, Analyse, Validierung, Statistiken, Export). Nutzt SQLite-Persistenz und UDS3-spezifische Komponenten.

## Endpoints (Auszug)
- `GET /api/health` – Health Check
- `GET/POST/PUT/DELETE /api/vpb/processes` – CRUD
- `POST /api/vpb/processes/{id}/analyze` – LLM-gestützte Analyse (UDS3)
- `POST /api/vpb/processes/{id}/validate` – Schema/Compliance-Validierung
- `GET /api/vpb/statistics` – DB-Statistik
- `GET /api/vpb/processes/{id}/export?format=json|xml` – Export

## Abhängigkeiten
- Flask, flask_cors
- `vpb_sqlite_db`, `uds3_vpb_schema`, `uds3_api_backend`

## Hinweise
- Enthält „VERITAS Protected Module“-Header und Lizenz-Metadaten
- In diesem Repo voraussichtlich nur als Referenz – nicht aktiv benutzt vom Minimal-Designer