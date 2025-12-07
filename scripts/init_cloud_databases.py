#!/usr/bin/env python3
"""
Initialize cloud databases (Neo4j Aura + Qdrant Cloud) with biomedical data.

Usage:
    python scripts/init_cloud_databases.py

Make sure your .env file has the cloud database credentials.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def main() -> None:
    """Initialize both databases."""
    # Import after path setup
    from biomedical_graphrag.infrastructure.neo4j_db.create_graph import create_graph
    from biomedical_graphrag.infrastructure.qdrant_db.qdrant_ingestion import ingest_data

    print("\n" + "=" * 60)
    print("🚀 Biomedical GraphRAG - Cloud Database Initialization")
    print("=" * 60 + "\n")

    # Step 1: Create Neo4j graph
    print("📊 Step 1/2: Creating Neo4j knowledge graph...")
    print("-" * 40)
    try:
        await create_graph()
        print("✅ Neo4j graph created successfully!\n")
    except Exception as e:
        print(f"❌ Neo4j setup failed: {e}")
        print("   Make sure Neo4j Aura credentials are correct in .env\n")
        return

    # Step 2: Ingest Qdrant embeddings
    print("🔍 Step 2/2: Creating Qdrant embeddings...")
    print("-" * 40)
    try:
        await ingest_data(recreate=True)
        print("✅ Qdrant embeddings created successfully!\n")
    except Exception as e:
        print(f"❌ Qdrant setup failed: {e}")
        print("   Make sure Qdrant Cloud credentials are correct in .env\n")
        return

    print("=" * 60)
    print("🎉 All done! Your cloud databases are ready.")
    print("   You can now use your deployed app!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

