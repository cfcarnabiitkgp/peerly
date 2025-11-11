#!/usr/bin/env python3
"""
Script to prune old entries from the review result cache.

Removes cache entries older than a specified number of days.

Usage:
    python scripts/prune_old_cache.py [days]

    Default: 7 days

Examples:
    python scripts/prune_old_cache.py       # Remove entries older than 7 days
    python scripts/prune_old_cache.py 30    # Remove entries older than 30 days
"""
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from app.config.settings import settings


def prune_old_cache_entries(days: int = 7):
    """
    Remove cache entries older than specified days.

    Args:
        days: Number of days to keep (entries older than this will be deleted)
    """
    print("=" * 60)
    print(f"Prune Old Review Cache Entries (>{days} days)")
    print("=" * 60)

    if not settings.review_cache_enabled:
        print("⚠️  Review cache is disabled in settings")
        return

    # Connect to Qdrant
    print(f"Connecting to Qdrant at {settings.qdrant_url}...")
    client = QdrantClient(url=settings.qdrant_url)
    collection_name = "review_results_cache"

    # Calculate cutoff timestamp
    cutoff_timestamp = time.time() - (days * 24 * 60 * 60)
    print(f"Cutoff date: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cutoff_timestamp))}")

    try:
        # Check if collection exists
        collections = client.get_collections().collections
        collection_exists = any(c.name == collection_name for c in collections)

        if not collection_exists:
            print(f"⚠️  Collection '{collection_name}' does not exist")
            return

        # Get collection info
        collection_info = client.get_collection(collection_name)
        total_points = collection_info.points_count
        print(f"Total cache entries: {total_points}")

        # Scroll through all points and filter old ones
        print("\nScanning cache entries...")
        old_point_ids = []
        offset = None

        while True:
            # Scroll through points
            result, offset = client.scroll(
                collection_name=collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            if not result:
                break

            # Check each point's timestamp
            for point in result:
                timestamp = point.payload.get("timestamp", 0)
                if timestamp < cutoff_timestamp:
                    old_point_ids.append(point.id)

            if offset is None:
                break

        # Delete old entries
        if old_point_ids:
            print(f"\nFound {len(old_point_ids)} old entries to delete...")
            client.delete(
                collection_name=collection_name,
                points_selector=old_point_ids
            )
            print(f"✅ Deleted {len(old_point_ids)} old cache entries")
            print(f"Remaining entries: {total_points - len(old_point_ids)}")
        else:
            print("\n✅ No old entries found (all entries are recent)")

    except Exception as e:
        print(f"❌ Error pruning cache: {e}")

    print("=" * 60)


def main():
    """Main function."""
    # Get days from command line argument
    days = 7  # Default
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print(f"Invalid argument: {sys.argv[1]}")
            print("Usage: python scripts/prune_old_cache.py [days]")
            sys.exit(1)

    prune_old_cache_entries(days)


if __name__ == "__main__":
    main()
