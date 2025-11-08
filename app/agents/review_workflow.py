"""
LangGraph workflow for orchestrating multi-agent peer review.
"""
import asyncio
from typing import List, TypedDict, Annotated, TYPE_CHECKING
from langgraph.graph import StateGraph, END
from app.models.schemas import Section, SectionSuggestions, SuggestionGroup
from app.agents.clarity_agent import ClarityAgent
from app.agents.rigor_agent import RigorAgent
from app.agents.orchestrator_agent import orchestrator

# Import RAG nodes only for type checking to avoid loading dependencies
if TYPE_CHECKING:
    from app.agents.rag_nodes import ClarityRAGNode, RigorRAGNode


def keep_first_value(left, right):
    """Reducer that keeps the first (existing) non-empty value for concurrent updates."""
    # If left is empty list or None, use right
    # Otherwise keep left (for when parallel nodes return the same data)
    if not left:
        return right
    return left


class ReviewState(TypedDict):
    """State shared across the review workflow."""
    sections: List[Section]
    sections_for_clarity: Annotated[List[Section], keep_first_value]
    sections_for_rigor: Annotated[List[Section], keep_first_value]
    clarity_guidelines: str
    rigor_guidelines: str
    clarity_suggestions: List[SectionSuggestions]
    rigor_suggestions: List[SectionSuggestions]
    final_suggestions: List[SectionSuggestions]
    error: str | None


