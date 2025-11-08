"""RAG nodes for retrieving writing guidelines during review workflow."""

from typing import List
from qdrant_client import QdrantClient

from app.rag.config import clarity_rag_config, rigor_rag_config
from app.rag.cached_rag_service import create_cached_rag_service
from app.models.schemas import Section


class ClarityRAGNode:
    """
    Dedicated RAG node for Clarity Agent.
    Retrieves relevant clarity-focused writing guidelines with semantic caching.

    Uses CachedRAGService which provides:
    - Semantic query-level caching (FastEmbed + Qdrant)
    - Separate cache namespace for clarity agent
    - Automatic cache hit/miss tracking
    """

    def __init__(self, qdrant_client: QdrantClient | None = None, cache_enabled: bool | None = None):
        """
        Initialize the Clarity RAG node with semantic caching.

        Args:
            qdrant_client: Optional Qdrant client (creates default if not provided)
            cache_enabled: Whether to enable semantic caching (defaults to settings.use_semantic_cache)
        """
        from app.config.settings import settings

        if cache_enabled is None:
            cache_enabled = settings.use_semantic_cache

        self.rag_service = create_cached_rag_service(
            config=clarity_rag_config,
            agent_name="clarity",
            qdrant_client=qdrant_client,
            cache_enabled=cache_enabled,
        )

    def __call__(self, state: dict) -> dict:
        """
        Execute RAG retrieval for clarity guidelines.

        Args:
            state: Current workflow state

        Returns:
            Dictionary with retrieved clarity guidelines
        """
        try:
            sections = state.get("sections_for_clarity", [])

            if not sections:
                return {"clarity_guidelines": ""}

            # Formulate query based on section types and content
            query = self._formulate_query(sections)

            # Retrieve relevant guidelines using LangChain retriever
            results = self.rag_service.retrieve(query, top_k=3)

            # Format results for agent consumption
            guidelines = self.rag_service.format_results(results)

            return {"clarity_guidelines": guidelines}

        except Exception as e:
            print(f"Error in Clarity RAG Node: {str(e)}")
            # Return empty guidelines on error, don't block workflow
            return {"clarity_guidelines": ""}

    def _formulate_query(self, sections: List[Section]) -> str:
        """
        Formulate RAG query based on sections to be reviewed.

        Args:
            sections: Sections to be reviewed

        Returns:
            Query string for RAG retrieval
        """
        # Base query for clarity guidelines
        query_parts = ["writing clarity guidelines mathematical papers"]

        # Add section type context
        section_types = set(s.section_type.lower() for s in sections)
        if section_types:
            query_parts.append(f"{', '.join(section_types)}")

        # Look for specific clarity issues to focus on
        content_sample = " ".join(s.content[:200] for s in sections[:2])

        # Add focus based on content characteristics
        if any(len(s.content.split()) > 100 for s in sections):
            query_parts.append("simplifying complex sentences")

        if "theorem" in content_sample.lower() or "lemma" in content_sample.lower():
            query_parts.append("clear mathematical statements")

        return " ".join(query_parts)


class RigorRAGNode:
    """
    Dedicated RAG node for Rigor Agent.
    Retrieves relevant rigor-focused validation guidelines with semantic caching.

    Uses CachedRAGService which provides:
    - Semantic query-level caching (FastEmbed + Qdrant)
    - Separate cache namespace for rigor agent
    - Automatic cache hit/miss tracking
    """

    def __init__(self, qdrant_client: QdrantClient | None = None, cache_enabled: bool | None = None):
        """
        Initialize the Rigor RAG node with semantic caching.

        Args:
            qdrant_client: Optional Qdrant client (creates default if not provided)
            cache_enabled: Whether to enable semantic caching (defaults to settings.use_semantic_cache)
        """
        from app.config.settings import settings

        if cache_enabled is None:
            cache_enabled = settings.use_semantic_cache

        self.rag_service = create_cached_rag_service(
            config=rigor_rag_config,
            agent_name="rigor",
            qdrant_client=qdrant_client,
            cache_enabled=cache_enabled,
        )

    def __call__(self, state: dict) -> dict:
        """
        Execute RAG retrieval for rigor guidelines.

        Args:
            state: Current workflow state

        Returns:
            Dictionary with retrieved rigor guidelines
        """
        try:
            sections = state.get("sections_for_rigor", [])

            if not sections:
                return {"rigor_guidelines": ""}

            # Formulate query based on section types and content
            query = self._formulate_query(sections)

            # Retrieve relevant guidelines using LangChain retriever
            results = self.rag_service.retrieve(query, top_k=3)

            # Format results for agent consumption
            guidelines = self.rag_service.format_results(results)

            return {"rigor_guidelines": guidelines}

        except Exception as e:
            print(f"Error in Rigor RAG Node: {str(e)}")
            # Return empty guidelines on error, don't block workflow
            return {"rigor_guidelines": ""}

    def _formulate_query(self, sections: List[Section]) -> str:
        """
        Formulate RAG query based on sections to be reviewed.

        Args:
            sections: Sections to be reviewed

        Returns:
            Query string for RAG retrieval
        """
        # Base query for rigor guidelines
        query_parts = ["mathematical rigor validation proof writing"]

        # Add section type context
        section_types = set(s.section_type.lower() for s in sections)
        if section_types:
            query_parts.append(f"{', '.join(section_types)}")

        # Look for specific rigor concerns
        content_sample = " ".join(s.content[:200] for s in sections[:2])

        # Add focus based on content characteristics
        if "proof" in content_sample.lower():
            query_parts.append("proof structure validation")

        if "experiment" in content_sample.lower() or "result" in content_sample.lower():
            query_parts.append("experimental validation statistical methods")

        if "theorem" in content_sample.lower() or "lemma" in content_sample.lower():
            query_parts.append("assumptions definitions mathematical statements")

        return " ".join(query_parts)
