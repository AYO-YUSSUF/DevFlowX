import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


DATA_PATH = Path(os.getenv("DEVFLOWX_DATA", "./data/devflowx.sqlite3"))


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATA_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def initialize() -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, task TEXT NOT NULL,
                dataset TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                parameters_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL REFERENCES experiments(id),
                status TEXT NOT NULL, created_at TEXT NOT NULL,
                parameters_json TEXT NOT NULL, metrics_json TEXT NOT NULL, notes TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS models (
                id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL REFERENCES experiments(id),
                run_id TEXT NOT NULL REFERENCES runs(id), name TEXT NOT NULL,
                version INTEGER NOT NULL, created_at TEXT NOT NULL,
                metrics_json TEXT NOT NULL, parent_model_id TEXT REFERENCES models(id)
            );
            """
        )
        if db.execute("SELECT COUNT(*) FROM experiments").fetchone()[0] == 0:
            seed_demo(db)


def seed_demo(db: sqlite3.Connection) -> None:
    created = now()
    experiment_id = "exp-demo-churn"
    db.execute(
        "INSERT INTO experiments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (experiment_id, "Customer churn baseline", "Binary classification", "telco-churn-v1.csv",
         "Baseline logistic regression with a small parameter sweep.", "active", created, created,
         json.dumps({"test_size": 0.2, "random_state": 42})),
    )
    first_run, second_run = "run-demo-001", "run-demo-002"
    db.executemany(
        "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (first_run, experiment_id, "succeeded", created,
             json.dumps({"C": 0.5, "max_iter": 200}), json.dumps({"accuracy": 0.81, "f1": 0.72}),
             "Initial baseline."),
            (second_run, experiment_id, "succeeded", created,
             json.dumps({"C": 1.0, "max_iter": 300}), json.dumps({"accuracy": 0.84, "f1": 0.76}),
             "Higher regularization setting improved validation F1 in this demo record."),
        ],
    )
    db.executemany(
        "INSERT INTO models VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("model-demo-v1", experiment_id, first_run, "churn-classifier", 1, created,
             json.dumps({"accuracy": 0.81, "f1": 0.72}), None),
            ("model-demo-v2", experiment_id, second_run, "churn-classifier", 2, created,
             json.dumps({"accuracy": 0.84, "f1": 0.76}), "model-demo-v1"),
        ],
    )


def as_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def create_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10]}"


def decode(value: str) -> dict:
    return json.loads(value)
