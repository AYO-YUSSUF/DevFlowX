"""Graph provider factory for DevFlowX."""

from __future__ import annotations

import logging
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from .mock_repository import MockGraphRepository

logger = logging.getLogger(__name__)


def create_graph_repository(store_module: Any) -> Any:
    """Create the configured graph provider."""

    provider = os.getenv("GRAPH_PROVIDER", "mock").strip().lower()

    # Use SQLite when mock mode is selected.
    if provider in {"mock", "sqlite", "local"}:
        logger.info("DevFlowX graph provider: SQLite local projection")
        return MockGraphRepository(store_module)

    if provider != "neo4j":
        raise ValueError(
            "GRAPH_PROVIDER must be one of: mock, sqlite, local, neo4j"
        )

    repository = None

    try:
        from .neo4j_repository import Neo4jGraphRepository

        repository = Neo4jGraphRepository.from_environment()

        repository.verify_connectivity()
        repository.create_constraints()
        repository.sync_from_store(store_module)

        logger.info("DevFlowX graph provider: Neo4j")

        return repository

    except Exception:
        logger.exception(
            "Neo4j graph provider could not be initialized; "
            "using the SQLite graph projection instead."
        )

        if repository is not None:
            try:
                repository.close()
            except Exception:
                logger.exception("Could not close failed Neo4j driver")

        return MockGraphRepository(store_module)