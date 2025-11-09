"""
File management service for handling project files.
"""
from pathlib import Path
from typing import List, Dict, Optional
import shutil
import aiofiles
import aiofiles.os


class FileService:
    """Service for managing project files (images, bibliography, style files, etc.)."""

    def __init__(self, project_dir: Path):
        """
        Initialize file service.

        Args:
            project_dir: Directory to store project files
        """
        self.project_dir = project_dir
        self.project_dir.mkdir(exist_ok=True, parents=True)

    async def save_file(self, filename: str, content: bytes) -> Dict[str, any]:
        """
        Save a file to the project directory.

        Args:
            filename: Name of the file
            content: File content as bytes

        Returns:
            Dict with success status and message
        """
        try:
            if not filename:
                return {
                    "success": False,
                    "error": "No filename provided"
                }

            file_path = self.project_dir / filename

            # Save the file using async I/O
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            return {
                "success": True,
                "filename": filename,
                "message": f"File {filename} uploaded successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to upload file"
            }

    async def list_files(self) -> Dict[str, any]:
        """
        List all files in the project directory.

        Returns:
            Dict with success status and list of files
        """
        try:
            files = []
            for file_path in self.project_dir.iterdir():
                if file_path.is_file() and file_path.name != "document.tex":
                    stat = file_path.stat()
                    files.append({
                        "name": file_path.name,
                        "size": stat.st_size,
                        "type": file_path.suffix
                    })

            return {
                "success": True,
                "files": files
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "files": []
            }

    async def delete_file(self, filename: str) -> Dict[str, any]:
        """
        Delete a file from the project directory.

        Args:
            filename: Name of the file to delete

        Returns:
            Dict with success status and message
        """
        try:
            file_path = self.project_dir / filename

            # Check existence using async
            if not await aiofiles.os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "File not found"
                }

            # Delete file using async
            await aiofiles.os.remove(file_path)

            return {
                "success": True,
                "message": f"File {filename} deleted successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_file_content(self, filename: str) -> Dict[str, any]:
        """
        Get the content of a file from the project directory.

        Args:
            filename: Name of the file to read

        Returns:
            Dict with success status and file content
        """
        try:
            file_path = self.project_dir / filename

            # Check existence using async
            if not await aiofiles.os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "File not found"
                }

            # Read file using async I/O
            async with aiofiles.open(file_path, "r", encoding='utf-8') as f:
                content = await f.read()

            return {
                "success": True,
                "content": content,
                "filename": filename
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def clear_project_directory(self) -> None:
        """Clear all files from the project directory."""
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)
            self.project_dir.mkdir(exist_ok=True, parents=True)


# Global file service instance
file_service = FileService(project_dir=Path("/tmp/latex-editor-project"))
