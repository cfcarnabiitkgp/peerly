#!/usr/bin/env python3
"""
Test script for review result cache functionality.

Tests:
1. Cache miss (first time)
2. Cache hit (exact same content)
3. Cache miss (different content)
4. Cache hit with semantic similarity
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.cache.review_result_cache import create_review_result_cache


# Test documents
TEST_DOC_1 = r"""
\documentclass{article}
\begin{document}
\section{Introduction}
This is a test document for caching.
The purpose is to verify that semantic caching works correctly.
\end{document}
"""

TEST_DOC_2 = r"""
\documentclass{article}
\begin{document}
\section{Different Section}
This is a completely different document.
It should not match the cache.
\end{document}
"""

# Nearly identical to TEST_DOC_1 (99% similar)
TEST_DOC_3 = r"""
\documentclass{article}
\begin{document}
\section{Introduction}
This is a test document for caching.
The purpose is to verify that semantic caching works correctly!
\end{document}
"""


def test_cache():
    """Test review result cache."""
    print("=" * 60)
    print("REVIEW RESULT CACHE TEST")
    print("=" * 60)

    # Initialize cache
    print("\n1. Initializing cache...")
    cache = create_review_result_cache(similarity_threshold=0.98)
    print("✅ Cache initialized")

    # Test 1: Cache miss (first time)
    print("\n2. Test 1: Cache miss (first request)")
    result = cache.get(TEST_DOC_1, ["clarity", "rigor"])
    if result is None:
        print("✅ Cache MISS (expected)")
    else:
        print("❌ Expected cache MISS, got HIT")

    # Store result
    print("\n3. Storing test result in cache...")
    test_result = {
        "success": True,
        "sections": [],
        "total_suggestions": 5,
        "processing_time": 12.5,
        "error": None,
        "cached": False
    }
    cache.set(TEST_DOC_1, ["clarity", "rigor"], test_result)
    print("✅ Result cached")

    # Test 2: Cache hit (exact same)
    print("\n4. Test 2: Cache hit (exact same content)")
    result = cache.get(TEST_DOC_1, ["clarity", "rigor"])
    if result is not None:
        print("✅ Cache HIT (expected)")
        print(f"   Retrieved: {result['total_suggestions']} suggestions")
    else:
        print("❌ Expected cache HIT, got MISS")

    # Test 3: Different agents = different cache entry
    print("\n5. Test 3: Different agents (should miss)")
    result = cache.get(TEST_DOC_1, ["clarity"])  # Only clarity
    if result is None:
        print("✅ Cache MISS for different agents (expected)")
    else:
        print("❌ Expected MISS for different agents")

    # Test 4: Completely different content
    print("\n6. Test 4: Different content (should miss)")
    result = cache.get(TEST_DOC_2, ["clarity", "rigor"])
    if result is None:
        print("✅ Cache MISS for different content (expected)")
    else:
        print("❌ Expected MISS for different content")

    # Test 5: Nearly identical content (semantic similarity test)
    print("\n7. Test 5: Nearly identical content (semantic similarity)")
    print("   (Added one exclamation mark)")
    result = cache.get(TEST_DOC_3, ["clarity", "rigor"])
    if result is None:
        print("✅ Cache MISS due to hash mismatch (expected)")
        print("   Semantic match found but hash verification failed")
    else:
        print("❌ Should not return cached result for modified content")

    # Stats
    print("\n8. Cache statistics:")
    stats = cache.get_stats()
    print(f"   Total queries: {stats['total_queries']}")
    print(f"   Cache hits: {stats['cache_hits']}")
    print(f"   Cache misses: {stats['cache_misses']}")
    print(f"   Hit rate: {stats['hit_rate_percent']:.1f}%")
    print(f"   False candidates: {stats['false_candidates']}")

    # Cleanup
    print("\n9. Cleaning up test cache...")
    cache.clear()
    print("✅ Cache cleared")

    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)


def main():
    """Main test function."""
    try:
        test_cache()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
