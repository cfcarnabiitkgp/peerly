"""
API router for peer review endpoints.
"""
import time
import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import ReviewRequest, ReviewResponse
from app.services.latex_parser import latex_parser
from app.agents.review_workflow import review_workflow
from app.cache.review_result_cache import create_review_result_cache
from app.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["review"])

# Initialize review result cache with settings
review_cache = None
if settings.review_cache_enabled:
    review_cache = create_review_result_cache(
        similarity_threshold=settings.review_cache_similarity_threshold,
        max_fingerprint_length=settings.review_cache_fingerprint_length,
        strict_matching=settings.review_cache_strict_matching
    )
    mode = "strict (semantic+hash)" if settings.review_cache_strict_matching else "lenient (semantic only)"
    logger.info(f"Review result cache initialized in {mode} mode")
else:
    logger.info("Review result cache disabled")


@router.post("/review", response_model=ReviewResponse)
async def review_manuscript(request: ReviewRequest) -> ReviewResponse:
    """
    Review LaTeX manuscript content and return suggestions.

    Uses semantic caching to avoid re-analyzing identical or very similar content.
    Cache checks are based on content similarity + exact hash verification.

    Args:
        request: Review request with LaTeX content

    Returns:
        Review response with suggestions
    """
    start_time = time.time()

    try:
        # Check cache first (semantic similarity + exact hash verification)
        cached_result = None
        if review_cache is not None:
            cached_result = review_cache.get(
                content=request.content,
                agents=request.agents
            )

        if cached_result:
            # Cache hit! Return cached result
            processing_time = time.time() - start_time
            logger.info(
                f"Cache HIT: Returning cached review result "
                f"(saved ~10-15s, actual time: {processing_time:.2f}s)"
            )

            # Update processing time to reflect cache lookup time
            cached_result["processing_time"] = processing_time
            cached_result["cached"] = True

            return ReviewResponse(**cached_result)

        # Cache miss - proceed with analysis
        logger.info("Cache MISS: Running full review analysis")

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

        # Create response
        response = ReviewResponse(
            success=True,
            sections=result["final_suggestions"],
            total_suggestions=total_suggestions,
            processing_time=processing_time,
            error=None,
            cached=False
        )

        # Store in cache for future requests
        if review_cache is not None:
            try:
                review_cache.set(
                    content=request.content,
                    agents=request.agents,
                    result=response.model_dump()
                )
                logger.info(
                    f"Cached review result for future use "
                    f"(content_len={len(request.content)}, agents={request.agents})"
                )
            except Exception as cache_error:
                # Don't fail the request if caching fails
                logger.error(f"Failed to cache result: {cache_error}")

        return response

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


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get review result cache statistics.

    Returns cache hit/miss rates, time saved, and other metrics.
    """
    if review_cache is None:
        return {
            "cache_enabled": False,
            "message": "Review result cache is disabled"
        }
    return review_cache.get_stats()


@router.delete("/cache/clear")
async def clear_cache():
    """
    Clear all cached review results.

    Useful for forcing fresh analysis or troubleshooting.
    """
    if review_cache is None:
        raise HTTPException(
            status_code=400,
            detail="Review result cache is disabled"
        )

    try:
        review_cache.clear()
        return {
            "status": "success",
            "message": "Review result cache cleared successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )
