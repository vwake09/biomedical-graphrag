from biomedical_graphrag.infrastructure.neo4j_db.neo4j_client import Neo4jClient


def delete_graph() -> None:
    """
    Delete all nodes and relationships in the Neo4j graph database.

    Args:
        None
    Returns:
        None
    """

    client = Neo4jClient()

    client.delete_graph()
    client.close()


if __name__ == "__main__":
    delete_graph()
