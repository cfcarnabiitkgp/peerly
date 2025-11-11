#!/usr/bin/env python3
"""
Script to display cache statistics for all caches.

Shows statistics for:
- Review result cache (full document analysis)
- RAG semantic cache (clarity guidelines)
- RAG semantic cache (rigor guidelines)

Usage:
    python scripts/cache_stats.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.cache.review_result_cache import create_review_result_cache
from app.config.settings import settings


def format_time(seconds):
    """Format seconds into human-readable time."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def print_review_cache_stats():
    """Print review result cache statistics."""
    print("\n" + "=" * 60)
    print("REVIEW RESULT CACHE")
    print("=" * 60)

    if not settings.review_cache_enabled:
        print("⚠️  Review result cache is disabled")
        return

    try:
        cache = create_review_result_cache()
        stats = cache.get_stats()

        print(f"Status:              ENABLED")
        print(f"Collection:          {stats['collection_name']}")
        print(f"Similarity Threshold: {stats['similarity_threshold']}")
        print(f"Fingerprint Length:  {stats['max_fingerprint_length']} chars")
        print(f"\nStatistics:")
        print(f"  Total Queries:     {stats['total_queries']}")
        print(f"  Cache Hits:        {stats['cache_hits']}")
        print(f"  Cache Misses:      {stats['cache_misses']}")
        print(f"  Hit Rate:          {stats['hit_rate_percent']:.1f}%")
        print(f"  Time Saved:        {format_time(stats['total_time_saved'])}")
        print(f"  False Candidates:  {stats['false_candidates']}")

        if stats['total_queries'] > 0:
            avg_time_saved = stats['total_time_saved'] / stats['cache_hits'] if stats['cache_hits'] > 0 else 0
            print(f"  Avg Time/Hit:      {format_time(avg_time_saved)}")

    except Exception as e:
        print(f"❌ Error accessing review cache: {e}")


def print_rag_cache_stats():
    """Print RAG semantic cache statistics."""
    print("\n" + "=" * 60)
    print("RAG SEMANTIC CACHE")
    print("=" * 60)

    if not settings.use_semantic_cache:
        print("⚠️  RAG semantic cache is disabled")
        return

    try:
        # Try to import and get stats from RAG caches
        from app.agents.rag_nodes import ClarityRAGNode, RigorRAGNode

        print("\nClarity Guidelines Cache:")
        try:
            clarity_node = ClarityRAGNode()
            if hasattr(clarity_node, 'rag_service') and hasattr(clarity_node.rag_service, 'get_stats'):
                clarity_stats = clarity_node.rag_service.get_stats()
                print(f"  Total Queries:  {clarity_stats.get('total_queries', 0)}")
                print(f"  Cache Hits:     {clarity_stats.get('cache_hits', 0)}")
                print(f"  Hit Rate:       {clarity_stats.get('hit_rate_percent', 0):.1f}%")
        except Exception as e:
            print(f"  ⚠️  Could not load: {e}")

        print("\nRigor Guidelines Cache:")
        try:
            rigor_node = RigorRAGNode()
            if hasattr(rigor_node, 'rag_service') and hasattr(rigor_node.rag_service, 'get_stats'):
                rigor_stats = rigor_node.rag_service.get_stats()
                print(f"  Total Queries:  {rigor_stats.get('total_queries', 0)}")
                print(f"  Cache Hits:     {rigor_stats.get('cache_hits', 0)}")
                print(f"  Hit Rate:       {rigor_stats.get('hit_rate_percent', 0):.1f}%")
        except Exception as e:
            print(f"  ⚠️  Could not load: {e}")

    except ImportError:
        print("⚠️  RAG nodes not available (use_rag=False?)")
    except Exception as e:
        print(f"❌ Error accessing RAG caches: {e}")


def main():
    """Display all cache statistics."""
    print("\n" + "=" * 60)
    print("PEERLY CACHE STATISTICS")
    print("=" * 60)
    print(f"Environment: {settings.railway_environment or 'Local'}")
    print(f"Qdrant URL:  {settings.qdrant_url}")

    # Review result cache stats
    print_review_cache_stats()

    # RAG semantic cache stats
    print_rag_cache_stats()

    print("\n" + "=" * 60)
    print("END OF CACHE STATISTICS")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
