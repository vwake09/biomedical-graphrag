"""Neo4j graph ingestion for biomedical papers dataset."""

from typing import Any

from biomedical_graphrag.domain.dataset import Dataset
from biomedical_graphrag.domain.paper import Paper
from biomedical_graphrag.infrastructure.neo4j_db.neo4j_client import Neo4jClient


class Neo4jGraphIngestion:
    """Handles ingestion of biomedical paper data into Neo4j graph database."""

    def __init__(self, client: Neo4jClient) -> None:
        """
        Initialize the graph ingestion handler.

        Args:
            client: Neo4jClient instance for database operations
        """
        self.client = client

    def create_constraints(self) -> None:
        """
        Create unique constraints for graph nodes to ensure data integrity.

        This creates constraints for:
        - Paper nodes (by PMID)
        - Author nodes (by name)
        - Institution nodes (by name)
        - MeshTerm nodes (by UI)
        - Qualifier nodes (by name)
        - Journal nodes (by name)
        """
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Paper) REQUIRE p.pmid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Institution) REQUIRE i.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:MeshTerm) REQUIRE m.ui IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (q:Qualifier) REQUIRE q.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (j:Journal) REQUIRE j.name IS UNIQUE",
        ]

        for constraint in constraints:
            self.client.create_graph(constraint)

    def ingest_paper(self, paper: Paper) -> None:
        """
        Ingest a single paper and all its related entities into the graph.

        Args:
            paper: Paper domain model containing all paper metadata
        """
        # Create paper node
        self._create_paper_node(paper)

        # Create journal relationship if available
        if paper.journal:
            self._create_journal_relationship(paper.pmid, paper.journal)

        # Create authors and their affiliations
        for author in paper.authors:
            self._create_author_relationship(paper.pmid, author.name)

            for affiliation in author.affiliations:
                self._create_affiliation_relationship(author.name, affiliation)

        # Create MeSH terms and qualifiers
        for mesh_term in paper.mesh_terms:
            self._create_mesh_term_relationship(
                paper.pmid, mesh_term.ui, mesh_term.term, mesh_term.major_topic
            )

            for qualifier in mesh_term.qualifiers:
                self._create_qualifier_relationship(mesh_term.ui, qualifier)

    def ingest_citations(self, citation_network: dict[str, Any]) -> None:
        """
        Ingest citation relationships between papers.

        Args:
            citation_network: Dictionary mapping PMIDs to CitationNetwork objects
        """
        for pmid, citation_info in citation_network.items():
            # Create references (this paper cites others)
            references = (
                citation_info.references
                if hasattr(citation_info, "references")
                else citation_info.get("references", [])
            )
            for reference_pmid in references:
                self._create_citation_relationship(pmid, reference_pmid)

            # Cited_by relationships are the inverse and will be created
            # when those papers reference this one

    def ingest_dataset(self, dataset: Dataset) -> None:
        """
        Ingest complete dataset including papers and citations.

        Args:
            dataset: Complete dataset with papers and citation network

        Raises:
            Exception: If ingestion fails for any reason
        """
        try:
            print("Creating constraints...")
            self.create_constraints()

            print(f"Ingesting {len(dataset.papers)} papers...")
            failed_papers = []

            for i, paper in enumerate(dataset.papers, 1):
                try:
                    self.ingest_paper(paper)
                    if i % 10 == 0:
                        print(f"  Processed {i}/{len(dataset.papers)} papers")
                except Exception as e:
                    print(f"  Warning: Failed to ingest paper {paper.pmid}: {e}")
                    failed_papers.append(paper.pmid)

            if failed_papers:
                print(f"\nWarning: {len(failed_papers)} papers failed to ingest")

            print("Ingesting citation network...")
            self.ingest_citations(dataset.citation_network)

            print("Graph ingestion complete!")

        except Exception as e:
            print(f"\nError: Graph ingestion failed: {e}")
            raise

    def _create_paper_node(self, paper: Paper) -> None:
        """Create or update a paper node with its metadata."""
        query = """
            MERGE (p:Paper {pmid: $pmid})
            SET p.title = $title,
                p.abstract = $abstract,
                p.publication_date = $publication_date,
                p.doi = $doi
        """
        params = {
            "pmid": paper.pmid,
            "title": paper.title,
            "abstract": paper.abstract,
            "publication_date": paper.publication_date,
            "doi": paper.doi,
        }
        self.client.create_graph(query, params)

    def _create_journal_relationship(self, pmid: str, journal: str) -> None:
        """Create journal node and relationship to paper."""
        query = """
            MERGE (j:Journal {name: $journal})
            MERGE (p:Paper {pmid: $pmid})
            MERGE (p)-[:PUBLISHED_IN]->(j)
        """
        self.client.create_graph(query, {"pmid": pmid, "journal": journal})

    def _create_author_relationship(self, pmid: str, author_name: str) -> None:
        """Create author node and WROTE relationship to paper."""
        query = """
            MERGE (a:Author {name: $name})
            MERGE (p:Paper {pmid: $pmid})
            MERGE (a)-[:WROTE]->(p)
        """
        self.client.create_graph(query, {"name": author_name, "pmid": pmid})

    def _create_affiliation_relationship(self, author_name: str, affiliation: str) -> None:
        """Create institution node and AFFILIATED_WITH relationship."""
        query = """
            MERGE (i:Institution {name: $affiliation})
            MERGE (a:Author {name: $name})
            MERGE (a)-[:AFFILIATED_WITH]->(i)
        """
        self.client.create_graph(query, {"name": author_name, "affiliation": affiliation})

    def _create_mesh_term_relationship(
        self, pmid: str, ui: str, term: str, major_topic: bool
    ) -> None:
        """Create MeSH term node and relationship to paper."""
        query = """
            MERGE (m:MeshTerm {ui: $ui})
            SET m.term = $term
            MERGE (p:Paper {pmid: $pmid})
            MERGE (p)-[:HAS_MESH_TERM {major_topic: $major_topic}]->(m)
        """
        self.client.create_graph(
            query, {"ui": ui, "term": term, "pmid": pmid, "major_topic": major_topic}
        )

    def _create_qualifier_relationship(self, mesh_ui: str, qualifier: str) -> None:
        """Create qualifier node and relationship to MeSH term."""
        query = """
            MERGE (q:Qualifier {name: $qualifier})
            MERGE (m:MeshTerm {ui: $ui})
            MERGE (m)-[:HAS_QUALIFIER]->(q)
        """
        self.client.create_graph(query, {"ui": mesh_ui, "qualifier": qualifier})

    def _create_citation_relationship(self, citing_pmid: str, cited_pmid: str) -> None:
        """Create CITES relationship between two papers."""
        query = """
            MATCH (p1:Paper {pmid: $citing_pmid})
            MATCH (p2:Paper {pmid: $cited_pmid})
            MERGE (p1)-[:CITES]->(p2)
        """
        self.client.create_graph(query, {"citing_pmid": citing_pmid, "cited_pmid": cited_pmid})
