"""
API router for LaTeX compilation endpoints.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.services.latex_compiler import latex_compiler

router = APIRouter(prefix="", tags=["latex"])


class LaTeXInput(BaseModel):
    """LaTeX input schema."""
    content: str


@router.post("/compile")
async def compile_latex(latex_input: LaTeXInput):
    """
    Compile LaTeX to PDF using Tectonic with all project files.

    Args:
        latex_input: LaTeX content to compile

    Returns:
        Dict with success status and compilation details
    """
    result = await latex_compiler.compile(latex_input.content)
    return result


@router.get("/download-pdf")
async def download_pdf():
    """
    Download the most recently compiled PDF.

    Returns:
        PDF file as download
    """
    if not latex_compiler.pdf_exists():
        raise HTTPException(
            status_code=404,
            detail="No PDF available. Please compile first."
        )

    return FileResponse(
        path=str(latex_compiler.get_output_pdf_path()),
        filename="document.pdf",
        media_type="application/pdf"
    )


@router.get("/preview-pdf")
async def preview_pdf():
    """
    Preview the most recently compiled PDF (for embedding in iframe).

    Returns:
        PDF file for preview
    """
    if not latex_compiler.pdf_exists():
        raise HTTPException(
            status_code=404,
            detail="No PDF available. Please compile first."
        )

    return FileResponse(
        path=str(latex_compiler.get_output_pdf_path()),
        media_type="application/pdf"
    )


@router.post("/validate")
async def validate_latex(latex_input: LaTeXInput):
    """
    Quick validation of LaTeX syntax without full compilation.

    Args:
        latex_input: LaTeX content to validate

    Returns:
        Dict with validation status and issues
    """
    result = await latex_compiler.validate(latex_input.content)
    return result
