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

Each person owns one reviewable slice. Build against the shared API and data contracts above, keep the local demo working, and include a short handoff note with changed files, run steps, decisions, and known gaps.

### Savage — UI and experiment dashboard

- **Build:** polish the experiment list/detail and create form, run status, and a simple hyperparameter visualization. Use mock data if an API field is not ready; coordinate contract changes before depending on them.
- **Deliver:** UI changes, screenshots or a short walkthrough, and the API fields/endpoints the UI needs.
- **Done when:** a user can create and inspect an experiment in the local demo, with validation plus empty, loading, and error states.
- **Start in:** `frontend/src/App.tsx` and `frontend/src/styles.css`.
- **Keep in scope:** prioritize the form, dashboard, and chart; leave drag-and-drop pipeline editing for later.

### TAh — Gemini-assisted ML helper

- **Build:** one focused suggestion feature, such as generating a starter training/evaluation snippet or explaining an ML error. Put Gemini behind a provider interface and retain a deterministic mock mode so the demo works without an API key.
- **Deliver:** provider/service, prompt template, at least two example scenarios, error and missing-key behavior, and setup notes.
- **Done when:** the frontend/API can request a useful suggestion for two ML scenarios, and the UI labels generated content as a suggestion that needs review.
- **Keep in scope:** never put the Gemini key in frontend code; do not build a general autonomous coding agent.

### Tobenna — Neo4j experiment and version graph

- **Build:** Neo4j schema and queries for experiments, runs, model versions, and parent/change relationships. Provide seed data and connect it behind the existing `GET /api/graph` response contract.
- **Deliver:** schema note, seed script, graph repository/queries, and local setup or mock fallback.
- **Done when:** the dashboard can trace a run to its experiment and show at least two related model versions.
- **Keep in scope:** make version history transparent; defer automatic concurrent merge/conflict resolution.

### Pauline — Azure deployment and CI

- **Build:** a reproducible deployment path appropriate to the available class account, plus CI configuration if time and repo access allow. Preserve local development as a working path.
- **Deliver:** deployment files or a step-by-step walkthrough, environment-variable/secrets list, assumptions about Azure access and cost, and CI configuration if feasible.
- **Done when:** another teammate can reproduce the local run and follow the documented Azure path; secrets are not committed.
- **Keep in scope:** do not create paid cloud resources without the team's budget/access plan; clearly mark any Azure ML or AKS part that is documented or mocked rather than deployed.

### Shared integration expectations

- Agree on changes to `frontend/src/contracts.ts` and `backend/app/schemas.py` before relying on new fields.
- Keep the app runnable without Gemini, Neo4j, or Azure credentials; use mock/local providers as needed.
- At each check-in, report what is working, what is next, blockers, and any contract change needed.
- If a task is blocked or unfinished, hand over its current files and notes so another teammate can continue without restarting.

## Current limitations

This is a course-project prototype. It has no authentication, multi-user collaboration, cloud deployment, production data controls, or measured performance claims. Generated code suggestions must be reviewed by a person.
