"""Example usage of Neo4j graph querying with LangChain."""

from biomedical_graphrag.infrastructure.neo4j_db.neo4j_query import (
    BiomedicalGraphQueries,
    Neo4jGraphQuery,
)


def main() -> None:
    """Run various query examples."""
    # Initialize query handler
    query_handler = Neo4jGraphQuery()

    print("=" * 80)
    print("Example 1: Natural Language Query")
    print("=" * 80)
    answer = query_handler.ask("Which authors work on cancer research?")
    print(f"Answer: {answer}\n")

    print("=" * 80)
    print("Example 2: Pre-built Query - Find Papers by MeSH Term")
    print("=" * 80)
    results = query_handler.query(BiomedicalGraphQueries.find_papers_by_mesh_term("CRISPR"))
    for result in results[:5]:
        print(f"  [{result['pmid']}] {result['title']}")
    print()

    print("=" * 80)
    print("Example 3: Pre-built Query - Find Prolific Authors")
    print("=" * 80)
    results = query_handler.query(BiomedicalGraphQueries.find_prolific_authors(min_papers=1))
    for result in results[:5]:
        print(f"  {result['author']}: {result['paper_count']} papers")
    print()

    print("=" * 80)
    print("Example 4: Custom Cypher Query")
    print("=" * 80)
    custom_query = """
        MATCH (p:Paper)-[:HAS_MESH_TERM]->(m:MeshTerm)
        WHERE m.term CONTAINS 'gene editing'
        RETURN DISTINCT p.title, p.pmid, p.publication_date
        ORDER BY p.publication_date DESC
        LIMIT 5
    """
    results = query_handler.query(custom_query)
    for result in results:
        print(f"  [{result['pmid']}] {result['title']} ({result['publication_date']})")
    print()

    print("=" * 80)
    print("Example 5: Find Citation Network")
    print("=" * 80)
    # Get first paper PMID
    first_paper = query_handler.query("MATCH (p:Paper) RETURN p.pmid LIMIT 1")
    if first_paper:
        pmid = first_paper[0]["p.pmid"]
        results = query_handler.query(BiomedicalGraphQueries.find_citation_network(pmid, depth=1))
        if results:
            print(f"  Papers cited by {pmid}:")
            for result in results[:3]:
                print(f"    - [{result['related_pmid']}] {result['related_title'][:60]}...")
        else:
            print(f"  No citations found for {pmid}")
    print()

    print("=" * 80)
    print("Example 6: Find Related Papers by Shared MeSH Terms")
    print("=" * 80)
    if first_paper:
        pmid = first_paper[0]["p.pmid"]
        results = query_handler.query(BiomedicalGraphQueries.find_related_papers_by_mesh(pmid))
        if results:
            print(f"  Papers related to {pmid}:")
            for result in results[:3]:
                print(
                    f"    - [{result['pmid']}] {result['title'][:60]}... "
                    f"({result['shared_terms']} shared terms)"
                )
        else:
            print(f"  No related papers found for {pmid}")
    print()

    print("=" * 80)
    print("All examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
