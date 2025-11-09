"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum


# ============================================================================
# Structured LLM Output Models (for agents using with_structured_output)
# ============================================================================

class StructuredSuggestion(BaseModel):
    """
    Individual suggestion from LLM with structured fields.
    Used by agents with LangChain's with_structured_output().
    """
    issue: str = Field(
        description="Concise statement of what's wrong (1 sentence). Keep it short and concise."
    )
    line: int = Field(
        description="The specific line number where this issue occurs in the provided content"
    )
    severity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Severity score from 0.0 to 1.0 indicating how critical this issue is. Use the full range naturally based on actual severity."
    )
    explanation: str = Field(
        description="Why this is problematic and its impact (maximum 1-2 sentences). Use concise language and avoid unnecessary details."
    )
    suggested_fix: str = Field(
        description="Specific actionable fix or improvement (maximum 1-2 sentences). Use concise language and avoid unnecessary details."
    )


class AgentSuggestionResponse(BaseModel):
    """
    Response model for agent LLM calls.
    Contains a list of structured suggestions.
    """
    suggestions: List[StructuredSuggestion] = Field(
        description="List of suggestions for the reviewed section",
        default_factory=list
    )


class OrchestratedSuggestion(BaseModel):
    """
    Final suggestion after orchestrator review (kept or merged).
    """
    issue: str = Field(
        description="The issue statement (original or merged)"
    )
    line: int = Field(
        description="Line number where this issue occurs"
    )
    severity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Severity score (may be adjusted by orchestrator if merged)"
    )
    explanation: str = Field(
        description="Explanation (original or merged)"
    )
    suggested_fix: str = Field(
        description="Suggested fix (original or merged)"
    )
    agent_sources: List[str] = Field(
        description="Which agents contributed to this suggestion (e.g., ['clarity', 'rigor'])"
    )
    orchestrator_note: Optional[str] = Field(
        None,
        description="Optional note from orchestrator (e.g., 'Merged from 2 suggestions', 'Contradiction resolved')"
    )


class OrchestratorSectionResponse(BaseModel):
    """
    Orchestrator's final suggestions for one section.
    """
    suggestions: List[OrchestratedSuggestion] = Field(
        description="Final list of suggestions after deduplication, merging, and quality control.",
        default_factory=list
    )


# ============================================================================
# API Models (for HTTP requests/responses)
# ============================================================================


class SuggestionType(str, Enum):
    """Types of suggestions that can be generated."""
    CLARITY = "clarity"
    RIGOR = "rigor"
    ETHICS = "ethics"
    STYLE = "style"
    GRAMMAR = "grammar"


class SeverityLevel(str, Enum):
    """Severity levels for suggestions."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Section(BaseModel):
    """Represents a section of the LaTeX document."""
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    section_type: str = Field(..., description="Type of section (e.g., introduction, methodology)")
    line_start: int = Field(..., description="Starting line number")
    line_end: int = Field(..., description="Ending line number")


class SuggestionItem(BaseModel):
    """Individual suggestion from an agent."""
    text: str = Field(..., description="Suggestion text")
    line: int = Field(..., description="Line number where issue occurs")
    severity: SeverityLevel = Field(default=SeverityLevel.INFO, description="Severity level")
    severity_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Severity confidence score (0.0-1.0)")
    explanation: Optional[str] = Field(None, description="Detailed explanation")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix if applicable")


class SuggestionGroup(BaseModel):
    """Group of suggestions by type."""
    type: SuggestionType = Field(..., description="Type of suggestion")
    count: int = Field(..., description="Number of suggestions")
    items: List[SuggestionItem] = Field(default_factory=list, description="List of suggestions")


class SectionSuggestions(BaseModel):
    """Suggestions for a specific section."""
    section: str = Field(..., description="Section name")
    line: int = Field(..., description="Section starting line")
    section_type: str = Field(..., description="Type of section")
    suggestions: List[SuggestionGroup] = Field(default_factory=list, description="Grouped suggestions")


class ReviewRequest(BaseModel):
    """Request to review LaTeX content."""
    content: str = Field(..., description="LaTeX document content")
    sections_to_review: Optional[List[str]] = Field(
        None,
        description="Specific sections to review (if None, review all)"
    )
    agents: Optional[List[Literal["clarity", "rigor"]]] = Field(
        default=["clarity", "rigor"],
        description="Which agents to run: 'clarity', 'rigor', or both (default: both)"
    )


class ReviewResponse(BaseModel):
    """Response containing review suggestions."""
    success: bool = Field(..., description="Whether the review was successful")
    sections: List[SectionSuggestions] = Field(default_factory=list, description="Suggestions per section")
    total_suggestions: int = Field(0, description="Total number of suggestions")
    processing_time: float = Field(..., description="Time taken to process in seconds")
    error: Optional[str] = Field(None, description="Error message if any")
