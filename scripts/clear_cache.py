#!/usr/bin/env python3
"""Clear semantic cache collections."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.rag.semantic_cache import create_semantic_cache

print("=" * 70)
print("Clearing Semantic Cache Collections")
print("=" * 70)

# Clear clarity cache
print("\n1. Clearing clarity_query_cache...")
try:
    clarity_cache = create_semantic_cache(cache_name="clarity")
    clarity_cache.clear()
    print("   ✓ Clarity cache cleared")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Clear rigor cache
print("\n2. Clearing rigor_query_cache...")
try:
    rigor_cache = create_semantic_cache(cache_name="rigor")
    rigor_cache.clear()
    print("   ✓ Rigor cache cleared")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Clear test caches (optional)
print("\n3. Clearing test caches (optional)...")
for cache_name in ["test", "clarity_test"]:
    try:
        test_cache = create_semantic_cache(cache_name=cache_name)
        test_cache.clear()
        print(f"   ✓ {cache_name}_query_cache cleared")
    except Exception as e:
        print(f"   ○ {cache_name}_query_cache: {e}")

print("\n" + "=" * 70)
print("Cache clearing complete!")
print("=" * 70)
print("\nVerify with:")
print("  curl http://localhost:6333/collections/clarity_query_cache")
print("  curl http://localhost:6333/collections/rigor_query_cache")
