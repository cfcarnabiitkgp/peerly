"""
Cached RAG Service with semantic query-level caching.

This module wraps RAGService with semantic caching to avoid expensive
RAG retrievals for similar queries.

Cache Architecture:
    1. Check semantic cache (FastEmbed + Qdrant) → 0.02s
    2. If miss, run RAG (OpenAI + Qdrant) → 1.2s
    3. Store result in cache for future queries

Separate caches per agent ensure no mixing between clarity and rigor.
"""

from typing import List, Optional
from qdrant_client import QdrantClient
import time
import logging

from app.rag.rag_service import RAGService
from app.rag.config import RAGConfig
from app.rag.semantic_cache import create_semantic_cache, QdrantSemanticCache
from app.rag.base import Document

logger = logging.getLogger(__name__)


class CachedRAGService:
    """
    RAG Service with semantic query-level caching.

    This wrapper adds a semantic cache layer on top of RAGService.
    For each query, it first checks if a semantically similar query
    was answered before. If not, it runs the full RAG pipeline.

    The cache is agent-specific to prevent mixing clarity and rigor results.

    Attributes:
        rag_service (RAGService): Underlying RAG service
        cache (QdrantSemanticCache): Qdrant-based semantic cache
        agent_name (str): Agent name (for logging)
    """

    def __init__(
        self,
        config: RAGConfig,
        agent_name: str,
        qdrant_client: Optional[QdrantClient] = None,
        cache_enabled: bool = True,
        cache_similarity_threshold: float = 0.90,
    ):
        """
        Initialize cached RAG service.

        Args:
            config: RAG configuration for this agent
            agent_name: Agent name (e.g., "clarity", "rigor")
                       Used as cache namespace to keep agents separate
            qdrant_client: Optional Qdrant client (created if not provided)
            cache_enabled: Whether to enable semantic caching
            cache_similarity_threshold: Similarity threshold for cache hits (0.0-1.0)
                                       Default 0.90 = 90% similar queries match
        """
        self.agent_name = agent_name
        self.cache_enabled = cache_enabled

        # Initialize underlying RAG service
        logger.info(f"Initializing RAG service for {agent_name}")
        self.rag_service = RAGService(config=config, qdrant_client=qdrant_client)

        # Initialize semantic cache (agent-specific, uses same Qdrant instance)
        if cache_enabled:
            logger.info(f"Initializing Qdrant semantic cache for {agent_name}")
            self.cache = create_semantic_cache(
                cache_name=agent_name,
                qdrant_client=qdrant_client,
                similarity_threshold=cache_similarity_threshold,
            )
        else:
            self.cache = None
            logger.info(f"Semantic cache disabled for {agent_name}")

        # Stats
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_time_saved": 0.0,  # seconds
        }

    def retrieve(self, query: str, top_k: int = 3) -> List[Document]:
        """
        Retrieve documents with semantic caching.

        Flow:
            1. Check semantic cache (FastEmbed lookup)
            2. If hit: Return cached formatted guidelines
            3. If miss: Run RAG, format results, cache, return

        Args:
            query: Query text
            top_k: Number of documents to retrieve

        Returns:
            List of Document objects

        Note:
            This method returns Document objects for compatibility.
            The cache stores formatted guidelines text internally.
        """
        self.stats["total_queries"] += 1

        # Check cache if enabled
        if self.cache_enabled and self.cache:
            start_time = time.time()
            cached_guidelines = self.cache.get(query)
            cache_lookup_time = time.time() - start_time

            if cached_guidelines:
                # Cache hit
                self.stats["cache_hits"] += 1
                # Estimate time saved (typical RAG query takes ~1s)
                time_saved = 1.0 - cache_lookup_time
                self.stats["total_time_saved"] += time_saved

                logger.info(
                    f"[{self.agent_name}] Cache HIT: '{query[:50]}...' "
                    f"(saved ~{time_saved:.2f}s)"
                )

                # Return as Document for compatibility
                # (Actual formatted guidelines will be used in format_results)
                return self._cached_guidelines_to_documents(cached_guidelines)

            # Cache miss
            self.stats["cache_misses"] += 1
            logger.info(f"[{self.agent_name}] Cache MISS: '{query[:50]}...'")

        # Run RAG retrieval
        start_time = time.time()
        results = self.rag_service.retrieve(query, top_k=top_k)
        retrieval_time = time.time() - start_time

        logger.info(
            f"[{self.agent_name}] RAG retrieval: {len(results)} docs "
            f"in {retrieval_time:.2f}s"
        )

        # Cache the formatted results
        if self.cache_enabled and self.cache and results:
            formatted_guidelines = self.rag_service.format_results(results)
            self.cache.set(query, formatted_guidelines)

        return results

    def format_results(self, results: List[Document]) -> str:
        """
        Format retrieved documents as guidelines text.

        This delegates to the underlying RAG service.

        Args:
            results: List of retrieved documents

        Returns:
            Formatted guidelines string
        """
        return self.rag_service.format_results(results)

    def _cached_guidelines_to_documents(self, guidelines: str) -> List[Document]:
        """
        Convert cached guidelines text back to Document list.

        This is a compatibility shim since cached results are strings
        but retrieve() should return Document objects.

        Args:
            guidelines: Cached guidelines text

        Returns:
            Single Document containing the guidelines
        """
        return [
            Document(
                page_content=guidelines,
                metadata={"source": "semantic_cache", "agent": self.agent_name},
            )
        ]

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache hit/miss stats and time saved
        """
        hit_rate = 0.0
        if self.stats["total_queries"] > 0:
            hit_rate = (
                self.stats["cache_hits"] / self.stats["total_queries"]
            ) * 100

        return {
            **self.stats,
            "hit_rate_percent": hit_rate,
            "cache_enabled": self.cache_enabled,
            "agent_name": self.agent_name,
        }

    def print_stats(self) -> None:
        """Print cache statistics in human-readable format."""
        stats = self.get_stats()

        print(f"\n{'=' * 60}")
        print(f"Cache Statistics: {self.agent_name.upper()}")
        print(f"{'=' * 60}")
        print(f"Total Queries:    {stats['total_queries']}")
        print(f"Cache Hits:       {stats['cache_hits']}")
        print(f"Cache Misses:     {stats['cache_misses']}")
        print(f"Hit Rate:         {stats['hit_rate_percent']:.1f}%")
        print(f"Time Saved:       {stats['total_time_saved']:.2f}s")
        print(f"Cache Enabled:    {stats['cache_enabled']}")
        print(f"{'=' * 60}\n")

    def flush_cache(self) -> None:
        """Clear all cached entries."""
        if self.cache:
            self.cache.clear()
            logger.info(f"Cache cleared for {self.agent_name}")


def create_cached_rag_service(
    config: RAGConfig,
    agent_name: str,
    qdrant_client: Optional[QdrantClient] = None,
    cache_enabled: bool = True,
) -> CachedRAGService:
    """
    Factory function to create a cached RAG service.

    Args:
        config: RAG configuration
        agent_name: Agent name (used as cache namespace)
        qdrant_client: Optional Qdrant client
        cache_enabled: Whether to enable caching

    Returns:
        Configured CachedRAGService instance

    Example:
        >>> from app.rag.config import clarity_rag_config
        >>> service = create_cached_rag_service(
        ...     config=clarity_rag_config,
        ...     agent_name="clarity"
        ... )
        >>> results = service.retrieve("clear writing tips")
    """
    return CachedRAGService(
        config=config,
        agent_name=agent_name,
        qdrant_client=qdrant_client,
        cache_enabled=cache_enabled,
    )
