# DevFlowX

DevFlowX is a prototype workspace for tracking ML experiments and model versions, with an AI helper and graph view designed to plug into the same workflow.

## Current demo slice

- Create and inspect experiments.
- Record runs and model versions through a typed REST API.
- View experiment/run/model relationships in a dashboard.
- Start with a seeded local SQLite store so the demo runs without Azure, Gemini, or Neo4j credentials.

The cloud, LLM, and graph integrations are provider boundaries for team contributions; this prototype does not claim those integrations are deployed.

## Run locally

Requirements: Python 3.10+ and Node.js 20+.

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```sh
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal. The API is at `http://localhost:8000`; its interactive docs are at `/docs`.

## Shared contracts

The TypeScript interfaces in `frontend/src/contracts.ts` mirror the API schemas in `backend/app/schemas.py`. Keep IDs and field names aligned when adding UI or service integrations.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/experiments` | List experiments |
| POST | `/api/experiments` | Create an experiment |
| GET | `/api/experiments/{id}` | Get experiment with runs and model versions |
| POST | `/api/experiments/{id}/runs` | Record a run and optional model version |
| GET | `/api/graph` | Get graph-shaped workflow data for visualization |
| GET | `/api/health` | Health check |

## Service boundaries

- SQLite is the local demo repository. Keep API behavior independent of the storage choice.
- The AI helper should expose a provider interface and a deterministic mock mode.
- The graph endpoint provides the UI contract; a Neo4j repository can replace the current local graph projection.
- Azure deployment should remain optional for local development. Never commit credentials.

## Team ownership handoff

- UI/dashboard: `frontend/src/App.tsx` and `frontend/src/styles.css`
- Gemini helper: add an isolated service/provider and its API route; keep mock mode available.
- Neo4j: implement the graph repository behind the existing `/api/graph` response contract.
- Azure/CI: add deployment configuration and document required secrets; preserve local run instructions.

## Current limitations

This is a course-project prototype. It has no authentication, multi-user collaboration, cloud deployment, production data controls, or measured performance claims. Generated code suggestions must be reviewed by a person.
