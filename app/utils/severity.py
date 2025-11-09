"""
Utility functions for severity level assignment.

This module provides a centralized function for converting severity scores
to severity levels, ensuring consistency across all agents and the orchestrator.
"""

from app.models.schemas import SeverityLevel


# Severity thresholds (centralized configuration)
ERROR_THRESHOLD = 0.70
WARNING_THRESHOLD = 0.40


def score_to_severity_level(score: float) -> SeverityLevel:
    """
    Convert a severity score (0.0-1.0) to a severity level (ERROR/WARNING/INFO).

    This function applies the threshold logic that maps continuous severity scores
    to discrete severity levels for display in the UI.

    Thresholds:
        - score >= 0.70 → ERROR (red badge)
        - 0.40 <= score < 0.70 → WARNING (yellow badge)
        - score < 0.40 → INFO (blue badge)

    Args:
        score: Severity score from 0.0 to 1.0

    Returns:
        SeverityLevel enum (ERROR, WARNING, or INFO)

    Examples:
        >>> score_to_severity_level(0.85)
        SeverityLevel.ERROR
        >>> score_to_severity_level(0.55)
        SeverityLevel.WARNING
        >>> score_to_severity_level(0.25)
        SeverityLevel.INFO

    Note:
        The LLM assigns scores without knowledge of these thresholds.
        This function is only used in the backend for display purposes.
    """
    if score >= ERROR_THRESHOLD:
        return SeverityLevel.ERROR
    elif score >= WARNING_THRESHOLD:
        return SeverityLevel.WARNING
    else:
        return SeverityLevel.INFO