class ReviewWorkflow:
    """
    Multi-agent workflow for peer reviewing technical manuscripts.
    Uses LangGraph StateGraph for orchestration.
    """

    def __init__(self, use_rag: bool = True):
        """
        Initialize the review workflow with agents.

        Args:
            use_rag: Whether to use RAG for retrieving guidelines (default: True)
                     Set to False to run without Qdrant/embeddings
        """
        self.use_rag = use_rag
        self.clarity_agent = ClarityAgent()
        self.rigor_agent = RigorAgent()

        if use_rag:
            # Import RAG nodes only when needed to avoid loading dependencies
            from app.agents.rag_nodes import ClarityRAGNode, RigorRAGNode
            self.clarity_rag_node = ClarityRAGNode()
            self.rigor_rag_node = RigorRAGNode()

        # Note: Workflow will be built dynamically based on agent selection

    def _build_workflow(self, agents: List[str]) -> StateGraph:
        """
        Build the LangGraph workflow based on selected agents.

        Args:
            agents: List of agents to run (e.g., ['clarity', 'rigor'])

        Returns:
            Compiled StateGraph workflow
        """
        # Create state graph
        workflow = StateGraph(ReviewState)

        # Always add orchestrator routing node
        workflow.add_node("orchestrator_route", self._orchestrator_route_node)
        workflow.set_entry_point("orchestrator_route")

        # Track which agents are active
        run_clarity = "clarity" in agents
        run_rigor = "rigor" in agents

        # Add nodes for selected agents only
        if run_clarity:
            if self.use_rag:
                workflow.add_node("clarity_rag", self.clarity_rag_node)
            workflow.add_node("clarity_review", self._clarity_review_node)

        if run_rigor:
            if self.use_rag:
                workflow.add_node("rigor_rag", self.rigor_rag_node)
            workflow.add_node("rigor_review", self._rigor_review_node)

        # Always add orchestrator finalize node
        workflow.add_node("orchestrator_finalize", self._orchestrator_finalize_node)

        # Define edges based on selected agents
        if run_clarity:
            if self.use_rag:
                # With RAG: orchestrator → clarity RAG → clarity review → finalize
                workflow.add_edge("orchestrator_route", "clarity_rag")
                workflow.add_edge("clarity_rag", "clarity_review")
            else:
                # Without RAG: orchestrator → clarity review → finalize
                workflow.add_edge("orchestrator_route", "clarity_review")
            workflow.add_edge("clarity_review", "orchestrator_finalize")

        if run_rigor:
            if self.use_rag:
                # With RAG: orchestrator → rigor RAG → rigor review → finalize
                workflow.add_edge("orchestrator_route", "rigor_rag")
                workflow.add_edge("rigor_rag", "rigor_review")
            else:
                # Without RAG: orchestrator → rigor review → finalize
                workflow.add_edge("orchestrator_route", "rigor_review")
            workflow.add_edge("rigor_review", "orchestrator_finalize")

        # If no agents selected, go directly to finalize
        if not run_clarity and not run_rigor:
            workflow.add_edge("orchestrator_route", "orchestrator_finalize")

        # Always end at orchestrator finalize
        workflow.add_edge("orchestrator_finalize", END)

        return workflow.compile()

    async def _orchestrator_route_node(self, state: ReviewState) -> dict:
        """
        Orchestrator node that filters and routes sections to appropriate agents.

        Args:
            state: Current workflow state

        Returns:
            Dictionary with filtered sections for each agent
        """
        sections = state["sections"]

        # All sections go to clarity review
        sections_for_clarity = sections

        # Only methodological/mathematical sections go to rigor review
        # Section types that need rigor: methodology, experiments, results, analysis
        # Also check for mathematical content indicators
        rigor_section_types = {"methodology", "experiments", "results", "analysis", "methods"}

        sections_for_rigor = [
            section for section in sections
            if (
                section.section_type.lower() in rigor_section_types
                or self._contains_mathematical_content(section.content)
            )
        ]

        return {
            "sections_for_clarity": sections_for_clarity,
            "sections_for_rigor": sections_for_rigor
        }

    def _contains_mathematical_content(self, content: str) -> bool:
        """
        Check if content contains mathematical indicators.

        Args:
            content: Section content to check

        Returns:
            True if content contains mathematical elements
        """
        math_indicators = [
            "\\begin{equation}",
            "\\begin{align}",
            "\\begin{theorem}",
            "\\begin{proof}",
            "\\begin{lemma}",
            "\\begin{proposition}",
            "theorem",
            "lemma",
            "proof",
            "proposition",
            "corollary"
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in math_indicators)

    async def _clarity_review_node(self, state: ReviewState) -> dict:
        """
        Node for clarity agent review.

        Args:
            state: Current workflow state

        Returns:
            Dictionary with clarity suggestions (partial state update)
        """
        try:
            clarity_suggestions = []

            # Review only the sections routed by orchestrator
            sections_to_review = state.get("sections_for_clarity", [])

            # Get retrieved guidelines from RAG
            guidelines = state.get("clarity_guidelines", "")

            # Review all sections in parallel using asyncio.gather
            review_tasks = [
                self.clarity_agent.review_section(section, guidelines)
                for section in sections_to_review
            ]
            review_results = await asyncio.gather(*review_tasks)

            # Build suggestions from results
            for section, suggestions in zip(sections_to_review, review_results):
                if suggestions:
                    clarity_suggestions.append(SectionSuggestions(
                        section=section.title,
                        line=section.line_start,
                        section_type=section.section_type,
                        suggestions=[SuggestionGroup(
                            type=self.clarity_agent.suggestion_type,
                            count=len(suggestions),
                            items=suggestions
                        )]
                    ))

            return {"clarity_suggestions": clarity_suggestions}

        except Exception as e:
            return {"error": f"Clarity review failed: {str(e)}"}

    async def _rigor_review_node(self, state: ReviewState) -> dict:
        """
        Node for rigor agent review.

        Args:
            state: Current workflow state

        Returns:
            Dictionary with rigor suggestions (partial state update)
        """
        try:
            rigor_suggestions = []

            # Review only the sections routed by orchestrator
            sections_to_review = state.get("sections_for_rigor", [])

            # Get retrieved guidelines from RAG
            guidelines = state.get("rigor_guidelines", "")

            # Review all sections in parallel using asyncio.gather
            review_tasks = [
                self.rigor_agent.review_section(section, guidelines)
                for section in sections_to_review
            ]
            review_results = await asyncio.gather(*review_tasks)

            # Build suggestions from results
            for section, suggestions in zip(sections_to_review, review_results):
                if suggestions:
                    rigor_suggestions.append(SectionSuggestions(
                        section=section.title,
                        line=section.line_start,
                        section_type=section.section_type,
                        suggestions=[SuggestionGroup(
                            type=self.rigor_agent.suggestion_type,
                            count=len(suggestions),
                            items=suggestions
                        )]
                    ))

            return {"rigor_suggestions": rigor_suggestions}

        except Exception as e:
            return {"error": f"Rigor review failed: {str(e)}"}

    async def _orchestrator_finalize_node(self, state: ReviewState) -> dict:
        """
        Orchestrator finalize node that validates, deduplicates, and prioritizes suggestions.

        Args:
            state: Current workflow state

        Returns:
            Dictionary with final validated suggestions
        """
        try:
            # Get suggestions from both agents
            clarity_suggestions = state.get("clarity_suggestions", [])
            rigor_suggestions = state.get("rigor_suggestions", [])

            # Combine suggestions from all agents by section
            combined_suggestions = self._merge_suggestions(
                clarity_suggestions,
                rigor_suggestions
            )

            # Validate and prioritize using orchestrator agent
            final_suggestions = await orchestrator.validate_and_prioritize(
                combined_suggestions
            )

            return {"final_suggestions": final_suggestions}

        except Exception as e:
            return {"error": f"Orchestration failed: {str(e)}"}

    def _merge_suggestions(
        self,
        clarity_suggs: List[SectionSuggestions],
        rigor_suggs: List[SectionSuggestions]
    ) -> List[SectionSuggestions]:
        """
        Merge suggestions from different agents by section.

        Args:
            clarity_suggs: Clarity suggestions
            rigor_suggs: Rigor suggestions

        Returns:
            Merged suggestions
        """
        # Create a dictionary to merge by section
        section_map = {}

        # Add clarity suggestions
        for sugg in clarity_suggs:
            section_map[sugg.section] = sugg

        # Merge rigor suggestions
        for sugg in rigor_suggs:
            if sugg.section in section_map:
                # Extend existing suggestions
                section_map[sugg.section].suggestions.extend(sugg.suggestions)
            else:
                section_map[sugg.section] = sugg

        return list(section_map.values())

    async def review(
        self,
        sections: List[Section],
        agents: List[str] = None
    ) -> ReviewState:
        """
        Execute the review workflow with selected agents.

        Args:
            sections: Parsed sections to review
            agents: List of agents to run (e.g., ['clarity', 'rigor']).
                   If None, runs all agents (default behavior)

        Returns:
            Final workflow state with suggestions
        """
        # Default to all agents if not specified
        if agents is None:
            agents = ["clarity", "rigor"]

        # Build workflow dynamically based on selected agents
        workflow = self._build_workflow(agents)

        initial_state: ReviewState = {
            "sections": sections,
            "sections_for_clarity": [],
            "sections_for_rigor": [],
            "clarity_guidelines": "",
            "rigor_guidelines": "",
            "clarity_suggestions": [],
            "rigor_suggestions": [],
            "final_suggestions": [],
            "error": None
        }

        # Run the workflow
        final_state = await workflow.ainvoke(initial_state)

        return final_state


# Singleton instance
# To disable RAG, set environment variable: USE_RAG=false in .env file
from app.config.settings import settings

review_workflow = ReviewWorkflow(use_rag=settings.use_rag)
