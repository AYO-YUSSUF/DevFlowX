import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import store
from .schemas import (
    Experiment, ExperimentCreate, GraphEdge, GraphNode, ModelVersion, Run,
    RunCreate, WorkflowGraph,
)


def model_from_row(row) -> ModelVersion:
    return ModelVersion(
        id=row["id"], experiment_id=row["experiment_id"], run_id=row["run_id"],
        name=row["name"], version=row["version"], created_at=row["created_at"],
        metrics=store.decode(row["metrics_json"]), parent_model_id=row["parent_model_id"],
    )


def run_from_row(row, model=None) -> Run:
    return Run(
        id=row["id"], experiment_id=row["experiment_id"], status=row["status"],
        created_at=row["created_at"], parameters=store.decode(row["parameters_json"]),
        metrics=store.decode(row["metrics_json"]), notes=row["notes"], model_version=model,
    )


def experiment_from_db(db, row) -> Experiment:
    models = [model_from_row(item) for item in db.execute(
        "SELECT * FROM models WHERE experiment_id=? ORDER BY version", (row["id"],)
    )]
    by_run = {model.run_id: model for model in models}
    runs = [run_from_row(item, by_run.get(item["id"])) for item in db.execute(
        "SELECT * FROM runs WHERE experiment_id=? ORDER BY created_at DESC", (row["id"],)
    )]
    return Experiment(
        id=row["id"], name=row["name"], task=row["task"], dataset=row["dataset"],
        description=row["description"], status=row["status"], created_at=row["created_at"],
        updated_at=row["updated_at"], parameters=store.decode(row["parameters_json"]),
        runs=runs, model_versions=models,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.initialize()
    yield


app = FastAPI(title="DevFlowX API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "devflowx-api"}


@app.get("/api/experiments", response_model=list[Experiment])
def list_experiments():
    with store.connect() as db:
        return [experiment_from_db(db, row) for row in db.execute(
            "SELECT * FROM experiments ORDER BY updated_at DESC"
        )]


@app.post("/api/experiments", response_model=Experiment, status_code=201)
def create_experiment(payload: ExperimentCreate):
    created = store.now()
    experiment_id = store.create_id("exp")
    with store.connect() as db:
        db.execute(
            "INSERT INTO experiments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (experiment_id, payload.name, payload.task, payload.dataset, payload.description,
             "active", created, created, json.dumps(payload.parameters)),
        )
        row = db.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
        return experiment_from_db(db, row)


@app.get("/api/experiments/{experiment_id}", response_model=Experiment)
def get_experiment(experiment_id: str):
    with store.connect() as db:
        row = db.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return experiment_from_db(db, row)


@app.post("/api/experiments/{experiment_id}/runs", response_model=Run, status_code=201)
def create_run(experiment_id: str, payload: RunCreate):
    created, run_id = store.now(), store.create_id("run")
    with store.connect() as db:
        experiment = db.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
        if experiment is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        db.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, experiment_id, payload.status, created, json.dumps(payload.parameters),
             json.dumps(payload.metrics), payload.notes),
        )
        model = None
        if payload.model_name:
            version = db.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM models WHERE experiment_id=? AND name=?",
                (experiment_id, payload.model_name),
            ).fetchone()[0]
            parent = db.execute(
                "SELECT id FROM models WHERE experiment_id=? AND name=? ORDER BY version DESC LIMIT 1",
                (experiment_id, payload.model_name),
            ).fetchone()
            model_id = store.create_id("model")
            db.execute(
                "INSERT INTO models VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (model_id, experiment_id, run_id, payload.model_name, version, created,
                 json.dumps(payload.metrics), parent[0] if parent else None),
            )
            model = model_from_row(db.execute("SELECT * FROM models WHERE id=?", (model_id,)).fetchone())
        db.execute("UPDATE experiments SET updated_at=? WHERE id=?", (created, experiment_id))
        row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        return run_from_row(row, model)


@app.get("/api/graph", response_model=WorkflowGraph)
def get_graph():
    nodes, edges = [], []
    with store.connect() as db:
        for exp in db.execute("SELECT * FROM experiments"):
            nodes.append(GraphNode(id=exp["id"], kind="experiment", label=exp["name"], detail=exp["task"]))
            for run in db.execute("SELECT * FROM runs WHERE experiment_id=?", (exp["id"],)):
                nodes.append(GraphNode(id=run["id"], kind="run", label=f"Run {run['id'][-4:]}", detail=run["status"]))
                edges.append(GraphEdge(source=exp["id"], target=run["id"], relation="HAS_RUN"))
            for model in db.execute("SELECT * FROM models WHERE experiment_id=?", (exp["id"],)):
                nodes.append(GraphNode(id=model["id"], kind="model", label=f"{model['name']} v{model['version']}", detail=f"F1 {store.decode(model['metrics_json']).get('f1', '—')}"))
                edges.append(GraphEdge(source=model["run_id"], target=model["id"], relation="PRODUCED"))
                if model["parent_model_id"]:
                    edges.append(GraphEdge(source=model["parent_model_id"], target=model["id"], relation="PARENT_OF"))
    return WorkflowGraph(nodes=nodes, edges=edges)
