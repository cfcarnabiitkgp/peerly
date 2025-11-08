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

**IMPORTANT: Output Format**
You MUST respond with a JSON array of suggestion objects. Each object must have exactly these fields:
- "issue": A concise statement of what rigor problem exists (1 sentence)
- "explanation": Why this undermines technical validity or scientific credibility (1-2 sentences)
- "suggested_fix": Specific actionable fix to address the rigor issue (1-2 sentences)

Example output:
[
  {
    "issue": "The convergence proof assumes continuity without stating this requirement",
    "explanation": "This unstated assumption means the proof is incomplete and could mislead readers about when the result applies. Mathematical rigor requires all assumptions to be explicitly stated",
    "suggested_fix": "Add 'Assume f is continuous on [a,b]' before the proof, and discuss what happens if this assumption is violated"
  },
  {
    "issue": "No statistical significance test is provided for the performance comparison",
    "explanation": "Without significance testing, readers cannot determine if observed differences are meaningful or due to random variation, undermining the validity of the experimental claims",
    "suggested_fix": "Conduct a paired t-test or Wilcoxon signed-rank test to determine statistical significance (p < 0.05), and report p-values in the results table"
  }
]

Output ONLY the JSON array, no other text.
"""

        # Add guidelines if provided
        if guidelines:
            base_prompt += f"\n\n## Reference Guidelines\n\n{guidelines}\n\nUse these guidelines to inform your review and ensure your suggestions align with established best practices for mathematical and experimental rigor."

        return base_prompt

    def get_user_prompt(self, section: Section) -> str:
        """Generate user prompt for rigor review."""
        return f"""Review the following section for RIGOR issues:

**Section Title**: {section.title}
**Section Type**: {section.section_type}

**Content**:
{section.content}

Identify specific rigor issues in this section. Focus on:
- Mathematical statements lacking proofs or justification
- Experimental claims without proper validation
- Statistical methods that may be inappropriate
- Unverified claims or missing evidence
- Unstated assumptions or limitations
- Details needed for reproducibility

Provide 3-5 specific, actionable suggestions to improve rigor.

Remember: Output ONLY a JSON array with objects containing "issue", "explanation", and "suggested_fix" fields.
"""
