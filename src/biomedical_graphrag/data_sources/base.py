from abc import ABC, abstractmethod
from datetime import datetime

from biomedical_graphrag.domain.citation import CitationNetwork
from biomedical_graphrag.domain.dataset import Dataset, Metadata
from biomedical_graphrag.domain.paper import Paper


class BaseDataSource(ABC):
    """Abstract base class for all biomedical data sources"""

    @abstractmethod
    def search(self, query: str, max_results: int) -> list[str]:
        """
        Search for paper IDs based on query

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of paper IDs (e.g., PMIDs for PubMed)
        """
        pass

    @abstractmethod
    def fetch_papers(self, paper_ids: list[str]) -> list[Paper]:
        """
        Fetch detailed paper information

        Args:
            paper_ids: List of paper identifiers

        Returns:
            List of Paper domain objects
        """
        pass

    @abstractmethod
    def fetch_citations(self, paper_id: str) -> dict:
        """
        Fetch citation network for a paper

        Args:
            paper_id: Paper identifier

        Returns:
            Dictionary with 'cited_by' and 'references' keys
        """
        pass

    def collect_dataset(self, query: str, max_papers: int) -> Dataset:
        """
        High-level method to collect complete dataset with citations

        Args:
            query: Search query
            max_papers: Maximum number of papers to collect

        Returns:
            Complete Dataset with papers, citations, and metadata
        """
        print(f"Searching for papers: '{query}'")
        paper_ids = self.search(query, max_papers)

        print(f"Fetching details for {len(paper_ids)} papers...")
        papers = self.fetch_papers(paper_ids)

        print("Building citation network...")
        citation_network = {}
        for i, paper in enumerate(papers, 1):
            print(f"  Processing citations {i}/{len(papers)}: {paper.title[:50]}...")
            citations = self.fetch_citations(paper.pmid)
            citation_network[paper.pmid] = CitationNetwork(**citations)

        # Calculate metadata
        total_authors = sum(len(paper.authors) for paper in papers)
        total_mesh_terms = sum(len(paper.mesh_terms) for paper in papers)

        metadata = Metadata(
            collection_date=datetime.now().isoformat(),
            query=query,
            total_papers=len(papers),
            papers_with_citations=len(citation_network),
            total_authors=total_authors,
            total_mesh_terms=total_mesh_terms,
        )

        print(f"✓ Dataset collection complete: {len(papers)} papers")

        return Dataset(metadata=metadata, papers=papers, citation_network=citation_network)
