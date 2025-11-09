#!/usr/bin/env python3
"""Debug script for semantic cache Qdrant connection issue."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

print("="*80)
print("Debugging Semantic Cache Qdrant Connection")
print("="*80)

# Test 1: Direct Qdrant connection
print("\n1. Testing direct Qdrant connection...")
try:
    from qdrant_client import QdrantClient
    client = QdrantClient(url="http://localhost:6333")
    collections = client.get_collections()
    print(f"   ✓ Direct connection successful")
    print(f"   Collections: {[c.name for c in collections.collections]}")
except Exception as e:
    print(f"   ✗ Direct connection failed: {e}")

# Test 2: GPTCache manager factory
print("\n2. Testing GPTCache manager_factory...")
try:
    from gptcache.manager import manager_factory
    print("   ✓ manager_factory imported successfully")

    # Try creating just the Qdrant manager
    print("\n3. Creating Qdrant vector manager...")
    data_manager = manager_factory(
        "sqlite,qdrant",
        vector_params={
            "dimension": 384,
            "url": "http://localhost:6333",
            "collection_name": "test_semantic_cache",
        },
    )
    print("   ✓ Qdrant manager created successfully")

except Exception as e:
    print(f"   ✗ Manager creation failed")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error message: {str(e)}")

    # Print full traceback
    import traceback
    print("\n   Full traceback:")
    traceback.print_exc()

# Test 3: Try with different URL formats
print("\n4. Testing different Qdrant URL formats...")
url_formats = [
    "http://localhost:6333",
    "localhost",
    "127.0.0.1",
    "http://127.0.0.1:6333",
]

for url in url_formats:
    try:
        from gptcache.manager import manager_factory
        print(f"\n   Testing URL: {url}")
        data_manager = manager_factory(
            "sqlite,qdrant",
            vector_params={
                "dimension": 384,
                "url": url,
                "collection_name": f"test_cache_{url.replace('://', '_').replace(':', '_').replace('.', '_')}",
            },
        )
        print(f"   ✓ Success with URL: {url}")
        break
    except Exception as e:
        print(f"   ✗ Failed with URL: {url} - {type(e).__name__}: {str(e)[:100]}")

# Test 4: Check GPTCache version and dependencies
print("\n5. Checking GPTCache version and dependencies...")
try:
    import gptcache
    print(f"   GPTCache version: {gptcache.__version__}")
except:
    print("   Could not get GPTCache version")

try:
    from gptcache.adapter.api import get_qdrant_config
    print("   ✓ Qdrant adapter available")
except ImportError as e:
    print(f"   ✗ Qdrant adapter not available: {e}")

print("\n" + "="*80)
print("Debug Complete")
print("="*80)
