"""
Base agent class for all review agents.
"""
from abc import ABC, abstractmethod
from typing import List
from langchain_openai import ChatOpenAI
from app.models.schemas import (
    Section,
    SuggestionItem,
    SuggestionType,
    SeverityLevel,
    AgentSuggestionResponse,
)
from app.config.settings import settings

# keywords for determining severity levels of suggestions
SEVERITY_ERROR_KEYWORDS = ['must', 'required', 'missing', 'incorrect', 'error', 'critical']
SEVERITY_WARNING_KEYWORDS = ['should', 'recommend', 'unclear', 'ambiguous', 'consider revising']


class BaseReviewAgent(ABC):
    """
    Abstract base class for review agents.
    Each agent specializes in reviewing specific aspects of technical writing.
    """

    def __init__(self, agent_name: str, suggestion_type: SuggestionType):
        """
        Initialize the base agent.

        Args:
            agent_name: Name of the agent
            suggestion_type: Type of suggestions this agent generates
        """
        self.agent_name = agent_name
        self.suggestion_type = suggestion_type
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
        )

    @abstractmethod
    def get_system_prompt(self, guidelines: str = "") -> str:
        """
        Get the system prompt for this agent.

        Args:
            guidelines: Retrieved guidelines from RAG (optional)

        Returns:
            System prompt string
        """
        pass

    @abstractmethod
    def get_user_prompt(self, section: Section) -> str:
        """
        Generate user prompt for reviewing a section.

        Args:
            section: Section to review

        Returns:
            User prompt string
        """
        pass

    async def review_section(
        self, section: Section, guidelines: str = ""
    ) -> List[SuggestionItem]:
        """
        Review a section and generate suggestions using structured output.

        Args:
            section: Section to review
            guidelines: Retrieved guidelines from RAG (optional)

        Returns:
            List of suggestion items
        """
        try:
            # Create structured LLM that returns AgentSuggestionResponse
            structured_llm = self.llm.with_structured_output(AgentSuggestionResponse)

            # Build messages
            messages = [
                {"role": "system", "content": self.get_system_prompt(guidelines)},
                {"role": "user", "content": self.get_user_prompt(section)}
            ]

            # Get structured response - returns AgentSuggestionResponse object!
            response = await structured_llm.ainvoke(messages)

            # Convert StructuredSuggestion objects to SuggestionItem objects
            suggestions = []
            for structured_suggestion in response.suggestions:
                # Determine severity based on issue text
                severity = self._determine_severity(structured_suggestion.issue)

                suggestions.append(SuggestionItem(
                    text=structured_suggestion.issue,
                    line=section.line_start,
                    severity=severity,
                    explanation=structured_suggestion.explanation,
                    suggested_fix=structured_suggestion.suggested_fix
                ))

            return suggestions

        except Exception as e:
            print(f"Error in {self.agent_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _determine_severity(self, text: str) -> SeverityLevel:
        """
        Determine severity level based on suggestion text.

        Args:
            text: Suggestion text

        Returns:
            Severity level
        """
        text_lower = text.lower()

        # Error indicators
        if any(keyword in text_lower for keyword in SEVERITY_ERROR_KEYWORDS):
            return SeverityLevel.ERROR

        # Warning indicators
        elif any(keyword in text_lower for keyword in SEVERITY_WARNING_KEYWORDS):
            return SeverityLevel.WARNING

        # Info by default
        else:
            return SeverityLevel.INFO
