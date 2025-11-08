"""
Semantic Cache using Qdrant + FastEmbed.

This module provides a lightweight semantic caching layer that stores
query-result pairs in Qdrant for fast retrieval of similar queries.

Architecture:
    - Uses FastEmbed (from Qdrant) for fast, local query embeddings
    - Stores cache in separate Qdrant collections (e.g., "clarity_query_cache")
    - Configurable similarity threshold for cache hits
    - Completely separate from document embeddings (different dimensions)

Benefits:
    - No GPTCache dependency (avoiding compatibility issues)
    - Persistent cache (survives restarts)
    - Fast lookups using Qdrant's HNSW index
    - Full control over caching logic
"""

from typing import Optional
import time
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

logger = logging.getLogger(__name__)


class QdrantSemanticCache:
    """
    Semantic cache using Qdrant vector database and FastEmbed.

    Stores query embeddings and their corresponding results in Qdrant.
    When a new query comes in, searches for semantically similar queries
    and returns cached results if similarity exceeds threshold.

    Attributes:
        cache_name (str): Name of the cache (used as collection name suffix)
        qdrant_client (QdrantClient): Qdrant client instance
        embedding_model (TextEmbedding): FastEmbed model for query embeddings
        dimension (int): Embedding dimension (384 for default FastEmbed model)
        similarity_threshold (float): Minimum similarity for cache hits (0.0-1.0)
        collection_name (str): Full Qdrant collection name
    """

    def __init__(
        self,
        cache_name: str,
        qdrant_client: Optional[QdrantClient] = None,
        similarity_threshold: float = 0.90,
        embedding_model_name: str = "BAAI/bge-small-en-v1.5",
    ):
        """
        Initialize semantic cache.

        Args:
            cache_name: Unique name for this cache (e.g., "clarity", "rigor")
            qdrant_client: Qdrant client (creates default if not provided)
            similarity_threshold: Similarity threshold for cache hits (0.0-1.0)
                                 Default 0.90 = 90% similar queries match
            embedding_model_name: FastEmbed model name
                                 Default: BAAI/bge-small-en-v1.5 (384-dim)
        """
        self.cache_name = cache_name
        self.similarity_threshold = similarity_threshold
        self.collection_name = f"{cache_name}_query_cache"

        # Initialize Qdrant client
        if qdrant_client is None:
            from app.config.settings import settings
            self.qdrant_client = QdrantClient(url=settings.qdrant_url)
        else:
            self.qdrant_client = qdrant_client

        # Initialize FastEmbed model (lightweight, fast local embeddings)
        logger.info(f"Initializing FastEmbed model: {embedding_model_name}")
        self.embedding_model = TextEmbedding(model_name=embedding_model_name)
        self.dimension = 384  # BAAI/bge-small-en-v1.5 dimension

        # Create or verify cache collection
        self._ensure_collection_exists()

        # Stats
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_time_saved": 0.0,
        }

        logger.info(
            f"QdrantSemanticCache initialized: {self.collection_name} "
            f"(threshold={similarity_threshold}, dim={self.dimension})"
        )

    def _ensure_collection_exists(self):
        """Create cache collection if it doesn't exist."""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)

            if not collection_exists:
                logger.info(f"Creating cache collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"✓ Cache collection created: {self.collection_name}")
            else:
                logger.info(f"Using existing cache collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Error creating cache collection: {e}")
            raise

    def _embed_query(self, query: str) -> list:
        """
        Generate embedding for a query using FastEmbed.

        Args:
            query: Query text

        Returns:
            Embedding vector as list
        """
        embeddings = list(self.embedding_model.embed([query]))
        return embeddings[0].tolist()

    def get(self, query: str) -> Optional[str]:
        """
        Retrieve cached result for semantically similar query.

        Args:
            query: Query text

        Returns:
            Cached result if found (similarity > threshold), None otherwise
        """
        self.stats["total_queries"] += 1

        try:
            # Generate query embedding
            query_vector = self._embed_query(query)

            # Search for similar queries in cache
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=1,
                score_threshold=self.similarity_threshold,
            )

            if search_result and len(search_result) > 0:
                # Cache hit!
                cached_result = search_result[0].payload.get("result")
                similarity = search_result[0].score
                self.stats["cache_hits"] += 1

                logger.info(
                    f"Cache HIT: '{query[:50]}...' (similarity={similarity:.3f})"
                )
                return cached_result
            else:
                # Cache miss
                self.stats["cache_misses"] += 1
                logger.info(f"Cache MISS: '{query[:50]}...'")
                return None

        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None

    def set(self, query: str, result: str) -> None:
        """
        Store query-result pair in cache.

        Args:
            query: Query text
            result: Result to cache (formatted guidelines text)
        """
        try:
            # Generate query embedding
            query_vector = self._embed_query(query)

            # Create unique ID based on query hash
            point_id = hash(query) % (10**9)  # Use hash for reproducible IDs

            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=query_vector,
                        payload={
                            "query": query,
                            "result": result,
                            "timestamp": time.time(),
                        },
                    )
                ],
            )

            logger.debug(f"Cached query: '{query[:50]}...'")

        except Exception as e:
            logger.error(f"Error storing in cache: {e}")

    def clear(self) -> None:
        """Clear all cached entries (deletes and recreates collection)."""
        try:
            logger.info(f"Clearing cache collection: {self.collection_name}")
            self.qdrant_client.delete_collection(self.collection_name)
            self._ensure_collection_exists()
            logger.info(f"✓ Cache cleared: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache hit/miss stats
        """
        hit_rate = (
            self.stats["cache_hits"] / self.stats["total_queries"]
            if self.stats["total_queries"] > 0
            else 0.0
        )

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "cache_name": self.cache_name,
            "collection_name": self.collection_name,
        }


def create_semantic_cache(
    cache_name: str,
    qdrant_client: Optional[QdrantClient] = None,
    similarity_threshold: float = 0.90,
) -> QdrantSemanticCache:
    """
    Factory function to create a semantic cache.

    Args:
        cache_name: Unique name for this cache (e.g., "clarity", "rigor")
        qdrant_client: Optional Qdrant client
        similarity_threshold: Similarity threshold for cache hits (0.0-1.0)

    Returns:
        Configured QdrantSemanticCache instance

    Example:
        >>> cache = create_semantic_cache("clarity")
        >>> result = cache.get("How to write clear proofs?")
        >>> if not result:
        ...     result = expensive_rag_operation()
        ...     cache.set("How to write clear proofs?", result)
    """
    return QdrantSemanticCache(
        cache_name=cache_name,
        qdrant_client=qdrant_client,
        similarity_threshold=similarity_threshold,
    )
