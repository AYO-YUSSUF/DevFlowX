# DevFlowX Neo4j Graph Schema

## 1. Overview

DevFlowX uses Neo4j to represent relationships between machine learning experiments, training runs, and model versions.

The graph repository provides a graph-based view of experiment history while preserving the existing FastAPI `WorkflowGraph` response contract.

SQLite remains the local operational data store, while Neo4j provides graph storage and relationship queries.

## 2. Node Types

### Experiment

Represents an individual machine learning experiment.

Example:
- ID: `exp-demo-churn`
- Name: Customer churn baseline
- Task: Binary classification

### Run

Represents an individual execution or recorded training run associated with an experiment.

Example:
- ID: `run-demo-001`
- Status: succeeded
- Metrics: accuracy and F1 score

### ModelVersion

Represents a saved model version produced by a run.

Example:
- Name: `churn-classifier`
- Version: 1
- Metrics: accuracy and F1 score

## 3. Relationship Types

The graph uses three relationship types.

| Relationship | Direction | Description |
|---|---|---|
| HAS_RUN | Experiment → Run | An experiment contains a run. |
| PRODUCED | Run → ModelVersion | A run produces a model version. |
| PARENT_OF | ModelVersion → ModelVersion | A previous model version is related to its successor. |

## 4. Example Model Lineage

The demonstration dataset contains three versions of the `churn-classifier` model.

- Version 1 is the initial model.
- Version 2 is derived from version 1.
- Version 3 is derived from version 2.

The version relationships are:

`ModelVersion v1 → ModelVersion v2 → ModelVersion v3`

## 5. Seed Data

The seed script is located at:

`backend/scripts/seed_neo4j.py`

It initializes the SQLite store, transfers the existing experiment, run, and model-version records into Neo4j, and verifies the resulting graph.

Run it from the backend directory:

`python -m scripts.seed_neo4j`

## 6. API Integration

The graph is exposed through:

`GET /api/graph`

The response preserves the existing WorkflowGraph contract:

- `nodes`: experiment, run, and model records.
- `edges`: HAS_RUN, PRODUCED, and PARENT_OF relationships.

This allows the React frontend to visualize the graph without directly connecting to Neo4j.

## 7. Local Configuration

The graph provider is configured through backend environment variables.

- `GRAPH_PROVIDER`
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`

Neo4j configuration remains optional for local development. The SQLite graph fallback allows the prototype to run without Neo4j credentials.

Credentials must remain in the private `.env` file and must never be committed to GitHub.

## 8. Project Limitations

This implementation is a course-project prototype.

Automatic concurrent model-version merge and conflict resolution are outside its scope.