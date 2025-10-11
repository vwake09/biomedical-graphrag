from typing import Any

from neo4j import GraphDatabase

from biomedical_graphrag.config import settings


class Neo4jClient:
    """
    Neo4j client for creating and deleting graphs.
    """

    def __init__(self) -> None:
        """
        Initialize the Neo4j client with connection parameters.
        Args:
            uri (str): The URI of the Neo4j database.
            user (str): The username for authentication.
            password (SecretStr): The password for authentication.
        Returns:
            None
        """
        self.password = settings.neo4j.password
        self.uri = settings.neo4j.uri
        self.user = settings.neo4j.username

        self.driver = GraphDatabase.driver(
            self.uri, auth=(self.user, self.password.get_secret_value())
        )

    def close(self) -> None:
        """
        Close the Neo4j driver.

        Args:
            None
        Returns:
            None
        """
        self.driver.close()

    def create_graph(self, cypher_query: str, parameters: dict[str, Any] | None = None) -> None:
        """
        Execute a Cypher query to create nodes and relationships in the graph.
        Args:
            cypher_query (str): The Cypher query to execute.
            parameters (dict, optional): Parameters for the query.
        Returns:
            None
        """
        self.driver.execute_query(cypher_query, parameters or {})

    def delete_graph(self) -> None:
        """
        Delete all nodes and relationships in the graph.
        Args:
            None
        Returns:
            None
        """
        self.driver.execute_query("MATCH (n) DETACH DELETE n")
