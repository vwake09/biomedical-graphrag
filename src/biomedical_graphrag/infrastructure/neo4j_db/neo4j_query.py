"""Neo4j graph querying with LangChain integration for natural language queries."""

from typing import Any

from langchain.prompts import PromptTemplate
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_openai import ChatOpenAI

from biomedical_graphrag.config import settings


class Neo4jGraphQuery:
    """Handles querying Neo4j graph using LangChain for natural language questions."""

    def __init__(
        self,
        temperature: float = 0,
        model: str = "gpt-4o-mini",
    ) -> None:
        """
        Initialize the graph query handler with LangChain.

        Args:
            uri: Neo4j database URI (defaults to settings)
            username: Neo4j username (defaults to settings)
            password: Neo4j password (defaults to settings)
            openai_api_key: OpenAI API key (defaults to settings)
            temperature: LLM temperature for queries (default: 0 for consistency)
            model: OpenAI model to use (default: gpt-4)
        """
        # Use settings as defaults
        self.uri = settings.neo4j.uri
        self.username = settings.neo4j.username
        self.password = settings.neo4j.password.get_secret_value()
        self.openai_api_key = settings.openai.api_key

        # Initialize Neo4j graph connection
        self.graph = Neo4jGraph(url=self.uri, username=self.username, password=self.password)

        # Initialize LLM
        self.llm = ChatOpenAI(temperature=temperature, model=model, api_key=self.openai_api_key)

        # Custom instructions for better Cypher generation
        cypher_template = """
            Task: Generate Cypher queries for a Neo4j biomedical research graph database.

            Schema: {schema}

            IMPORTANT RULES for generating Cypher:
            1. For text searches on properties like 'term', 'title', 'name',
            ALWAYS use CONTAINS instead of exact match (=)
            - CORRECT: WHERE m.term CONTAINS 'CRISPR'
            - WRONG: WHERE m.term = 'CRISPR gene editing'

            2. For searching MeSH terms about a topic, use:
            MATCH (p:Paper)-[:HAS_MESH_TERM]->(m:MeshTerm)
            WHERE m.term CONTAINS 'keyword'

            3. For exact ID lookups (pmid), use exact match (=)
            - CORRECT: WHERE p.pmid = '12345'

            4. Always order results by relevance (publication_date DESC for papers)

            5. Limit results to 10 unless specifically asked for more

            Question: {question}

            Generate only the Cypher query, nothing else.
            """

        cypher_prompt = PromptTemplate(
            template=cypher_template, input_variables=["schema", "question"]
        )

        # Initialize QA chain with custom prompt
        self.chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            verbose=True,
            allow_dangerous_requests=True,
            cypher_prompt=cypher_prompt,
        )

    def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Execute a raw Cypher query against the graph.

        Args:
            cypher: Cypher query string
            params: Optional parameters for the query

        Returns:
            List of result dictionaries
        """
        return self.graph.query(cypher, params or {})

    def ask(self, question: str) -> str:
        """
        Ask a natural language question about the graph.

        Uses LangChain's GraphCypherQAChain to convert natural language
        to Cypher and return an answer.

        Args:
            question: Natural language question

        Returns:
            Answer as a string

        Examples:
            >>> query_handler = Neo4jGraphQuery()
            >>> query_handler.ask("Who are the authors of papers about CRISPR?")
            'The authors include...'
        """
        result = self.chain.invoke({"query": question})
        return result.get("result", "No answer found")

    def get_schema(self) -> str:
        """
        Get the graph schema as a string.

        Returns:
            String representation of the graph schema
        """
        return self.graph.schema

    def refresh_schema(self) -> None:
        """Refresh the graph schema (useful after ingestion)."""
        self.graph.refresh_schema()

    def close(self) -> None:
        """Close the database connection."""
        # Neo4jGraph doesn't expose a close method, but connection is managed
        pass


class BiomedicalGraphQueries:
    """Pre-built Cypher queries for common biomedical graph operations."""

    @staticmethod
    def find_papers_by_author(author_name: str) -> str:
        """
        Get Cypher query to find papers by author name.

        Args:
            author_name: Author's full or partial name

        Returns:
            Cypher query string
        """
        return f"""
            MATCH (a:Author)-[:WROTE]->(p:Paper)
            WHERE a.name CONTAINS '{author_name}'
            RETURN p.pmid as pmid, p.title as title,
                   p.publication_date as date, a.name as author
            ORDER BY p.publication_date DESC
        """

    @staticmethod
    def find_papers_by_mesh_term(mesh_term: str) -> str:
        """
        Get Cypher query to find papers by MeSH term.

        Args:
            mesh_term: MeSH term text (full or partial)

        Returns:
            Cypher query string
        """
        return f"""
            MATCH (p:Paper)-[r:HAS_MESH_TERM]->(m:MeshTerm)
            WHERE m.term CONTAINS '{mesh_term}'
            RETURN p.pmid as pmid, p.title as title, m.term as mesh_term,
                   r.major_topic as is_major_topic
            ORDER BY r.major_topic DESC, p.publication_date DESC
        """

    @staticmethod
    def find_citation_network(pmid: str, depth: int = 1) -> str:
        """
        Get Cypher query to find citation network around a paper.

        Args:
            pmid: PubMed ID of the central paper
            depth: How many citation hops to traverse (default: 1)

        Returns:
            Cypher query string
        """
        return f"""
            MATCH path = (p:Paper {{pmid: '{pmid}'}})-[:CITES*1..{depth}]-(cited:Paper)
            RETURN p.pmid as source_pmid, p.title as source_title,
                   cited.pmid as related_pmid, cited.title as related_title,
                   length(path) as distance
            ORDER BY distance, related_title
        """

    @staticmethod
    def find_collaborating_institutions(min_collaborations: int = 2) -> str:
        """
        Get Cypher query to find institutions that collaborate frequently.

        Args:
            min_collaborations: Minimum number of collaborations to include

        Returns:
            Cypher query string
        """
        return f"""
            MATCH (i1:Institution)<-[:AFFILIATED_WITH]-(a1:Author)-[:WROTE]->(p:Paper)
                  <-[:WROTE]-(a2:Author)-[:AFFILIATED_WITH]->(i2:Institution)
            WHERE i1.name < i2.name
            WITH i1, i2, COUNT(DISTINCT p) as collaborations
            WHERE collaborations >= {min_collaborations}
            RETURN i1.name as institution1, i2.name as institution2, collaborations
            ORDER BY collaborations DESC
        """

    @staticmethod
    def find_prolific_authors(min_papers: int = 2) -> str:
        """
        Get Cypher query to find authors with many papers.

        Args:
            min_papers: Minimum number of papers to include author

        Returns:
            Cypher query string
        """
        return f"""
            MATCH (a:Author)-[:WROTE]->(p:Paper)
            WITH a, COUNT(p) as paper_count
            WHERE paper_count >= {min_papers}
            RETURN a.name as author, paper_count
            ORDER BY paper_count DESC
        """

    @staticmethod
    def find_related_papers_by_mesh(pmid: str) -> str:
        """
        Get Cypher query to find papers with similar MeSH terms.

        Args:
            pmid: PubMed ID of the reference paper

        Returns:
            Cypher query string
        """
        return f"""
            MATCH (p1:Paper {{pmid: '{pmid}'}})-[:HAS_MESH_TERM]->(m:MeshTerm)
                  <-[:HAS_MESH_TERM]-(p2:Paper)
            WHERE p1 <> p2
            WITH p2, COUNT(DISTINCT m) as shared_terms
            RETURN p2.pmid as pmid, p2.title as title, shared_terms
            ORDER BY shared_terms DESC
            LIMIT 10
        """
