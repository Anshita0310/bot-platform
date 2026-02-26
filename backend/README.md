# B2B Bot Builder — Backend (FastAPI + MongoDB)

This is a local-first backend that powers your React + React Flow dialog builder. It stores flows in MongoDB, validates structure, allows import/export as JSON, and provides a simple simulator.

## Tech
- FastAPI (async)
- Motor (MongoDB async driver)
- Pydantic v2
- orjson (fast JSON)

## Endpoints
- `GET /api/flows?orgId=ORG&projectId=PROJ` — List flows
- `POST /api/flows` — Create flow (validates)
- `GET /api/flows/{id}` — Get one
- `PUT /api/flows/{id}` — Update (validates; bumps `version` when `isDraft` becomes `false`)
- `DELETE /api/flows/{id}` — Delete
- `GET /api/flows/{id}/export` — Download JSON
- `POST /api/flows/import` — Import JSON
- `POST /api/flows/{id}/simulate` — Run lightweight preview
- `GET /health` — Health check

## Flow JSON shape
Nodes + edges are React Flow-like. Required node types for v1: `Start`, `BotMessage`, `UserInput`, `Condition`, `End`.

Example:
```json
{
  "orgId": "acme_corp",
  "projectId": "support-bot",
  "name": "Order Support",
  "nodes": [
    {"id":"start_1","type":"Start","data":{},"position":{"x":0,"y":0}},
    {"id":"bot_1","type":"BotMessage","data":{"text":"Hi!"},"position":{"x":200,"y":0}},
    {"id":"end_1","type":"End","data":{},"position":{"x":400,"y":0}}
  ],
  "edges": [
    {"id":"e1","source":"start_1","target":"bot_1"},
    {"id":"e2","source":"bot_1","target":"end_1"}
  ],
  "isDraft": true
}
```

## Local setup (no Docker)

1. **MongoDB**: Run a local MongoDB (or use Atlas) and set `MONGODB_URI`.
2. **Install**
   ```bash
   cd backend
   python -m venv .venv
   # Windows: .venv\Scriptsctivate
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env if needed
   ```
3. **Run**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## Frontend quick calls
```ts
// Load
await fetch('http://localhost:8000/api/flows/<<id>>')

// Create
await fetch('http://localhost:8000/api/flows', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ orgId:'acme', projectId:'demo', name:'Demo', nodes, edges, isDraft:true }) })

// Update + publish
await fetch('http://localhost:8000/api/flows/<<id>>', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nodes, edges, isDraft:false }) })

// Export
await fetch('http://localhost:8000/api/flows/<<id>>/export')

// Import
await fetch('http://localhost:8000/api/flows/import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(flowJson) })

// Simulate
await fetch('http://localhost:8000/api/flows/<<id>>/simulate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_issue: 'order problem' }) })
```

## Notes
- The server validates: single `Start`, at least one `End`, no cycles, all edges valid, all `End` reachable.
- Extendable palette: add `SetVariable`, `APIRequest`, `LLMCall`, `Delay`, etc. to `simulator.py` and your frontend node config UI.
- Multi-tenant: uniqueness index on `(orgId, projectId, name)`.
