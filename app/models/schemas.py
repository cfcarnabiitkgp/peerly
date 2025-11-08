"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum


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


class AgentState(BaseModel):
    """State shared across agents in the workflow."""
    sections: List[Section] = Field(default_factory=list, description="Parsed sections")
    clarity_suggestions: List[SectionSuggestions] = Field(default_factory=list)
    rigor_suggestions: List[SectionSuggestions] = Field(default_factory=list)
    ethics_suggestions: List[SectionSuggestions] = Field(default_factory=list)
    final_suggestions: List[SectionSuggestions] = Field(default_factory=list)
    error: Optional[str] = None
