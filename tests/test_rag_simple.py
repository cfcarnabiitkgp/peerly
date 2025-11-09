#!/usr/bin/env python3
"""
Simple command-line script to test RAG functionality for both agents.

Usage:
    python tests/test_rag_simple.py
    python tests/test_rag_simple.py --agent clarity
    python tests/test_rag_simple.py --agent rigor
    python tests/test_rag_simple.py --query "your custom query"
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import argparse
import time
from qdrant_client import QdrantClient
from app.rag.config import clarity_rag_config, rigor_rag_config
from app.rag.rag_service import RAGService
from app.agents.rag_nodes import ClarityRAGNode, RigorRAGNode
from app.models.schemas import Section


def test_connection():
    """Test Qdrant connection."""
    print("\n" + "=" * 60)
    print("TESTING QDRANT CONNECTION")
    print("=" * 60)

    try:
        client = QdrantClient(url="http://localhost:6333")
        collections = client.get_collections()

        if not collections.collections:
            print("⚠️  No collections found!")
            print("   Run: python scripts/embed_documents.py --all")
            return None

        print("\n✓ Qdrant connected successfully")
        print(f"   Collections: {len(collections.collections)}")

        for collection in collections.collections:
            info = client.get_collection(collection.name)
            print(f"   - {collection.name}: {info.points_count} points")

        return client

    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")
        print("   Make sure Qdrant is running:")
        print("   docker run -p 6333:6333 qdrant/qdrant")
        return None


def test_agent_rag(agent_type: str, qdrant_client: QdrantClient, query: str = None):
    """Test RAG for a specific agent."""
    print(f"\n{'=' * 60}")
    print(f"TESTING {agent_type.upper()} AGENT RAG")
    print("=" * 60)

    # Select config and service
    if agent_type == "clarity":
        config = clarity_rag_config
        default_queries = [
            "how to write clear mathematical statements",
            "avoiding complex sentences",
            "defining technical terms",
        ]
    else:
        config = rigor_rag_config
        default_queries = [
            "mathematical proof validation",
            "stating assumptions in theorems",
            "experimental rigor",
        ]

    service = RAGService(config=config, qdrant_client=qdrant_client)

    # Use custom query or defaults
    queries = [query] if query else default_queries

    for i, q in enumerate(queries, 1):
        print(f"\n{'─' * 60}")
        print(f"Query {i}: {q}")
        print("─" * 60)

        try:
            # Retrieve
            start = time.time()
            results = service.retrieve(q, top_k=3)
            latency = time.time() - start

            print(f"⏱️  Latency: {latency*1000:.0f}ms")
            print(f"📄 Retrieved {len(results)} documents\n")

            # Display results
            for j, doc in enumerate(results, 1):
                source = doc.metadata.get("source", "Unknown")
                print(f"{j}. {source}")
                print(f"   {doc.page_content[:150]}...\n")

        except Exception as e:
            print(f"❌ Error: {e}")


def test_rag_nodes(qdrant_client: QdrantClient):
    """Test RAG nodes in workflow context."""
    print("\n" + "=" * 60)
    print("TESTING RAG NODES (WORKFLOW)")
    print("=" * 60)

    # Create nodes
    clarity_node = ClarityRAGNode(qdrant_client=qdrant_client)
    rigor_node = RigorRAGNode(qdrant_client=qdrant_client)

    # Sample sections
    sample_sections = [
        Section(
            title="Introduction",
            content="We present a novel algorithm for optimization using sophisticated mathematical techniques.",
            section_type="introduction",
            line_start=1,
        ),
        Section(
            title="Methodology",
            content="Our proof relies on the following theorem without validation of assumptions.",
            section_type="methodology",
            line_start=50,
        ),
    ]

    # Test clarity node
    print("\n📘 Clarity RAG Node")
    print("─" * 60)

    clarity_state = {"sections_for_clarity": sample_sections}
    clarity_result = clarity_node(clarity_state)
    clarity_guidelines = clarity_result.get("clarity_guidelines", "")

    if clarity_guidelines:
        print(f"✓ Retrieved guidelines ({len(clarity_guidelines)} chars)")
        print(f"\nPreview:\n{clarity_guidelines[:300]}...\n")
    else:
        print("⚠️  No guidelines retrieved")

    # Test rigor node
    print("\n📗 Rigor RAG Node")
    print("─" * 60)

    rigor_state = {"sections_for_rigor": [sample_sections[1]]}
    rigor_result = rigor_node(rigor_state)
    rigor_guidelines = rigor_result.get("rigor_guidelines", "")

    if rigor_guidelines:
        print(f"✓ Retrieved guidelines ({len(rigor_guidelines)} chars)")
        print(f"\nPreview:\n{rigor_guidelines[:300]}...\n")
    else:
        print("⚠️  No guidelines retrieved")


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test RAG system for agents")
    parser.add_argument(
        "--agent",
        choices=["clarity", "rigor", "both"],
        default="both",
        help="Which agent to test",
    )
    parser.add_argument("--query", type=str, help="Custom query to test")
    parser.add_argument(
        "--nodes", action="store_true", help="Test RAG nodes in workflow"
    )

    args = parser.parse_args()

    # Test connection
    qdrant_client = test_connection()
    if not qdrant_client:
        return

    # Test agents
    if args.agent in ["clarity", "both"]:
        test_agent_rag("clarity", qdrant_client, args.query)

    if args.agent in ["rigor", "both"]:
        test_agent_rag("rigor", qdrant_client, args.query)

    # Test nodes if requested
    if args.nodes:
        test_rag_nodes(qdrant_client)

    print("\n" + "=" * 60)
    print("✓ ALL TESTS COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
