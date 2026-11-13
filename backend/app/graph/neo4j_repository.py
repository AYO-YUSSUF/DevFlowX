"""Neo4j implementation of the DevFlowX WorkflowGraph repository."""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

# Load backend/.env when the API is launched from the backend directory.
load_dotenv()


class Neo4jGraphRepository:
    """Persist the SQLite experiment lineage in Neo4j and return its graph view.

    SQLite remains the application source of truth. ``sync_from_store`` is an
    idempotent full projection suitable for this course-project prototype.
    """

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        database: str = "neo4j",
    ) -> None:
        if not uri or not username or not password:
            raise ValueError(
                "Set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD to use Neo4j."
            )
        self.database = database or "neo4j"
        self.driver: Driver = GraphDatabase.driver(uri, auth=(username, password))

    @classmethod
    def from_environment(cls) -> "Neo4jGraphRepository":
        return cls(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            username=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", ""),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
        )

    def verify_connectivity(self) -> None:
        self.driver.verify_connectivity()

    def create_constraints(self) -> None:
        statements = (
            """
            CREATE CONSTRAINT devflowx_experiment_id IF NOT EXISTS
            FOR (e:Experiment) REQUIRE e.id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT devflowx_run_id IF NOT EXISTS
            FOR (r:Run) REQUIRE r.id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT devflowx_model_version_id IF NOT EXISTS
            FOR (m:ModelVersion) REQUIRE m.id IS UNIQUE
            """,
        )
        with self.driver.session(database=self.database) as session:
            for statement in statements:
                session.run(statement).consume()

    @staticmethod
    def _json_text(value: Any) -> str:
        return json.dumps(value if value is not None else {}, sort_keys=True)

    def sync_from_store(self, store_module: Any) -> None:
        """Copy the current SQLite tables into Neo4j, preserving their IDs."""
        with store_module.connect() as db:
            experiment_rows = [dict(row) for row in db.execute(
                "SELECT * FROM experiments ORDER BY id"
            ).fetchall()]
            run_rows = [dict(row) for row in db.execute(
                "SELECT * FROM runs ORDER BY id"
            ).fetchall()]
            model_rows = [dict(row) for row in db.execute(
                "SELECT * FROM models ORDER BY id"
            ).fetchall()]

        experiments = [
            {
                "id": row["id"],
                "name": row["name"],
                "task": row["task"],
                "dataset": row["dataset"],
                "description": row["description"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "parameters_json": row["parameters_json"],
            }
            for row in experiment_rows
        ]
        runs = [
            {
                "id": row["id"],
                "experiment_id": row["experiment_id"],
                "status": row["status"],
                "created_at": row["created_at"],
                "parameters_json": row["parameters_json"],
                "metrics_json": row["metrics_json"],
                "notes": row["notes"],
            }
            for row in run_rows
        ]
        models = [
            {
                "id": row["id"],
                "experiment_id": row["experiment_id"],
                "run_id": row["run_id"],
                "name": row["name"],
                "version": row["version"],
                "created_at": row["created_at"],
                "metrics_json": row["metrics_json"],
                "parent_model_id": row["parent_model_id"],
            }
            for row in model_rows
        ]

        with self.driver.session(database=self.database) as session:
            session.execute_write(self._write_snapshot, experiments, runs, models)

    @staticmethod
    def _write_snapshot(
        tx: Any,
        experiments: list[dict[str, Any]],
        runs: list[dict[str, Any]],
        models: list[dict[str, Any]],
    ) -> None:
        # Upsert all nodes. JSON columns remain JSON strings in Neo4j because
        # Neo4j properties do not store arbitrary nested Python dictionaries.
        tx.run(
            """
            UNWIND $rows AS row
            MERGE (e:Experiment {id: row.id})
            SET e.name = row.name,
                e.task = row.task,
                e.dataset = row.dataset,
                e.description = row.description,
                e.status = row.status,
                e.created_at = row.created_at,
                e.updated_at = row.updated_at,
                e.parameters_json = row.parameters_json
            """,
            rows=experiments,
        ).consume()

        tx.run(
            """
            UNWIND $rows AS row
            MERGE (r:Run {id: row.id})
            SET r.experiment_id = row.experiment_id,
                r.status = row.status,
                r.created_at = row.created_at,
                r.parameters_json = row.parameters_json,
                r.metrics_json = row.metrics_json,
                r.notes = row.notes
            """,
            rows=runs,
        ).consume()

        tx.run(
            """
            UNWIND $rows AS row
            MERGE (m:ModelVersion {id: row.id})
            SET m.experiment_id = row.experiment_id,
                m.run_id = row.run_id,
                m.name = row.name,
                m.version = row.version,
                m.created_at = row.created_at,
                m.metrics_json = row.metrics_json,
                m.parent_model_id = row.parent_model_id
            """,
            rows=models,
        ).consume()

        # Remove records that were deleted from the SQLite source of truth.
        tx.run(
            "MATCH (e:Experiment) WHERE NOT e.id IN $ids DETACH DELETE e",
            ids=[row["id"] for row in experiments],
        ).consume()
        tx.run(
            "MATCH (r:Run) WHERE NOT r.id IN $ids DETACH DELETE r",
            ids=[row["id"] for row in runs],
        ).consume()
        tx.run(
            "MATCH (m:ModelVersion) WHERE NOT m.id IN $ids DETACH DELETE m",
            ids=[row["id"] for row in models],
        ).consume()

        # Rebuild this small set of relationship types so changed parent links
        # cannot leave stale lineage edges in the graph.
        tx.run("MATCH ()-[r:HAS_RUN]->() DELETE r").consume()
        tx.run("MATCH ()-[r:PRODUCED]->() DELETE r").consume()
        tx.run("MATCH ()-[r:PARENT_OF]->() DELETE r").consume()

        tx.run(
            """
            UNWIND $rows AS row
            MATCH (e:Experiment {id: row.experiment_id})
            MATCH (r:Run {id: row.id})
            MERGE (e)-[:HAS_RUN]->(r)
            """,
            rows=runs,
        ).consume()

        tx.run(
            """
            UNWIND $rows AS row
            MATCH (r:Run {id: row.run_id})
            MATCH (m:ModelVersion {id: row.id})
            MERGE (r)-[:PRODUCED]->(m)
            """,
            rows=models,
        ).consume()

        tx.run(
            """
            UNWIND $rows AS row
            WITH row WHERE row.parent_model_id IS NOT NULL
            MATCH (parent:ModelVersion {id: row.parent_model_id})
            MATCH (child:ModelVersion {id: row.id})
            MATCH (run:Run {id: row.run_id})
            MERGE (parent)-[relationship:PARENT_OF]->(child)
            SET relationship.change_summary = run.notes,
                relationship.created_at = row.created_at
            """,
            rows=models,
        ).consume()

    @staticmethod
    def _metrics_from_node(node: Any) -> dict[str, Any]:
        raw = node.get("metrics_json") or "{}"
        try:
            value = json.loads(raw)
            return value if isinstance(value, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}

    def get_graph(self) -> dict[str, list[dict[str, str]]]:
        nodes: list[dict[str, str]] = []
        edges: list[dict[str, str]] = []

        with self.driver.session(database=self.database) as session:
            for record in session.run(
                "MATCH (node:Experiment) RETURN node ORDER BY node.created_at, node.id"
            ):
                node = record["node"]
                nodes.append(
                    {
                        "id": node["id"],
                        "kind": "experiment",
                        "label": node.get("name", node["id"]),
                        "detail": node.get("task", ""),
                    }
                )

            for record in session.run(
                "MATCH (node:Run) RETURN node ORDER BY node.created_at, node.id"
            ):
                node = record["node"]
                nodes.append(
                    {
                        "id": node["id"],
                        "kind": "run",
                        "label": f"Run {node['id'][-4:]}",
                        "detail": node.get("status", ""),
                    }
                )

            for record in session.run(
                "MATCH (node:ModelVersion) RETURN node ORDER BY node.name, node.version, node.id"
            ):
                node = record["node"]
                metrics = self._metrics_from_node(node)
                f1 = metrics.get("f1", "—")
                nodes.append(
                    {
                        "id": node["id"],
                        "kind": "model",
                        "label": f"{node.get('name', 'Model')} v{node.get('version', '?')}",
                        "detail": f"F1 {f1}",
                    }
                )

            for record in session.run(
                """
                MATCH (source)-[relationship]->(target)
                WHERE type(relationship) IN ['HAS_RUN', 'PRODUCED', 'PARENT_OF']
                RETURN source.id AS source,
                       target.id AS target,
                       type(relationship) AS relation
                ORDER BY relation, source, target
                """
            ):
                edges.append(
                    {
                        "source": record["source"],
                        "target": record["target"],
                        "relation": record["relation"],
                    }
                )

        return {"nodes": nodes, "edges": edges}

    def close(self) -> None:
        self.driver.close()
