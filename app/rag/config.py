"""RAG configuration for different agents."""

from typing import Literal
from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    """Configuration for document embedding (one-time operation)."""

    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model to use",
    )
    chunking_strategy: Literal["recursive", "semantic"] = Field(
        default="recursive",
        description="Text chunking strategy: 'recursive' or 'semantic'",
    )
    chunk_size: int = Field(
        default=1000, description="Size of document chunks in characters (for recursive)"
    )
    chunk_overlap: int = Field(
        default=200, description="Overlap between chunks in characters (for recursive)"
    )
    breakpoint_threshold_type: Literal["percentile", "standard_deviation", "interquartile"] = Field(
        default="percentile",
        description="Breakpoint threshold type for semantic chunking",
    )
    breakpoint_threshold_amount: float = Field(
        default=92.0,
        description="Breakpoint threshold amount for semantic chunking (e.g., 92 for 92nd percentile)",
    )
    use_cache: bool = Field(
        default=True, description="Whether to use cached embeddings"
    )


class RetrievalConfig(BaseModel):
    """Configuration for retrieval strategy (runtime, swappable)."""

    retriever_type: Literal["naive"] = Field(
        default="naive", description="Type of retriever to use"
    )
    top_k: int = Field(default=3, description="Number of documents to retrieve")
    metadata_filter: dict[str, str] = Field(
        default_factory=dict, description="Metadata filters for retrieval"
    )


class RAGConfig(BaseModel):
    """Complete RAG configuration for an agent."""

    collection_name: str = Field(description="Qdrant collection name")
    documents_path: str = Field(description="Path to source documents")
    embedding_config: EmbeddingConfig = Field(
        default_factory=EmbeddingConfig, description="Embedding configuration"
    )
    retrieval_config: RetrievalConfig = Field(
        default_factory=RetrievalConfig, description="Retrieval configuration"
    )


# Clarity Agent RAG Configuration
clarity_rag_config = RAGConfig(
    collection_name="clarity_guidelines",
    documents_path="app/resources/clarity_docs",
    embedding_config=EmbeddingConfig(
        embedding_model="text-embedding-3-small",
        chunking_strategy="recursive",  # List-based guidelines work better with recursive
        chunk_size=800,
        chunk_overlap=150,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=92.0,
        use_cache=True,
    ),
    retrieval_config=RetrievalConfig(
        retriever_type="naive",
        top_k=3,
        # No metadata filter needed - each agent has its own collection
    ),
)

# Rigor Agent RAG Configuration
rigor_rag_config = RAGConfig(
    collection_name="rigor_guidelines",
    documents_path="app/resources/rigor_docs",
    embedding_config=EmbeddingConfig(
        embedding_model="text-embedding-3-small",
        chunking_strategy="semantic",  # Paragraphs/equations benefit from semantic chunking
        chunk_size=1000,  # Fallback for recursive mode
        chunk_overlap=200,  # Fallback for recursive mode
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=70.0,  # Lower threshold for larger chunks with more context
        use_cache=True,
    ),
    retrieval_config=RetrievalConfig(
        retriever_type="naive",
        top_k=3,
        # No metadata filter needed - each agent has its own collection
    ),
)
