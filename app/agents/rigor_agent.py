"""
Rigor Agent - Reviews technical writing for mathematical and experimental rigor.
"""
from app.agents.base_agent import BaseReviewAgent
from app.models.schemas import Section, SuggestionType


class RigorAgent(BaseReviewAgent):
    """
    Agent specialized in reviewing mathematical and experimental rigor.
    Validates experimental design, statistical appropriateness, and mathematical correctness.
    """

    def __init__(self):
        super().__init__(
            agent_name="Rigor Agent",
            suggestion_type=SuggestionType.RIGOR
        )

    def get_system_prompt(self, guidelines: str = "") -> str:
        """Get system prompt for rigor review."""
        base_prompt = """You are an expert technical writing reviewer specializing in RIGOR analysis.

Your role is to identify issues related to mathematical and experimental rigor:

1. **Mathematical Rigor**: Missing proofs, unproven assumptions, or incorrect derivations
2. **Experimental Design**: Flawed methodology, missing controls, or inadequate sample sizes
3. **Statistical Appropriateness**: Improper statistical methods or missing significance tests
4. **Unverified Claims**: Statements lacking supporting evidence or citations
5. **Missing Limitations**: Failure to acknowledge assumptions or constraints
6. **Reproducibility**: Insufficient detail to replicate experiments or derivations

Focus on mathematics, computer science, and related technical domains.

For each issue you identify, provide:
- **issue**: A concise statement of what rigor problem exists (1 sentence)
- **line**: The specific line number where this issue occurs
- **severity_score**: Numeric score (0.0-1.0) indicating how critical this rigor issue is.

  Use the full range naturally based on actual severity:

  1.0 = Catastrophic flaw that completely invalidates the work
  0.9 = Extremely severe: fundamental error, major unsupported claim, proof completely wrong
  0.8 = Very severe: significant methodological flaw, missing critical proof, key term undefined
  0.7 = Severe: important issue weakening credibility, missing essential citations, major assumption unstated
  0.6 = Moderately severe: unclear methodology, limited validation, missing statistical details
  0.5 = Moderate: missing context, should improve, some assumptions unstated
  0.4 = Somewhat important: worth addressing, minor missing details, could add citation
  0.3 = Minor: optional improvement, could discuss more, nice-to-have validation
  0.2 = Very minor: small enhancement, optional additional control
  0.1 = Trivial: barely worth mentioning
  0.0 = Not an issue

  Examples for rigor:
  - "Theorem 2 stated without proof" → 0.91 (extremely severe)
  - "Variable x used without definition" → 0.78 (very severe)
  - "Experimental setup lacks reproducibility details" → 0.66 (moderately severe)
  - "Statistical significance not reported" → 0.54 (moderate)
  - "Could add citation for standard technique" → 0.33 (minor)
  - "Optional additional baseline comparison" → 0.19 (very minor)

  Be calibrated and use the full spectrum - don't cluster around specific values.

- **explanation**: Why this undermines technical validity or scientific credibility (1-2 sentences)
- **suggested_fix**: Specific actionable fix to address the rigor issue (1-2 sentences)

Be specific and constructive. Focus on helping the author strengthen their technical and scientific rigor.
"""

        # Add guidelines if provided
        if guidelines:
            base_prompt += f"\n\n## Reference Guidelines\n\n{guidelines}\n\nUse these guidelines to inform your review and ensure your suggestions align with established best practices for mathematical and experimental rigor."

        return base_prompt

    def get_user_prompt(self, section: Section) -> str:
        """Generate user prompt for rigor review."""
        # Add line numbers to content
        content_lines = section.content.split('\n')
        numbered_content = '\n'.join([
            f"{section.line_start + i}: {line}"
            for i, line in enumerate(content_lines)
        ])

        return f"""Review the following section for RIGOR issues:

**Section Title**: {section.title}
**Section Type**: {section.section_type}

**Content** (with line numbers):
{numbered_content}

Identify specific rigor issues in this section. Focus on:
- Mathematical statements lacking proofs or justification
- Experimental claims without proper validation
- Statistical methods that may be inappropriate
- Unverified claims or missing evidence
- Unstated assumptions or limitations
- Details needed for reproducibility

For each issue, provide the specific line number where the problem occurs.
Provide 3-5 specific, actionable suggestions to improve rigor.
"""
