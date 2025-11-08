"""
Orchestrator Agent - Validates, prioritizes, and cross-checks suggestions from other agents.
"""
from typing import List
from langchain_openai import ChatOpenAI
from app.models.schemas import SectionSuggestions, SuggestionGroup
from app.config.settings import settings


class OrchestratorAgent:
    """
    Orchestrator agent that validates and prioritizes suggestions from specialist agents.
    Performs final quality control and removes duplicates.
    """

    def __init__(self):
        self.agent_name = "Orchestrator Agent"
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.2,  # Lower temperature for more consistent validation
            api_key=settings.openai_api_key
        )

    async def validate_and_prioritize(
        self,
        section_suggestions: List[SectionSuggestions]
    ) -> List[SectionSuggestions]:
        """
        Validate and prioritize suggestions from all agents.

        Args:
            section_suggestions: Combined suggestions from all agents

        Returns:
            Validated and prioritized suggestions
        """
        validated_suggestions = []

        for section_sugg in section_suggestions:
            # Remove duplicates
            deduplicated = self._remove_duplicates(section_sugg)

            # Sort by severity
            sorted_sugg = self._sort_by_severity(deduplicated)

            validated_suggestions.append(sorted_sugg)

        return validated_suggestions

    def _remove_duplicates(self, section_sugg: SectionSuggestions) -> SectionSuggestions:
        """
        Remove duplicate or very similar suggestions.

        Args:
            section_sugg: Section suggestions

        Returns:
            Deduplicated section suggestions
        """
        seen_texts = set()
        unique_groups = []

        for group in section_sugg.suggestions:
            unique_items = []

            for item in group.items:
                # Simple deduplication based on text similarity
                text_lower = item.text.lower()

                # Check if similar suggestion already exists
                is_duplicate = any(
                    self._similarity_score(text_lower, seen_text) > 0.8
                    for seen_text in seen_texts
                )

                if not is_duplicate:
                    unique_items.append(item)
                    seen_texts.add(text_lower)

            if unique_items:
                unique_groups.append(SuggestionGroup(
                    type=group.type,
                    count=len(unique_items),
                    items=unique_items
                ))

        return SectionSuggestions(
            section=section_sugg.section,
            line=section_sugg.line,
            section_type=section_sugg.section_type,
            suggestions=unique_groups
        )

    def _sort_by_severity(self, section_sugg: SectionSuggestions) -> SectionSuggestions:
        """
        Sort suggestions by severity (error > warning > info).

        Args:
            section_sugg: Section suggestions

        Returns:
            Sorted section suggestions
        """
        severity_order = {'error': 0, 'warning': 1, 'info': 2}

        for group in section_sugg.suggestions:
            group.items.sort(key=lambda x: severity_order.get(x.severity, 3))

        return section_sugg

    def _similarity_score(self, text1: str, text2: str) -> float:
        """
        Calculate similarity score between two texts (simple word overlap).

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0 and 1
        """
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0


# Singleton instance
orchestrator = OrchestratorAgent()
