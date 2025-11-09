"""
LLM-Based Orchestrator Agent - Intelligently validates, deduplicates, and merges suggestions.

Uses GPT-4 to:
- Detect semantic duplicates (not just text overlap)
- Identify contradictions between agents
- Merge similar suggestions into concise versions
- Prioritize by impact and actionability
- Quality control on suggestion value
"""
import asyncio
from typing import List, Dict
from langchain_openai import ChatOpenAI
from app.models.schemas import (
    SectionSuggestions,
    SuggestionGroup,
    SuggestionItem,
    SuggestionType,
    SeverityLevel,
    OrchestratedSuggestion,
    OrchestratorSectionResponse,
)
from app.config.settings import settings
from app.utils.severity import score_to_severity_level
import logging

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    LLM-powered orchestrator that intelligently processes suggestions from all agents.

    Uses parallel processing (asyncio.gather) to orchestrate each section independently,
    then combines results.
    """

    def __init__(self):
        self.agent_name = "Orchestrator Agent"
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.2,  # Lower temperature for consistent decisions
            api_key=settings.openai_api_key
        )

    async def validate_and_prioritize(
        self,
        section_suggestions: List[SectionSuggestions]
    ) -> List[SectionSuggestions]:
        """
        Validate and prioritize suggestions from all agents using LLM.

        Processes sections in parallel using asyncio.gather for efficiency.

        Args:
            section_suggestions: Combined suggestions from all agents

        Returns:
            Validated, deduplicated, and prioritized suggestions
        """
        logger.info(f"Orchestrator processing {len(section_suggestions)} sections in parallel")

        # Process all sections in parallel
        tasks = [
            self._orchestrate_section(section_sugg)
            for section_sugg in section_suggestions
        ]

        orchestrated_sections = await asyncio.gather(*tasks)

        logger.info(f"Orchestrator completed processing {len(orchestrated_sections)} sections")
        return orchestrated_sections

    async def _orchestrate_section(
        self,
        section_sugg: SectionSuggestions
    ) -> SectionSuggestions:
        """
        Orchestrate suggestions for a single section using LLM.

        The LLM reviews all suggestions for this section and decides:
        - Which to keep as-is
        - Which to merge (semantic duplicates)
        - Which to discard (low value, contradictory)
        - How to resolve contradictions

        Args:
            section_sugg: All suggestions for one section from all agents

        Returns:
            Orchestrated section with deduplicated, merged suggestions
        """
        # Quick check: if no suggestions, return as-is
        if not section_sugg.suggestions or all(len(g.items) == 0 for g in section_sugg.suggestions):
            return section_sugg

        # Flatten all suggestions into a list with metadata
        all_items = []
        for group in section_sugg.suggestions:
            for item in group.items:
                all_items.append({
                    "agent": str(group.type),
                    "issue": item.text,
                    "line": item.line,
                    "severity_score": item.severity_score or 0.5,
                    "explanation": item.explanation or "",
                    "suggested_fix": item.suggested_fix or ""
                })

        # If only 1-2 suggestions, skip LLM orchestration (not worth the cost)
        if len(all_items) <= 2:
            logger.debug(f"Section '{section_sugg.section}' has only {len(all_items)} suggestions, skipping orchestration")
            return self._sort_by_severity_score(section_sugg)

        try:
            # Call LLM to orchestrate
            orchestrated = await self._llm_orchestrate(
                section_name=section_sugg.section,
                section_type=section_sugg.section_type,
                suggestions=all_items
            )

            # Convert back to SectionSuggestions format
            return self._rebuild_section_suggestions(section_sugg, orchestrated)

        except Exception as e:
            logger.error(f"Error in LLM orchestration for section '{section_sugg.section}': {e}")
            # Fallback to simple sorting
            return self._sort_by_severity_score(section_sugg)

    async def _llm_orchestrate(
        self,
        section_name: str,
        section_type: str,
        suggestions: List[Dict]
    ) -> OrchestratorSectionResponse:
        """
        Call LLM to orchestrate suggestions for one section.

        Args:
            section_name: Name of the section
            section_type: Type of section (e.g., "introduction", "methodology")
            suggestions: List of all suggestions from all agents

        Returns:
            Orchestrator's final suggestions (deduplicated, merged, prioritized)
        """
        # Build the system prompt
        system_prompt = self._get_system_prompt()

        # Build the user prompt with all suggestions
        user_prompt = self._build_user_prompt(section_name, section_type, suggestions)

        # Create structured LLM
        structured_llm = self.llm.with_structured_output(OrchestratorSectionResponse)

        # Call LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await structured_llm.ainvoke(messages)
        return response

    def _get_system_prompt(self) -> str:
        """Get the system prompt for orchestrator LLM."""
        return """You are an expert peer review orchestrator for academic research papers.

Your job is to review suggestions from multiple specialized agents (Clarity, Rigor, etc.)
and produce a final, high-quality list of suggestions for the author.

**Your responsibilities:**

1. **Detect Duplicates**: Identify suggestions that are semantically similar, even if worded differently.
   - Example: "Variable x is undefined" and "Missing definition for variable x" → MERGE

