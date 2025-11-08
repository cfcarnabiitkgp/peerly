"""
LaTeX compilation service using Tectonic.
"""
import subprocess
import shutil
from pathlib import Path
from typing import Dict


class LaTeXCompiler:
    """Service for compiling LaTeX documents to PDF."""

    def __init__(self, project_dir: Path, output_dir: Path):
        """
        Initialize LaTeX compiler.

        Args:
            project_dir: Directory containing LaTeX source and project files
            output_dir: Directory to store compiled PDFs
        """
        self.project_dir = project_dir
        self.output_dir = output_dir
        self.project_dir.mkdir(exist_ok=True, parents=True)
        self.output_dir.mkdir(exist_ok=True, parents=True)

    async def compile(self, latex_content: str) -> Dict[str, any]:
        """
        Compile LaTeX content to PDF using Tectonic.

        Args:
            latex_content: LaTeX source code

        Returns:
            Dict with success status and compilation details
        """
        try:
            # Write LaTeX content to the project directory
            tex_file = self.project_dir / "document.tex"
            tex_file.write_text(latex_content)

            pdf_file = self.project_dir / "document.pdf"

            # Run tectonic to compile LaTeX to PDF
            # tectonic will use all files in the project directory
            result = subprocess.run(
                ["tectonic", str(tex_file)],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr or result.stdout,
                    "message": "LaTeX compilation failed"
                }

            # Check if PDF was created
            if not pdf_file.exists():
                return {
                    "success": False,
                    "error": "PDF file was not generated",
                    "message": "Compilation completed but PDF not found"
                }

            # Copy PDF to output location
            output_pdf = self.output_dir / "output.pdf"
            shutil.copy(pdf_file, output_pdf)

            return {
                "success": True,
                "message": "Compilation successful",
                "pdf_path": str(output_pdf)
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Compilation timeout",
                "message": "LaTeX compilation took too long"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "tectonic not found",
                "message": "Please install tectonic: brew install tectonic (macOS) or cargo install tectonic"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "An unexpected error occurred"
            }

    async def validate(self, latex_content: str) -> Dict[str, any]:
        """
        Quick validation of LaTeX syntax without full compilation.

        Args:
            latex_content: LaTeX source code

        Returns:
            Dict with validation status and issues
        """
        content = latex_content.strip()
        issues = []

        # Basic validation checks
        if not content:
            issues.append("Document is empty")

        if "\\begin{document}" not in content:
            issues.append("Missing \\begin{document}")

        if "\\end{document}" not in content:
            issues.append("Missing \\end{document}")

        # Count environment pairs
        begins = content.count("\\begin{")
        ends = content.count("\\end{")

        if begins != ends:
            issues.append(f"Mismatched environments: {begins} \\begin vs {ends} \\end")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def get_output_pdf_path(self) -> Path:
        """
        Get the path to the most recently compiled PDF.

        Returns:
            Path to output PDF
        """
        return self.output_dir / "output.pdf"

    def pdf_exists(self) -> bool:
        """
        Check if a compiled PDF exists.

        Returns:
            True if PDF exists, False otherwise
        """
        return self.get_output_pdf_path().exists()

    def clear_output_directory(self) -> None:
        """Clear all files from the output directory."""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            self.output_dir.mkdir(exist_ok=True, parents=True)


# Global LaTeX compiler instance
latex_compiler = LaTeXCompiler(
    project_dir=Path("/tmp/latex-editor-project"),
    output_dir=Path("/tmp/latex-editor-output")
)
