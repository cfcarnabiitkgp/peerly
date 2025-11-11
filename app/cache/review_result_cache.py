"""
Review Result Cache with semantic similarity and exact hash verification.

This module provides caching for complete review results (analysis of LaTeX documents).
Unlike the RAG semantic cache which caches guidelines retrieval, this caches the
expensive LLM analysis results.

Architecture:
    - Semantic search finds similar documents (>98% similarity)
    - Exact hash verification prevents false positives
    - Stores complete ReviewResponse in Qdrant
    - Separate collection from RAG and RAG semantic cache

Benefits:
    - Fast semantic search (Qdrant HNSW index)
    - No false positives (hash verification)
    - Persistent across restarts
    - Handles documents of any length (fingerprint approach)
"""

import time
import hashlib
import json
import logging
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

logger = logging.getLogger(__name__)


class ReviewResultCache:
    """
    Semantic cache for complete review results with exact hash verification.

    This cache stores the full analysis results (ReviewResponse) for LaTeX documents.
    It uses a hybrid approach:
    1. Creates a semantic "fingerprint" from the first N characters
    2. Searches for semantically similar documents in Qdrant
    3. Verifies exact hash match to prevent false positives

    Why Hybrid?
    - Pure semantic: Risk of false positives (similar but different papers)
    - Pure hash: Any tiny change invalidates cache (too strict)
    - Hybrid: Fast semantic search + exact verification = best of both

    Attributes:
        collection_name (str): Qdrant collection name for cache
        qdrant_client (QdrantClient): Qdrant client instance
        embedding_model (TextEmbedding): FastEmbed model for fingerprints
        dimension (int): Embedding dimension (384 for default model)
        similarity_threshold (float): Minimum similarity for candidates (0.0-1.0)
        max_fingerprint_length (int): Max chars to use for fingerprint
    """

    def __init__(
        self,
        qdrant_client: Optional[QdrantClient] = None,
        similarity_threshold: float = 0.98,
        max_fingerprint_length: int = 2000,
        embedding_model_name: str = "BAAI/bge-small-en-v1.5",
        max_candidates: int = 5,
        strict_matching: bool = True
    ):
        """
        Initialize review result cache.

        Args:
            qdrant_client: Qdrant client (creates default if not provided)
            similarity_threshold: Similarity threshold for candidates (0.0-1.0)
                                 Default 0.98 = 98%+ similar documents
                                 Higher = more strict (fewer false candidates)
            max_fingerprint_length: Max characters for document fingerprint
                                   Default 2000 chars (~500 tokens)
                                   Typically includes preamble + start of content
            embedding_model_name: FastEmbed model name
                                 Default: BAAI/bge-small-en-v1.5 (384-dim)
            max_candidates: Max similar documents to check for hash match
            strict_matching: If True, require both semantic+hash match (strict)
                           If False, use semantic similarity only (lenient)
                           Default: True (strict mode)
        """
        self.collection_name = "review_results_cache"
        self.similarity_threshold = similarity_threshold
        self.max_fingerprint_length = max_fingerprint_length
        self.max_candidates = max_candidates
        self.strict_matching = strict_matching

        # Initialize Qdrant client
        if qdrant_client is None:
            from app.config.settings import settings
            self.qdrant_client = QdrantClient(url=settings.qdrant_url)
        else:
            self.qdrant_client = qdrant_client

        # Initialize FastEmbed model (lightweight, fast local embeddings)
        logger.info(f"Initializing FastEmbed model for review cache: {embedding_model_name}")
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
            "false_candidates": 0  # Semantic match but hash mismatch
        }

        matching_mode = "strict (semantic+hash)" if strict_matching else "lenient (semantic only)"
        logger.info(
            f"ReviewResultCache initialized: {self.collection_name} "
            f"(mode={matching_mode}, threshold={similarity_threshold}, fingerprint_len={max_fingerprint_length})"
        )

    def _ensure_collection_exists(self):
        """Create cache collection if it doesn't exist."""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)

            if not collection_exists:
                logger.info(f"Creating review cache collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"✓ Review cache collection created: {self.collection_name}")
            else:
                logger.info(f"Using existing review cache collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Error creating review cache collection: {e}")
            raise

    def _create_fingerprint(self, content: str) -> str:
        """
        Create a semantic fingerprint from the document.

        Takes the first N characters which typically include:
        - Document class and preamble
        - Package imports
        - Title, author, abstract
        - Beginning of content

        This is usually the most stable part and captures document identity.
        Small edits in the body won't affect the fingerprint much.

        Args:
            content: Full LaTeX content

        Returns:
            Fingerprint string (truncated content)
        """
        return content[:self.max_fingerprint_length]

    def _embed_fingerprint(self, fingerprint: str) -> list:
        """
        Generate embedding for a document fingerprint.

        Args:
            fingerprint: Fingerprint text

        Returns:
            Embedding vector as list
        """
        embeddings = list(self.embedding_model.embed([fingerprint]))
        return embeddings[0].tolist()

    def _create_full_hash(self, content: str, agents: List[str]) -> str:
        """
        Create exact hash of content + agents for verification.

        This ensures that even if two documents are semantically similar,
        we only return cached results if they are EXACTLY the same.

        Args:
            content: Full LaTeX content
            agents: List of agents used (e.g., ["clarity", "rigor"])

        Returns:
            SHA256 hash string
        """
        # Sort agents to ensure consistent hash regardless of order
        agents_str = ",".join(sorted(agents))
        combined = content + "|" + agents_str
        return hashlib.sha256(combined.encode()).hexdigest()

    def get(
        self,
        content: str,
        agents: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached review result using semantic similarity + hash verification.

        Process:
        1. Create semantic fingerprint from first N chars
        2. Search Qdrant for semantically similar documents (>threshold)
        3. For each candidate, verify exact hash match
        4. Return cached result if hash matches, else None

        This hybrid approach provides:
        - Fast candidate finding (semantic search)
        - No false positives (exact hash verification)

        Args:
            content: Full LaTeX content
            agents: List of agents used (e.g., ["clarity", "rigor"])

        Returns:
            Cached result dict (ReviewResponse) or None if no match found
        """
        self.stats["total_queries"] += 1
        start_time = time.time()

        try:
            # Step 1: Create fingerprint and embeddings
            fingerprint = self._create_fingerprint(content)
            fingerprint_embedding = self._embed_fingerprint(fingerprint)
            full_hash = self._create_full_hash(content, agents)

            # Step 2: Search for semantically similar documents
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=fingerprint_embedding,
                limit=self.max_candidates,
                score_threshold=self.similarity_threshold
            )

            if not search_results:
                self.stats["cache_misses"] += 1
                logger.info(
                    f"Cache MISS: No similar documents found "
                    f"(threshold={self.similarity_threshold})"
                )
                return None

            # Step 3: Check matching mode
            if self.strict_matching:
                # STRICT MODE: Verify exact hash match among candidates
                for idx, result in enumerate(search_results):
                    cached_hash = result.payload.get("full_hash")
                    cached_agents = result.payload.get("agents", [])
                    similarity = result.score

                    # Check exact match on hash and agents
                    if cached_hash == full_hash and set(cached_agents) == set(agents):
                        # Cache HIT!
                        self.stats["cache_hits"] += 1

                        # Estimate time saved (typical review takes 10-15 seconds)
                        cache_lookup_time = time.time() - start_time
                        time_saved = 12.0 - cache_lookup_time  # Average 12s review time
                        self.stats["total_time_saved"] += time_saved

                        logger.info(
                            f"Cache HIT (strict): similarity={similarity:.4f}, "
                            f"exact_hash_match=True, "
                            f"candidate_rank={idx+1}/{len(search_results)}, "
                            f"saved ~{time_saved:.1f}s"
                        )

                        # Return cached result
                        return json.loads(result.payload.get("result"))

                # Semantic matches found but no exact hash match
                self.stats["cache_misses"] += 1
                self.stats["false_candidates"] += len(search_results)

                logger.info(
                    f"Cache MISS (strict): Found {len(search_results)} similar documents "
                    f"(best similarity={search_results[0].score:.4f}) "
                    f"but no exact hash match"
                )
                return None

            else:
                # LENIENT MODE: Use semantic similarity only (no hash verification)
                # Take the best match that has the same agents
                for idx, result in enumerate(search_results):
                    cached_agents = result.payload.get("agents", [])
                    similarity = result.score

                    # Only check agents match (no hash check)
                    if set(cached_agents) == set(agents):
                        # Cache HIT based on semantic similarity!
                        self.stats["cache_hits"] += 1

                        # Estimate time saved
                        cache_lookup_time = time.time() - start_time
                        time_saved = 12.0 - cache_lookup_time
                        self.stats["total_time_saved"] += time_saved

                        logger.info(
                            f"Cache HIT (lenient): similarity={similarity:.4f}, "
                            f"semantic_only=True, "
                            f"candidate_rank={idx+1}/{len(search_results)}, "
                            f"saved ~{time_saved:.1f}s"
                        )

                        # Return cached result
                        return json.loads(result.payload.get("result"))

                # No match with same agents
                self.stats["cache_misses"] += 1
                logger.info(
                    f"Cache MISS (lenient): Found {len(search_results)} similar documents "
                    f"but none with matching agents"
                )
                return None

        except Exception as e:
            logger.error(f"Error retrieving from review cache: {e}")
            return None

    def set(
        self,
        content: str,
        agents: List[str],
        result: Dict[str, Any]
    ) -> None:
        """
        Store review result in cache.

        Args:
            content: Full LaTeX content
            agents: List of agents used (e.g., ["clarity", "rigor"])
            result: Review result to cache (ReviewResponse dict)
        """
        try:
            # Create fingerprint, embedding, and hash
            fingerprint = self._create_fingerprint(content)
            fingerprint_embedding = self._embed_fingerprint(fingerprint)
            full_hash = self._create_full_hash(content, agents)

            # Generate point ID from hash (deterministic)
            point_id = int(full_hash[:16], 16) % (10**9)

            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=fingerprint_embedding,
                        payload={
                            "full_hash": full_hash,
                            "agents": agents,
                            "result": json.dumps(result),
                            "fingerprint_length": len(fingerprint),
                            "content_length": len(content),
                            "timestamp": time.time(),
                        }
                    )
                ]
            )

            logger.info(
                f"Cached review result: hash={full_hash[:8]}..., "
                f"agents={agents}, content_len={len(content)}"
            )

        except Exception as e:
            logger.error(f"Error storing in review cache: {e}")

    def clear(self) -> None:
        """Clear all cached review results (deletes and recreates collection)."""
        try:
            logger.info(f"Clearing review cache collection: {self.collection_name}")
            self.qdrant_client.delete_collection(self.collection_name)
            self._ensure_collection_exists()

            # Reset stats
            self.stats = {
                "total_queries": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "total_time_saved": 0.0,
                "false_candidates": 0
            }

            logger.info(f"✓ Review cache cleared: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing review cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache hit/miss stats, time saved, etc.
        """
        hit_rate = 0.0
        if self.stats["total_queries"] > 0:
            hit_rate = (self.stats["cache_hits"] / self.stats["total_queries"]) * 100

        matching_mode = "strict (semantic+hash)" if self.strict_matching else "lenient (semantic only)"
        return {
            **self.stats,
            "hit_rate_percent": hit_rate,
            "collection_name": self.collection_name,
            "matching_mode": matching_mode,
            "strict_matching": self.strict_matching,
            "similarity_threshold": self.similarity_threshold,
            "max_fingerprint_length": self.max_fingerprint_length
        }

    def print_stats(self) -> None:
        """Print cache statistics in human-readable format."""
        stats = self.get_stats()

        print(f"\n{'=' * 60}")
        print(f"Review Result Cache Statistics")
        print(f"{'=' * 60}")
        print(f"Matching Mode:       {stats['matching_mode']}")
        print(f"Total Queries:       {stats['total_queries']}")
        print(f"Cache Hits:          {stats['cache_hits']}")
        print(f"Cache Misses:        {stats['cache_misses']}")
        print(f"Hit Rate:            {stats['hit_rate_percent']:.1f}%")
        print(f"Time Saved:          {stats['total_time_saved']:.1f}s")
        print(f"False Candidates:    {stats['false_candidates']}")
        print(f"Threshold:           {stats['similarity_threshold']}")
        print(f"Fingerprint Length:  {stats['max_fingerprint_length']} chars")
        print(f"{'=' * 60}\n")


def create_review_result_cache(
    qdrant_client: Optional[QdrantClient] = None,
    similarity_threshold: float = 0.98,
    max_fingerprint_length: int = 2000,
    strict_matching: bool = True
) -> ReviewResultCache:
    """
    Factory function to create a review result cache.

    Args:
        qdrant_client: Optional Qdrant client
        similarity_threshold: Similarity threshold for candidates (0.0-1.0)
                             Default 0.98 = 98%+ similar documents
        max_fingerprint_length: Max characters for document fingerprint
        strict_matching: If True, require both semantic+hash match (strict)
                        If False, use semantic similarity only (lenient)
                        Default: True (strict mode)

    Returns:
        Configured ReviewResultCache instance

    Example:
        >>> # Strict mode (default): semantic + hash verification
        >>> cache = create_review_result_cache(strict_matching=True)
        >>>
        >>> # Lenient mode: semantic similarity only
        >>> cache = create_review_result_cache(strict_matching=False)
        >>>
        >>> result = cache.get(latex_content, ["clarity", "rigor"])
        >>> if not result:
        ...     result = expensive_llm_analysis()
        ...     cache.set(latex_content, ["clarity", "rigor"], result)
    """
    return ReviewResultCache(
        qdrant_client=qdrant_client,
        similarity_threshold=similarity_threshold,
        max_fingerprint_length=max_fingerprint_length,
        strict_matching=strict_matching
    )
