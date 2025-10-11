from pydantic import BaseModel, Field

from biomedical_graphrag.domain.citation import CitationNetwork
from biomedical_graphrag.domain.paper import Paper


class Metadata(BaseModel):
    collection_date: str = Field(default="", description="Date of data collection")
    query: str = Field(default="", description="Query used for data collection")
    total_papers: int = Field(default=0, description="Total number of papers")
    papers_with_citations: int = Field(default=0, description="Number of papers with citations")
    total_authors: int = Field(default=0, description="Total number of authors")
    total_mesh_terms: int = Field(default=0, description="Total number of MeSH terms")


class Dataset(BaseModel):
    metadata: Metadata = Field(default_factory=Metadata, description="Dataset metadata")
    papers: list[Paper] = Field(default_factory=list, description="List of papers in the dataset")
    citation_network: dict[str, CitationNetwork] = Field(
        default_factory=dict,
        description="Citation network mapping paper IDs to their citation details",
    )
