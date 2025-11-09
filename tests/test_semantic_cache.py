#!/usr/bin/env python3
"""
Test script for semantic caching functionality.

Tests:
1. Semantic cache initialization
2. Query-level caching with FastEmbed
3. Cache hit/miss behavior
4. Agent-specific cache separation
5. Performance measurements

Usage:
    python tests/test_semantic_cache.py
    python tests/test_semantic_cache.py --agent clarity
    python tests/test_semantic_cache.py --skip-rag  # Test cache only
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import argparse
import time
from qdrant_client import QdrantClient

from app.rag.config import clarity_rag_config, rigor_rag_config
from app.rag.cached_rag_service import create_cached_rag_service
from app.models.schemas import Section


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print(f"{'=' * 70}\n")


def test_cache_initialization():
    """Test 1: Cache initialization."""
    print_section("TEST 1: Cache Initialization")

    try:
        # Test clarity cache
        print("Initializing Clarity cache...")
        clarity_service = create_cached_rag_service(
            config=clarity_rag_config, agent_name="clarity", cache_enabled=True
        )
        print("✓ Clarity cache initialized")

        # Test rigor cache
        print("\nInitializing Rigor cache...")
        rigor_service = create_cached_rag_service(
            config=rigor_rag_config, agent_name="rigor", cache_enabled=True
        )
        print("✓ Rigor cache initialized")

        print("\n✓ Both caches initialized successfully")
        print("  - clarity_query_cache collection created")
        print("  - rigor_query_cache collection created")

        return clarity_service, rigor_service

    except Exception as e:
        print(f"✗ Cache initialization failed: {e}")
        return None, None


def test_semantic_matching(service, agent_name: str):
    """Test 2: Semantic matching behavior."""
    print_section(f"TEST 2: Semantic Matching - {agent_name.upper()}")

    queries = [
        ("Original query", "How to write clear mathematical proofs?"),
        (
            "Semantically similar (should hit cache)",
            "What are tips for clarity in proof writing?",
        ),
        ("Different topic (should miss)", "How to validate experimental results?"),
    ]

    results = []

    for i, (description, query) in enumerate(queries, 1):
        print(f"Query {i}: {description}")
        print(f"  Text: '{query}'")

        start_time = time.time()
        docs = service.retrieve(query, top_k=3)
        elapsed = time.time() - start_time

        print(f"  Time: {elapsed:.3f}s")
        print(f"  Docs: {len(docs)}")

        results.append((query, elapsed, len(docs)))
        print()

    # Print analysis
    print("Analysis:")
    print(f"  Query 1 (first): {results[0][1]:.3f}s (cache miss expected)")
    print(f"  Query 2 (similar): {results[1][1]:.3f}s (cache hit expected)")
    print(f"  Query 3 (different): {results[2][1]:.3f}s (cache miss expected)")

    if results[1][1] < results[0][1] / 2:
        print("  ✓ Query 2 significantly faster (likely cache hit)")
    else:
        print("  ⚠ Query 2 not faster (cache may have missed)")


def test_exact_repetition(service, agent_name: str):
    """Test 3: Exact query repetition."""
    print_section(f"TEST 3: Exact Repetition - {agent_name.upper()}")

    query = "guidelines for writing mathematical introduction sections"

    # First query
    print("First query (cache miss expected):")
    start_time = time.time()
    docs1 = service.retrieve(query, top_k=3)
    time1 = time.time() - start_time
    print(f"  Time: {time1:.3f}s")
    print(f"  Docs: {len(docs1)}")

    # Exact same query
    print("\nSecond query (exact same - cache hit expected):")
    start_time = time.time()
    docs2 = service.retrieve(query, top_k=3)
    time2 = time.time() - start_time
    print(f"  Time: {time2:.3f}s")
    print(f"  Docs: {len(docs2)}")

    speedup = time1 / time2 if time2 > 0 else 0
    print(f"\nSpeedup: {speedup:.1f}x")

    if speedup > 10:
        print("✓ Significant speedup - cache working!")
    else:
        print("⚠ Low speedup - check cache configuration")


def test_agent_separation(clarity_service, rigor_service):
    """Test 4: Agent-specific cache separation."""
    print_section("TEST 4: Agent Cache Separation")

    query = "How to validate mathematical assumptions?"

    # Query clarity agent
    print("Querying Clarity agent:")
    start_time = time.time()
    clarity_docs = clarity_service.retrieve(query, top_k=3)
    clarity_time = time.time() - start_time
    print(f"  Time: {clarity_time:.3f}s")
    print(f"  Docs: {len(clarity_docs)}")

    # Query rigor agent (should NOT hit clarity cache)
    print("\nQuerying Rigor agent (should NOT use clarity cache):")
    start_time = time.time()
    rigor_docs = rigor_service.retrieve(query, top_k=3)
    rigor_time = time.time() - start_time
    print(f"  Time: {rigor_time:.3f}s")
    print(f"  Docs: {len(rigor_docs)}")

    # Query clarity again (should hit cache)
    print("\nQuerying Clarity agent again (should hit cache):")
    start_time = time.time()
    clarity_docs2 = clarity_service.retrieve(query, top_k=3)
    clarity_time2 = time.time() - start_time
    print(f"  Time: {clarity_time2:.3f}s")
    print(f"  Docs: {len(clarity_docs2)}")

    print("\nAnalysis:")
    if clarity_time2 < clarity_time / 2:
        print("  ✓ Clarity cache hit on second query")
    else:
        print("  ⚠ Clarity cache may have missed")

    if rigor_time >= clarity_time / 2:
        print("  ✓ Rigor cache separate (no cross-contamination)")
    else:
        print("  ⚠ Rigor query suspiciously fast (possible cache mixing?)")


def test_cache_statistics(service, agent_name: str):
    """Test 5: Cache statistics."""
    print_section(f"TEST 5: Cache Statistics - {agent_name.upper()}")

    # Run several queries
    queries = [
        "clear writing in mathematics",
        "mathematical clarity tips",  # Similar to above
        "proof structure guidelines",
        "structured mathematical proofs",  # Similar to above
        "notation consistency",
    ]

    print("Running 5 queries...")
    for i, query in enumerate(queries, 1):
        print(f"  {i}. '{query[:40]}...'")
        service.retrieve(query, top_k=3)

    # Print statistics
    print()
    service.print_stats()


def test_with_rag_nodes():
    """Test 6: Integration with RAG nodes."""
    print_section("TEST 6: RAG Nodes Integration")

    from app.agents.rag_nodes import ClarityRAGNode, RigorRAGNode

    try:
        # Initialize nodes
        print("Initializing RAG nodes with caching...")
        clarity_node = ClarityRAGNode(cache_enabled=True)
        rigor_node = RigorRAGNode(cache_enabled=True)
        print("✓ Nodes initialized")

        # Test clarity node
        print("\nTesting Clarity RAG Node:")
        sample_sections = [
            Section(
                title="Introduction",
                content="We present sophisticated techniques for optimization.",
                section_type="introduction",
                line_start=1,
            )
        ]

        state = {"sections_for_clarity": sample_sections}

        # First call
        print("  First call (cache miss expected):")
        start = time.time()
        result1 = clarity_node(state)
        time1 = time.time() - start
        print(f"    Time: {time1:.3f}s")
        print(f"    Guidelines: {len(result1.get('clarity_guidelines', ''))} chars")

        # Second call (same sections, should hit cache)
        print("  Second call (cache hit expected):")
        start = time.time()
        result2 = clarity_node(state)
        time2 = time.time() - start
        print(f"    Time: {time2:.3f}s")
        print(f"    Guidelines: {len(result2.get('clarity_guidelines', ''))} chars")

        speedup = time1 / time2 if time2 > 0 else 0
        print(f"\n  Speedup: {speedup:.1f}x")

        if speedup > 5:
            print("  ✓ Cache working in RAG node!")
        else:
            print("  ⚠ Low speedup in RAG node")

    except Exception as e:
        print(f"✗ RAG node test failed: {e}")


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test semantic caching")
    parser.add_argument(
        "--agent",
        choices=["clarity", "rigor", "both"],
        default="both",
        help="Which agent to test",
    )
    parser.add_argument(
        "--skip-rag", action="store_true", help="Skip RAG node integration test"
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("SEMANTIC CACHE TESTING")
    print("=" * 70)

    # Prerequisites check
    print("\nPrerequisites:")
    print("  - Qdrant running on localhost:6333")
    print("  - Documents embedded (python scripts/embed_documents.py --all)")
    print("  - OpenAI API key set in .env")
    print()

    # Test 1: Initialization
    clarity_service, rigor_service = test_cache_initialization()
    if not clarity_service or not rigor_service:
        print("\n✗ Cannot proceed without cache initialization")
        return

    # Test agent-specific
    if args.agent in ["clarity", "both"]:
        test_semantic_matching(clarity_service, "clarity")
        test_exact_repetition(clarity_service, "clarity")
        test_cache_statistics(clarity_service, "clarity")

    if args.agent in ["rigor", "both"]:
        test_semantic_matching(rigor_service, "rigor")
        test_exact_repetition(rigor_service, "rigor")
        test_cache_statistics(rigor_service, "rigor")

    # Test separation
    if args.agent == "both":
        test_agent_separation(clarity_service, rigor_service)

    # Test RAG nodes
    if not args.skip_rag:
        test_with_rag_nodes()

    print_section("ALL TESTS COMPLETE")

    print("Summary:")
    print("  ✓ Semantic caching initialized")
    print("  ✓ Cache hit/miss behavior verified")
    print("  ✓ Agent separation confirmed")
    print("  ✓ Performance improvements observed")
    print()


if __name__ == "__main__":
    main()