2. **Merge Similar Suggestions**: Combine redundant suggestions into one concise, comprehensive suggestion.
   - Keep the higher severity_score
   - Combine insights from both explanations
   - List all contributing agents in agent_sources

3. **Detect Contradictions**: Identify when agents give conflicting advice.
   - Example: Clarity says "shorten", Rigor says "add more detail"
   - Resolve intelligently: balance or prioritize based on impact
   - Add orchestrator_note explaining the resolution

4. **Quality Control**: Discard suggestions that are:
   - Too minor or nitpicky (very low value)
   - Redundant after merging
   - Not actionable

5. **Prioritize**: Order by impact × actionability, not just severity score.

**Guidelines:**
- Be CONSERVATIVE: When in doubt, keep the suggestion
- Preserve important feedback even if minor
- For contradictions, try to find a balanced middle ground
- Keep suggestions concise (1-2 sentences each field)
- Maintain the author's voice - don't be overly critical

Output a list of final suggestions, deduplicated and prioritized."""

    def _build_user_prompt(
        self,
        section_name: str,
        section_type: str,
        suggestions: List[Dict]
    ) -> str:
        """Build user prompt with all suggestions for this section."""
        # Format suggestions nicely
        formatted_suggestions = []
        for i, sugg in enumerate(suggestions, 1):
            formatted_suggestions.append(
                f"{i}. **Agent**: {sugg['agent']}\n"
                f"   **Line**: {sugg['line']}\n"
                f"   **Severity Score**: {sugg['severity_score']:.2f}\n"
                f"   **Issue**: {sugg['issue']}\n"
                f"   **Explanation**: {sugg['explanation']}\n"
                f"   **Suggested Fix**: {sugg['suggested_fix']}\n"
            )

        suggestions_text = "\n".join(formatted_suggestions)

        return f"""Review the following suggestions for the **{section_name}** section (type: {section_type}).

**All Suggestions ({len(suggestions)} total):**

{suggestions_text}

Please analyze these suggestions and produce a final, deduplicated list:
- Merge semantically similar suggestions
- Detect and resolve contradictions
- Discard low-value suggestions
- Prioritize by impact and actionability

For each final suggestion, specify:
- issue, line, severity_score, explanation, suggested_fix
- agent_sources: list of agents that contributed (e.g., ["clarity"], ["clarity", "rigor"])
- orchestrator_note: optional note if merged or resolved contradiction
"""

    def _rebuild_section_suggestions(
        self,
        original_section: SectionSuggestions,
        orchestrated: OrchestratorSectionResponse
    ) -> SectionSuggestions:
        """
        Convert orchestrated suggestions back to SectionSuggestions format.

        Groups suggestions by agent_sources to rebuild SuggestionGroups.
        """
        # Group orchestrated suggestions by primary agent
        grouped: Dict[SuggestionType, List[SuggestionItem]] = {}

        for orch_sugg in orchestrated.suggestions:
            # Determine primary agent (first in sources, or 'clarity' as default)
            primary_agent = orch_sugg.agent_sources[0] if orch_sugg.agent_sources else "clarity"

            # Map to SuggestionType enum
            agent_type_map = {
                "clarity": SuggestionType.CLARITY,
                "rigor": SuggestionType.RIGOR,
                "ethics": SuggestionType.ETHICS,
                "style": SuggestionType.STYLE,
                "grammar": SuggestionType.GRAMMAR,
            }
            suggestion_type = agent_type_map.get(primary_agent, SuggestionType.CLARITY)

            # Determine severity level from score using centralized utility
            severity = score_to_severity_level(orch_sugg.severity_score)

            # Create SuggestionItem
            item = SuggestionItem(
                text=orch_sugg.issue,
                line=orch_sugg.line,
                severity=severity,
                severity_score=orch_sugg.severity_score,
                explanation=orch_sugg.explanation,
                suggested_fix=orch_sugg.suggested_fix
            )

            if suggestion_type not in grouped:
                grouped[suggestion_type] = []
            grouped[suggestion_type].append(item)

        # Rebuild SuggestionGroups
        new_groups = []
        for suggestion_type, items in grouped.items():
            if items:
                # Sort by severity score (highest first)
                items.sort(key=lambda x: x.severity_score or 0, reverse=True)

                new_groups.append(SuggestionGroup(
                    type=suggestion_type,
                    count=len(items),
                    items=items
                ))

        return SectionSuggestions(
            section=original_section.section,
            line=original_section.line,
            section_type=original_section.section_type,
            suggestions=new_groups
        )

    def _sort_by_severity_score(self, section_sugg: SectionSuggestions) -> SectionSuggestions:
        """
        Simple fallback: sort suggestions by severity score (highest first).

        Used when LLM orchestration is skipped or fails.
        """
        for group in section_sugg.suggestions:
            group.items.sort(
                key=lambda x: (x.severity_score or 0),
                reverse=True
            )
        return section_sugg


# Singleton instance
orchestrator = OrchestratorAgent()
