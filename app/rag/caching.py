"""
Simplified embedding caching using LangChain's CacheBackedEmbeddings.

This module provides a clean interface for creating cached embeddings
using LangChain's built-in caching mechanisms with local file storage.
"""

from langchain.embeddings import CacheBackedEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.storage import LocalFileStore


def create_cached_embeddings(
    model: str = "text-embedding-3-small",
    cache_dir: str = "app/embedding_cache",
    namespace: str = "default",
) -> CacheBackedEmbeddings:
    """
    Create embeddings with local file-based caching.

    This uses LangChain's CacheBackedEmbeddings to automatically cache
    embeddings in a local file store, avoiding redundant API calls.

    Args:
        model: OpenAI embedding model name
        cache_dir: Base directory for cache storage
        namespace: Cache namespace for separation (e.g., "clarity", "rigor")

    Returns:
        CacheBackedEmbeddings instance with caching enabled

    Example:
        >>> embeddings = create_cached_embeddings(namespace="clarity")
        >>> vectors = embeddings.embed_documents(["text1", "text2"])
        >>> # Second call uses cache - no API call!
        >>> vectors = embeddings.embed_documents(["text1", "text2"])
    """
    # Create underlying OpenAI embeddings
    underlying_embeddings = OpenAIEmbeddings(model=model)

    # Create local file store for caching (binary storage)
    store = LocalFileStore(f"{cache_dir}/{namespace}")

    # Wrap with caching layer
    cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings=underlying_embeddings,
        document_embedding_cache=store,
        namespace=namespace,
    )

    return cached_embeddings
