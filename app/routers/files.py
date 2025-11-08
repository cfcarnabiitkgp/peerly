"""
API router for file management endpoints.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.file_service import file_service

router = APIRouter(prefix="", tags=["files"])


@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a supporting file (image, .bib, .sty, etc.).

    Args:
        file: Uploaded file

    Returns:
        Dict with success status and message
    """
    if not file.filename:
        return {
            "success": False,
            "error": "No filename provided"
        }

    content = await file.read()
    result = await file_service.save_file(file.filename, content)
    return result


@router.get("/list-files")
async def list_files():
    """
    List all files in the project directory.

    Returns:
        Dict with success status and list of files
    """
    result = await file_service.list_files()
    return result


@router.delete("/delete-file/{filename}")
async def delete_file(filename: str):
    """
    Delete a file from the project directory.

    Args:
        filename: Name of the file to delete

    Returns:
        Dict with success status and message
    """
    result = await file_service.delete_file(filename)
    return result


@router.get("/get-file/{filename}")
async def get_file(filename: str):
    """
    Get the content of a file from the project directory.

    Args:
        filename: Name of the file to read

    Returns:
        Dict with success status and file content
    """
    result = await file_service.get_file_content(filename)
    return result
