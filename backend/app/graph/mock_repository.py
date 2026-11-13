"""SQLite-backed graph provider used when Neo4j is not enabled or unavailable."""

from __future__ import annotations

from typing import Any


class MockGraphRepository:
    """Expose the current SQLite records using the WorkflowGraph response shape.

    This is intentionally a real projection of the SQLite store, not fixed mock
    records. It keeps DevFlowX usable when no Neo4j server or credentials exist.
    """

    def __init__(self, store_module: Any) -> None:
        self.store = store_module

    def sync_from_store(self, _store_module: Any | None = None) -> None:
        """No-op: get_graph reads the current SQLite contents directly."""

    def get_graph(self) -> dict[str, list[dict[str, str]]]:
        nodes: list[dict[str, str]] = []
        edges: list[dict[str, str]] = []

        with self.store.connect() as db:
            experiments = db.execute(
                "SELECT * FROM experiments ORDER BY created_at, id"
            ).fetchall()

            for experiment in experiments:
                nodes.append(
                    {
                        "id": experiment["id"],
                        "kind": "experiment",
                        "label": experiment["name"],
                        "detail": experiment["task"],
                    }
                )

                runs = db.execute(
                    "SELECT * FROM runs WHERE experiment_id=? ORDER BY created_at, id",
                    (experiment["id"],),
                ).fetchall()
                for run in runs:
                    nodes.append(
                        {
                            "id": run["id"],
                            "kind": "run",
                            "label": f"Run {run['id'][-4:]}",
                            "detail": run["status"],
                        }
                    )
                    edges.append(
                        {
                            "source": experiment["id"],
                            "target": run["id"],
                            "relation": "HAS_RUN",
                        }
                    )

                models = db.execute(
                    "SELECT * FROM models WHERE experiment_id=? ORDER BY name, version, id",
                    (experiment["id"],),
                ).fetchall()
                for model in models:
                    metrics = self.store.decode(model["metrics_json"])
                    f1 = metrics.get("f1", "—")
                    nodes.append(
                        {
                            "id": model["id"],
                            "kind": "model",
                            "label": f"{model['name']} v{model['version']}",
                            "detail": f"F1 {f1}",
                        }
                    )
                    edges.append(
                        {
                            "source": model["run_id"],
                            "target": model["id"],
                            "relation": "PRODUCED",
                        }
                    )
                    if model["parent_model_id"]:
                        edges.append(
                            {
                                "source": model["parent_model_id"],
                                "target": model["id"],
                                "relation": "PARENT_OF",
                            }
                        )

        return {"nodes": nodes, "edges": edges}

    def close(self) -> None:
        """There is no external connection to close for the SQLite provider."""
