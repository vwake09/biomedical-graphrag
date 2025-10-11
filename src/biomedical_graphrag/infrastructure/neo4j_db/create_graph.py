"""Script to create and populate Neo4j graph from biomedical papers dataset."""

import json
from pathlib import Path

from biomedical_graphrag.domain.dataset import Dataset
from biomedical_graphrag.infrastructure.neo4j_db.neo4j_client import Neo4jClient
from biomedical_graphrag.infrastructure.neo4j_db.neo4j_graph_schema import Neo4jGraphIngestion


def load_dataset(file_path: str | Path) -> Dataset:
    """
    Load dataset from JSON file.

    Args:
        file_path: Path to the JSON dataset file

    Returns:
        Dataset object with papers and citation network
    """
    with open(file_path) as f:
        data = json.load(f)

    return Dataset(**data)


def create_graph(dataset_path: str | Path | None = None) -> None:
    """
    Create a new graph in the Neo4j graph database from biomedical papers dataset.

    Args:
        dataset_path: Optional path to dataset JSON file.
                     Defaults to data/pubmed_dataset.json in project root.

    Returns:
        None
    """
    # Use default path if none provided
    if dataset_path is None:
        project_root = Path(__file__).parents[4]
        dataset_path = project_root / "data" / "pubmed_dataset.json"

    # Load dataset
    print(f"Loading dataset from {dataset_path}...")
    dataset = load_dataset(dataset_path)
    print(f"Loaded {len(dataset.papers)} papers with {len(dataset.citation_network)} citations")

    # Initialize Neo4j client
    client = Neo4jClient()

    try:
        # Initialize ingestion handler
        ingestion = Neo4jGraphIngestion(client)

        # Ingest complete dataset
        ingestion.ingest_dataset(dataset)

        print("\n✅ Graph with papers, authors, affiliations, journals, and MeSH terms created!")
        print(f"   - {len(dataset.papers)} papers")
        print(f"   - {dataset.metadata.total_authors} authors")
        print(f"   - {dataset.metadata.total_mesh_terms} MeSH terms")
        print("   - Citation network relationships created")

    finally:
        client.close()


if __name__ == "__main__":
    create_graph()
