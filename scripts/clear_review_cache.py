#!/usr/bin/env python3
"""
Script to clear the review result cache.

Usage:
    python scripts/clear_review_cache.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.cache.review_result_cache import create_review_result_cache
from app.config.settings import settings


def main():
    """Clear the review result cache."""
    print("=" * 60)
    print("Clear Review Result Cache")
    print("=" * 60)

    if not settings.review_cache_enabled:
        print("⚠️  Review cache is disabled in settings")
        return

    # Create cache instance
    print("Connecting to Qdrant...")
    cache = create_review_result_cache()

    # Get stats before clearing
    stats = cache.get_stats()
    print(f"\nCache stats before clearing:")
    print(f"  Total queries: {stats['total_queries']}")
    print(f"  Cache hits: {stats['cache_hits']}")
    print(f"  Hit rate: {stats['hit_rate_percent']:.1f}%")

    # Clear cache
    print("\nClearing cache...")
    cache.clear()

    print("✅ Review result cache cleared successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
