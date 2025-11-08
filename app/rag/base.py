"""Base classes and interfaces for RAG components using LangChain."""

from abc import ABC, abstractmethod
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

# Re-export LangChain's Document for convenience
__all__ = ["Document", "BaseRetriever"]

# Note: We now use LangChain's built-in types:
# - Document: langchain_core.documents.Document
# - BaseRetriever: langchain_core.retrievers.BaseRetriever
#
# This simplifies our code and ensures compatibility with the
# broader LangChain ecosystem.
