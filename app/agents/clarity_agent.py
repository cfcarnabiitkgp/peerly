"""
Clarity Agent - Reviews technical writing for clarity and comprehension.
"""
from app.agents.base_agent import BaseReviewAgent
from app.models.schemas import Section, SuggestionType


class ClarityAgent(BaseReviewAgent):
    """
    Agent specialized in reviewing clarity of technical writing.
    Identifies unclear statements, complex sentences, and undefined jargon.
    """

    def __init__(self):
        super().__init__(
            agent_name="Clarity Agent",
            suggestion_type=SuggestionType.CLARITY
        )

    def get_system_prompt(self, guidelines: str = "") -> str:
        """Get system prompt for clarity review."""
        base_prompt = """You are an expert technical writing reviewer specializing in CLARITY analysis.

Your role is to identify issues that make technical content difficult to understand:

1. **Unclear Statements**: Vague or ambiguous claims that lack precision
2. **Complex Sentences**: Overly long or convoluted sentence structures
3. **Undefined Jargon**: Technical terms used without proper definition or context
4. **Missing Context**: Statements that assume too much prior knowledge
5. **Logical Gaps**: Unexplained jumps in reasoning or argumentation

Focus on mathematics, computer science, and related technical domains.

**IMPORTANT: Output Format**
You MUST respond with a JSON array of suggestion objects. Each object must have exactly these fields:
- "issue": A concise statement of what's wrong (1 sentence)
- "explanation": Why this is problematic and its impact on clarity (1-2 sentences)
- "suggested_fix": Specific actionable fix or rewrite suggestion (1-2 sentences)

Example output:
[
  {
    "issue": "The term 'convergence rate' is used without definition",
    "explanation": "Readers unfamiliar with optimization theory may not understand what convergence rate means, making it difficult to evaluate the claim's significance",
    "suggested_fix": "Define convergence rate when first introduced, e.g., 'convergence rate (the speed at which the algorithm approaches the optimal solution)'"
  },
  {
    "issue": "This sentence contains three nested clauses making it hard to parse",
    "explanation": "Complex sentence structure forces readers to hold multiple ideas in working memory, reducing comprehension and increasing cognitive load",
    "suggested_fix": "Break into two simpler sentences: First explain the main point, then add the qualifying details in a separate sentence"
  }
]

Output ONLY the JSON array, no other text.
"""

        # Add guidelines if provided
        if guidelines:
            base_prompt += f"\n\n## Reference Guidelines\n\n{guidelines}\n\nUse these guidelines to inform your review and ensure your suggestions align with established best practices."

        return base_prompt

    def get_user_prompt(self, section: Section) -> str:
        """Generate user prompt for clarity review."""
        return f"""Review the following section for CLARITY issues:

**Section Title**: {section.title}
**Section Type**: {section.section_type}

**Content**:
{section.content}

Identify specific clarity issues in this section. Focus on:
- Unclear or ambiguous statements
- Overly complex sentences that should be simplified
- Technical jargon that needs definition
- Missing context or assumptions
- Logical gaps in the argument

Provide 3-5 specific, actionable suggestions to improve clarity.

Remember: Output ONLY a JSON array with objects containing "issue", "explanation", and "suggested_fix" fields.
"""
