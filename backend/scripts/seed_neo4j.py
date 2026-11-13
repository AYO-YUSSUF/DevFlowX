
"""Seed Neo4j from the existing DevFlowX SQLite database."""

from app import store
from app.graph.neo4j_repository import Neo4jGraphRepository


def main():
    print("Initializing DevFlowX SQLite database...")

    store.initialize()

    print("Connecting to Neo4j...")

    repository = Neo4jGraphRepository.from_environment()

    try:
        repository.verify_connectivity()
        print("Neo4j connection successful!")

        print("Creating database constraints...")
        repository.create_constraints()

        print("Transferring SQLite records into Neo4j...")
        repository.sync_from_store(store)

        graph = repository.get_graph()

        print("\nDevFlowX Neo4j seed completed!")
        print(f"Total nodes: {len(graph['nodes'])}")
        print(f"Total relationships: {len(graph['edges'])}")

    finally:
        repository.close()


if __name__ == "__main__":
    main()
