"""
Main FastAPI application for Peerly multi-agentic peer review system.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.routers import review, files, latex

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-agentic LLM co-reviewing assistant for technical manuscript writing"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(review.router)
app.include_router(files.router)
app.include_router(latex.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Peerly - Technical Manuscript Reviewer",
        "version": settings.app_version,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info"
    )
