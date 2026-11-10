# DevFlowX architecture and integration contract

## Product boundary

The prototype has one end-to-end user journey: create an experiment, record a run, attach a model version, and inspect the recorded lineage. Local development uses SQLite and seeded example records. Integrations can be swapped in behind the API without changing the browser contract.

```text
React dashboard
      │ JSON REST (frontend/src/contracts.ts)
      ▼
FastAPI routes (backend/app/main.py)
      │
      ├── local SQLite repository (backend/app/store.py)
      ├── AI suggestion provider (teammate integration)
      └── graph repository (local projection now, Neo4j adapter later)
```

## Entity relationships

- An `Experiment` has zero or more `Run` records.
- A `Run` can produce zero or one `ModelVersion` in this prototype.
- A `ModelVersion` can have a `parent_model_id`, which records the prior version of the same named model.
- A `WorkflowGraph` is a projection of those records: `HAS_RUN`, `PRODUCED`, and `PARENT_OF` edges.

IDs are opaque strings. Timestamps are ISO 8601 UTC values. Metric values are numeric; parameter values may be arbitrary JSON. New API fields should be additive where possible. Coordinate breaking contract changes in the team before merging.

## API ownership contracts

- UI contribution reads/writes through `frontend/src/api.ts`; it must not reach into the database.
- AI contribution should add a provider module with `mock` and Gemini modes and a narrow endpoint such as `POST /api/assistant/suggest`. Do not add provider secrets to the browser bundle.
- Neo4j contribution should preserve the `WorkflowGraph` schema returned by `GET /api/graph`; seed/sample data must still work locally.
- Azure contribution should document deployment configuration separately from the local startup path and keep secrets out of version control.

## Deliberate prototype limits

There is no authentication, multi-user access control, live training execution, automatic conflict resolution, cloud persistence, or performance baseline. The dashboard's “Log run” action records a demo run; it does not train a model. The seeded metrics are illustrative data, not benchmark evidence.
