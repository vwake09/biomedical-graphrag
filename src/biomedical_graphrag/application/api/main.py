"""FastAPI backend for Biomedical GraphRAG service."""

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from biomedical_graphrag.application.services.hybrid_service.tool_calling import (
    run_graph_enrichment,
    summarize_fused_results,
)
from biomedical_graphrag.application.services.query_vectorstore_service.qdrant_query import (
    AsyncQdrantQuery,
)
from biomedical_graphrag.utils.logger_util import setup_logging

logger = setup_logging()


def find_frontend_path() -> Path | None:
    """Find the frontend directory in various possible locations."""
    possible_paths = [
        # Docker container path
        Path("/app/frontend"),
        # Relative to this file (development)
        Path(__file__).parent.parent.parent.parent.parent / "frontend",
        # Current working directory
        Path.cwd() / "frontend",
        # Environment variable override
        Path(os.environ.get("FRONTEND_PATH", "")) if os.environ.get("FRONTEND_PATH") else None,
    ]

    for path in possible_paths:
        if path and path.exists() and (path / "index.html").exists():
            logger.info(f"📁 Frontend found at: {path}")
            return path

    logger.warning("⚠️ Frontend directory not found")
    return None


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for queries."""

    question: str
    query_type: str = "hybrid"  # "hybrid" or "vector"
    top_k: int = 5


class QueryResponse(BaseModel):
    """Response model for queries."""

    answer: str
    sources: list[dict[str, Any]] | None = None
    query_type: str
    neo4j_enrichment: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    services: dict[str, str]


# Global variables
qdrant_client: AsyncQdrantQuery | None = None
static_path: Path | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global qdrant_client, static_path
    logger.info("🚀 Starting Biomedical GraphRAG API...")

    # Find frontend path
    static_path = find_frontend_path()

    # Mount static files if frontend exists
    if static_path:
        app.mount("/static", StaticFiles(directory=static_path), name="static")

    # Initialize Qdrant client
    qdrant_client = AsyncQdrantQuery()

    yield

    logger.info("🛑 Shutting down Biomedical GraphRAG API...")
    if qdrant_client:
        await qdrant_client.close()


app = FastAPI(
    title="Biomedical GraphRAG API",
    description="A hybrid GraphRAG system combining Neo4j knowledge graphs with Qdrant vector search for biomedical research",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serve the frontend HTML."""
    if static_path:
        index_path = static_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend not found. Set FRONTEND_PATH env var.")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        services={
            "api": "running",
            "qdrant": "connected" if qdrant_client else "disconnected",
            "neo4j": "available",
        },
    )


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Execute a query against the biomedical knowledge base.

    - **hybrid**: Combines Qdrant vector search with Neo4j graph enrichment
    - **vector**: Uses only Qdrant vector search
    """
    if not qdrant_client:
        raise HTTPException(status_code=503, detail="Qdrant client not initialized")

    try:
        logger.info(f"📝 Processing query: {request.question[:100]}...")

        # Step 1: Retrieve documents from Qdrant
        documents = await qdrant_client.retrieve_documents(request.question, request.top_k)
        qdrant_chunks = [
            f"PMID: {doc['payload']['paper']['pmid']}\n"
            f"Title: {doc['payload']['paper']['title']}\n"
            f"Abstract: {doc['payload']['paper']['abstract']}"
            for doc in documents
            if doc.get("payload", {}).get("paper")
        ]

        sources = [
            {
                "pmid": doc["payload"]["paper"]["pmid"],
                "title": doc["payload"]["paper"]["title"],
                "score": doc["score"],
                "journal": doc["payload"]["paper"].get("journal"),
                "publication_date": doc["payload"]["paper"].get("publication_date"),
                "authors": doc["payload"]["paper"].get("authors", [])[:3],  # First 3 authors
            }
            for doc in documents
            if doc.get("payload", {}).get("paper")
        ]

        if request.query_type == "hybrid":
            # Step 2: Run graph enrichment with Neo4j
            neo4j_results = await asyncio.to_thread(
                run_graph_enrichment, request.question, qdrant_chunks
            )

            # Step 3: Summarize fused results
            answer = await asyncio.to_thread(
                summarize_fused_results, request.question, qdrant_chunks, neo4j_results
            )

            return QueryResponse(
                answer=answer,
                sources=sources,
                query_type="hybrid",
                neo4j_enrichment=neo4j_results,
            )
        else:
            # Vector-only query
            answer = await qdrant_client.get_answer(request.question)
            return QueryResponse(
                answer=answer,
                sources=sources,
                query_type="vector",
                neo4j_enrichment=None,
            )

    except Exception as e:
        logger.error(f"❌ Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get statistics about the knowledge base."""
    return {
        "papers_indexed": 824,
        "neo4j_nodes": {
            "papers": 1000,
            "authors": 4529,
            "mesh_terms": 8777,
            "genes": 1374,
        },
        "citation_relationships": 33541,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

