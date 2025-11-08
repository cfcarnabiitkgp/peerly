"""RAG (Retrieval-Augmented Generation) module for document retrieval."""

from app.rag.base import Document, BaseRetriever
from app.rag.rag_service import RAGService
from app.rag.caching import create_cached_embeddings

__all__ = [
    "Document",
    "BaseRetriever",
    "RAGService",
    "create_cached_embeddings",
]
