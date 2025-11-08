"""Main RAG service using LangChain components."""

from typing import Optional, List

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank

from app.rag.config import RAGConfig
from app.rag.caching import create_cached_embeddings


class RAGService:
    """
    Simplified RAG service using LangChain patterns.

    Provides high-level interface for document retrieval with support
    for multiple retrieval strategies (naive, hybrid, rerank, etc.).
    """

    def __init__(
        self,
        config: RAGConfig,
        qdrant_client: Optional[QdrantClient] = None,
    ):
        """
        Initialize the RAG service.

        Args:
            config: RAG configuration
            qdrant_client: Optional Qdrant client (creates default if not provided)
        """
        self.config = config
        if qdrant_client is None:
            from app.config.settings import settings
            self.qdrant_client = QdrantClient(url=settings.qdrant_url)
        else:
            self.qdrant_client = qdrant_client

        # Create cached embeddings using LangChain
        self.embeddings = create_cached_embeddings(
            model=config.embedding_config.embedding_model,
            namespace=config.collection_name,  # Separate cache per collection
        )

        # Create Qdrant vector store using LangChain
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=config.collection_name,
            embedding=self.embeddings,
        )

        # Create retriever based on strategy
        self.retriever = self._create_retriever()

    def _create_retriever(self) -> BaseRetriever:
        """
        Create retriever based on configuration strategy.

        Returns:
            Configured LangChain retriever

        Raises:
            ValueError: If retriever type is not supported
        """
        retriever_type = self.config.retrieval_config.retriever_type
        top_k = self.config.retrieval_config.top_k
        metadata_filter = self.config.retrieval_config.metadata_filter

        # Create base retriever with metadata filtering
        search_kwargs = {"k": top_k}
        if metadata_filter:
            search_kwargs["filter"] = metadata_filter

        base_retriever = self.vector_store.as_retriever(search_kwargs=search_kwargs)

        # Apply retrieval strategy
        if retriever_type == "naive":
            return base_retriever

        elif retriever_type == "rerank":
            # Contextual compression with Cohere reranking
            compressor = CohereRerank(top_n=top_k)
            return ContextualCompressionRetriever(
                base_compressor=compressor, base_retriever=base_retriever
            )

        # Add more strategies here as needed
        # elif retriever_type == "hybrid":
        #     return create_hybrid_retriever(...)
        # elif retriever_type == "multi_query":
        #     return MultiQueryRetriever(...)

        raise ValueError(f"Unsupported retriever type: {retriever_type}")

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Document]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: The search query
            top_k: Number of results to return (uses config default if not provided)

        Returns:
            List of LangChain Document objects
        """
        if top_k is not None:
            # Temporarily override top_k
            original_k = self.retriever.search_kwargs.get("k")
            self.retriever.search_kwargs["k"] = top_k
            results = self.retriever.invoke(query)
            self.retriever.search_kwargs["k"] = original_k
            return results

        return self.retriever.invoke(query)

    def retrieve_with_scores(self, query: str, top_k: Optional[int] = None) -> List[tuple[Document, float]]:
        """
        Retrieve relevant documents with similarity scores.

        Args:
            query: The search query
            top_k: Number of results to return (uses config default if not provided)

        Returns:
            List of tuples (Document, score) where score is cosine similarity (0-1, higher is better)
        """
        k = top_k if top_k is not None else self.config.retrieval_config.top_k

        # Use vector store's similarity_search_with_score for scores
        results = self.vector_store.similarity_search_with_score(query, k=k)

        return results

    def format_results(self, results: List[Document]) -> str:
        """
        Format retrieval results as a readable string for agent consumption.

        Args:
            results: List of LangChain documents

        Returns:
            Formatted string with results
        """
        if not results:
            return "No relevant guidelines found."

        formatted = "Retrieved Guidelines:\n\n"
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "Unknown")
            # Check if document has score (some retrievers add it)
            score = doc.metadata.get("score", "N/A")
            if score != "N/A":
                formatted += f"{i}. [Score: {score:.3f}] {source}\n"
            else:
                formatted += f"{i}. {source}\n"
            formatted += f"{doc.page_content}\n\n"

        return formatted
