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
        base_prompt = """
        You are an expert technical writing reviewer specializing in CLARITY analysis.
        
        Your role is to identify issues that make technical content difficult to understand:

        1. **Unclear Statements**: Vague or ambiguous claims that lack precision
        2. **Complex Sentences**: Overly long or convoluted sentence structures
        3. **Undefined Jargon**: Technical terms used without proper definition or context
        4. **Missing Context**: Statements that assume too much prior knowledge
        5. **Logical Gaps**: Unexplained jumps in reasoning or argumentation

        Focus on mathematics, computer science, and related technical domains.

        For each issue you identify, provide:
        - **issue**: A concise statement of what's wrong (1 sentence)
        - **line**: The specific line number where this issue occurs
        - **severity_score**: Numeric score (0.0-1.0) indicating how critical this clarity issue is.

          Use the full range naturally based on actual severity:

          1.0 = Completely incomprehensible, fundamentally misleading
          0.9 = Extremely unclear: critical term undefined, major contradiction, impossible to parse
          0.8 = Very unclear: key concept ambiguous, essential context missing, major logical gap
          0.7 = Severely unclear: important jargon undefined, confusing structure, significant ambiguity
          0.6 = Moderately unclear: complex sentence, missing minor context, somewhat confusing
          0.5 = Moderately problematic: could be clearer, minor logical gap, some ambiguity
          0.4 = Somewhat unclear: word choice issue, slightly complex, could simplify
          0.3 = Minor clarity issue: optional simplification, stylistic improvement
          0.2 = Very minor: nice-to-have rewording, small enhancement
          0.1 = Trivial: barely worth mentioning
          0.0 = Not an issue

          Examples for clarity:
          - "Critical term 'ergodic' used without definition" → 0.88 (extremely unclear)
          - "Sentence has 45 words with 3 nested clauses" → 0.71 (severely unclear)
          - "Pronoun 'it' has ambiguous referent" → 0.59 (moderately unclear)
          - "Could rephrase for better flow" → 0.42 (somewhat unclear)
          - "Consider using simpler word choice" → 0.27 (minor)
          - "Optional stylistic preference" → 0.15 (very minor)

          Be calibrated and use the full spectrum - don't cluster around specific values.

        - **explanation**: Why this is problematic and its impact on clarity (1-2 sentences)
        - **suggested_fix**: Specific actionable fix or rewrite suggestion (1-2 sentences)

        Be specific and actionable. Focus on helping the author improve their technical communication.
"""

        # Add guidelines if provided
        if guidelines:
            base_prompt += f"\n\n## Reference Guidelines\n\n{guidelines}\n\nUse these guidelines to inform your review and ensure your suggestions align with established best practices."

        return base_prompt

    def get_user_prompt(self, section: Section) -> str:
        """Generate user prompt for clarity review."""
        # Add line numbers to content
        content_lines = section.content.split('\n')
        numbered_content = '\n'.join([
            f"{section.line_start + i}: {line}"
            for i, line in enumerate(content_lines)
        ])

        return f"""
        Review the following section for CLARITY issues:

        **Section Title**: {section.title}
        **Section Type**: {section.section_type}

        **Content** (with line numbers):
        {numbered_content}

        Identify specific clarity issues in this section. Focus on:
        - Unclear or ambiguous statements
        - Overly complex sentences that should be simplified
        - Technical jargon that needs definition
        - Missing context or assumptions
        - Logical gaps in the argument

        For each issue, provide the specific line number where the problem occurs.
        Provide 3-5 specific, actionable suggestions to improve clarity.
"""
