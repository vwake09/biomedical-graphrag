"""CLI script for querying the Neo4j biomedical knowledge graph."""

import argparse
import sys

from biomedical_graphrag.infrastructure.neo4j_db.neo4j_query import (
    BiomedicalGraphQueries,
    Neo4jGraphQuery,
)


def run_example_queries() -> None:
    """Run example queries to demonstrate graph querying capabilities."""
    print("=" * 80)
    print("Biomedical Knowledge Graph - Example Queries")
    print("=" * 80)

    try:
        # Initialize query handler
        print("\nInitializing query handler...")
        query_handler = Neo4jGraphQuery()

        # Show schema
        print("\n" + "=" * 80)
        print("GRAPH SCHEMA")
        print("=" * 80)
        print(query_handler.get_schema())

        # Example 1: Find prolific authors
        print("\n" + "=" * 80)
        print("Example 1: Find authors with multiple papers")
        print("=" * 80)
        results = query_handler.query(BiomedicalGraphQueries.find_prolific_authors(min_papers=1))
        for result in results[:5]:  # Show top 5
            print(f"  - {result['author']}: {result['paper_count']} papers")

        # Example 2: Find papers by MeSH term
        print("\n" + "=" * 80)
        print("Example 2: Find papers about CRISPR")
        print("=" * 80)
        results = query_handler.query(BiomedicalGraphQueries.find_papers_by_mesh_term("CRISPR"))
        for result in results[:3]:  # Show top 3
            major = "(MAJOR TOPIC)" if result.get("is_major_topic") else ""
            print(f"  - [{result['pmid']}] {result['title'][:60]}... {major}")

        # Example 3: Find collaborating institutions
        print("\n" + "=" * 80)
        print("Example 3: Find collaborating institutions")
        print("=" * 80)
        results = query_handler.query(
            BiomedicalGraphQueries.find_collaborating_institutions(min_collaborations=1)
        )
        for result in results[:3]:  # Show top 3
            inst1 = result["institution1"][:40]
            inst2 = result["institution2"][:40]
            print(f"  - {inst1} <-> {inst2}")
            print(f"    Collaborations: {result['collaborations']}")

        print("\n" + "=" * 80)
        print("Query examples completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\nError running queries: {e}", file=sys.stderr)
        raise


def run_natural_language_query(question: str) -> None:
    """
    Run a natural language query using LangChain.

    Args:
        question: Natural language question to ask
    """
    print("=" * 80)
    print("Natural Language Query")
    print("=" * 80)
    print(f"\nQuestion: {question}\n")

    try:
        query_handler = Neo4jGraphQuery()
        answer = query_handler.ask(question)

        print("\n" + "=" * 80)
        print("Answer:")
        print("=" * 80)
        print(answer)

    except Exception as e:
        print(f"\nError processing question: {e}", file=sys.stderr)
        raise


def run_custom_cypher(cypher: str) -> None:
    """
    Run a custom Cypher query.

    Args:
        cypher: Cypher query string
    """
    print("=" * 80)
    print("Custom Cypher Query")
    print("=" * 80)
    print(f"\nQuery:\n{cypher}\n")

    try:
        query_handler = Neo4jGraphQuery()
        results = query_handler.query(cypher)

        print("\n" + "=" * 80)
        print(f"Results: ({len(results)} rows)")
        print("=" * 80)

        if not results:
            print("No results found.")
        else:
            # Print first 10 results
            for i, result in enumerate(results[:10], 1):
                print(f"\nRow {i}:")
                for key, value in result.items():
                    # Truncate long values
                    str_value = str(value)
                    if len(str_value) > 100:
                        str_value = str_value[:97] + "..."
                    print(f"  {key}: {str_value}")

            if len(results) > 10:
                print(f"\n... and {len(results) - 10} more rows")

    except Exception as e:
        print(f"\nError running query: {e}", file=sys.stderr)
        raise


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Query the Neo4j biomedical knowledge graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run example queries
  python -m src.biomedical_graphrag.infrastructure.neo4j_db.query_graph

  # Ask a natural language question
  python -m src.biomedical_graphrag.infrastructure.neo4j_db.query_graph \\
      --ask "Who are the authors working on CRISPR gene editing?"

  # Run a custom Cypher query
  python -m src.biomedical_graphrag.infrastructure.neo4j_db.query_graph \\
      --cypher "MATCH (p:Paper) RETURN p.title LIMIT 5"
        """,
    )

    parser.add_argument(
        "--ask",
        type=str,
        help="Ask a natural language question about the graph",
        metavar="QUESTION",
    )

    parser.add_argument("--cypher", type=str, help="Run a custom Cypher query", metavar="QUERY")

    args = parser.parse_args()

    try:
        if args.ask:
            run_natural_language_query(args.ask)
        elif args.cypher:
            run_custom_cypher(args.cypher)
        else:
            # Default: run example queries
            run_example_queries()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
