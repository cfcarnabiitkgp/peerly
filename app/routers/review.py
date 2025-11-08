"""
API router for peer review endpoints.
"""
import time
from fastapi import APIRouter, HTTPException
from app.models.schemas import ReviewRequest, ReviewResponse
from app.services.latex_parser import latex_parser
from app.agents.review_workflow import review_workflow

router = APIRouter(prefix="/api", tags=["review"])


@router.post("/review", response_model=ReviewResponse)
async def review_manuscript(request: ReviewRequest) -> ReviewResponse:
    """
    Review LaTeX manuscript content and return suggestions.

    Args:
        request: Review request with LaTeX content

    Returns:
        Review response with suggestions
    """
    start_time = time.time()

    try:
        # Parse LaTeX content into sections
        sections = latex_parser.parse_sections(request.content)

        if not sections:
            return ReviewResponse(
                success=False,
                sections=[],
                total_suggestions=0,
                processing_time=time.time() - start_time,
                error="No sections found in the document"
            )

        # Filter sections if specific ones requested
        if request.sections_to_review:
            sections = [
                s for s in sections
                if s.title in request.sections_to_review
            ]

        # Run the multi-agent review workflow with selected agents
        result = await review_workflow.review(sections, agents=request.agents)

        # Check for errors
        if result["error"]:
            return ReviewResponse(
                success=False,
                sections=[],
                total_suggestions=0,
                processing_time=time.time() - start_time,
                error=result["error"]
            )

        # Calculate total suggestions
        total_suggestions = sum(
            sum(len(group.items) for group in section.suggestions)
            for section in result["final_suggestions"]
        )

        processing_time = time.time() - start_time

        return ReviewResponse(
            success=True,
            sections=result["final_suggestions"],
            total_suggestions=total_suggestions,
            processing_time=processing_time,
            error=None
        )

    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail=f"Review failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Peerly Review API"
    }
