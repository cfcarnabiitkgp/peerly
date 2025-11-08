"""
Base agent class for all review agents.
"""
from abc import ABC, abstractmethod
from typing import List
import json
from langchain_openai import ChatOpenAI
from app.models.schemas import Section, SuggestionItem, SuggestionType, SeverityLevel
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
        Review a section and generate suggestions.

        Args:
            section: Section to review
            guidelines: Retrieved guidelines from RAG (optional)

        Returns:
            List of suggestion items
        """
        try:
            # Build messages
            messages = [
                {"role": "system", "content": self.get_system_prompt(guidelines)},
                {"role": "user", "content": self.get_user_prompt(section)}
            ]

            # Get response from LLM
            response = await self.llm.ainvoke(messages)
            content = response.content

            # Parse suggestions from response
            suggestions = self._parse_suggestions(content, section)

            return suggestions

        except Exception as e:
            print(f"Error in {self.agent_name}: {str(e)}")
            return []

    def _parse_suggestions(self, response: str, section: Section) -> List[SuggestionItem]:
        """
        Parse LLM response into structured suggestions.

        Args:
            response: Raw LLM response (expected to be JSON array)
            section: Section being reviewed

        Returns:
            List of suggestion items
        """
        suggestions = []

        try:
            # Try to parse JSON response
            # Expected format: [{"issue": "...", "explanation": "...", "suggested_fix": "..."}]
            response_clean = response.strip()

            # Extract JSON array if wrapped in markdown code blocks
            if response_clean.startswith('```'):
                # Remove markdown code fences
                lines = response_clean.split('\n')
                response_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_clean
                response_clean = response_clean.replace('```json', '').replace('```', '').strip()

            data = json.loads(response_clean)

            # Handle both array and single object
            if isinstance(data, dict):
                data = [data]

            for item in data:
                if not isinstance(item, dict):
                    continue

                issue = item.get('issue', '').strip()
                explanation = item.get('explanation', '').strip()
                suggested_fix = item.get('suggested_fix', '').strip()

                # Skip if issue is empty or too short
                if not issue or len(issue) < 10:
                    continue

                # Determine severity based on issue text
                severity = self._determine_severity(issue)

                suggestions.append(SuggestionItem(
                    text=issue,
                    line=section.line_start,
                    severity=severity,
                    explanation=explanation if explanation else None,
                    suggested_fix=suggested_fix if suggested_fix else None
                ))

        except json.JSONDecodeError as e:
            # Fallback to old parsing if JSON fails
            print(f"Warning: Failed to parse JSON response from {self.agent_name}: {e}")
            print(f"Response was: {response[:200]}...")
            suggestions = self._parse_suggestions_fallback(response, section)

        return suggestions

    def _parse_suggestions_fallback(self, response: str, section: Section) -> List[SuggestionItem]:
        """
        Fallback parser for non-JSON responses (backwards compatibility).

        Args:
            response: Raw LLM response
            section: Section being reviewed

        Returns:
            List of suggestion items
        """
        suggestions = []
        lines = response.strip().split('\n')

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Remove bullet points or numbers
            if line.startswith('- ') or line.startswith('* '):
                line = line[2:].strip()
            elif line and line[0].isdigit() and '. ' in line:
                line = line.split('. ', 1)[1].strip()

            if line and len(line) > 10:
                severity = self._determine_severity(line)

                suggestions.append(SuggestionItem(
                    text=line,
                    line=section.line_start,
                    severity=severity,
                    explanation=None,
                    suggested_fix=None
                ))

        return suggestions

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
