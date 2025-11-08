"""
Service for parsing LaTeX documents into sections.
"""
import re
from typing import List
from app.models.schemas import Section


class LatexParser:
    """Parser for extracting sections from LaTeX documents."""

    SECTION_PATTERNS = [
        (r'\\section\{([^}]+)\}', 'section'),
        (r'\\subsection\{([^}]+)\}', 'subsection'),
        (r'\\subsubsection\{([^}]+)\}', 'subsubsection'),
    ]

    SPECIAL_SECTIONS = {
        'abstract': r'\\begin\{abstract\}(.*?)\\end\{abstract\}',
        'introduction': r'\\section\{Introduction\}',
        'methodology': r'\\section\{(Methodology|Methods|Method)\}',
        'results': r'\\section\{(Results|Experimental Results)\}',
        'conclusion': r'\\section\{(Conclusion|Conclusions)\}',
    }

    def parse_sections(self, latex_content: str) -> List[Section]:
        """
        Parse LaTeX content into structured sections.

        Args:
            latex_content: Raw LaTeX document content

        Returns:
            List of Section objects
        """
        sections = []
        lines = latex_content.split('\n')

        # Find document boundaries
        doc_start = self._find_document_start(latex_content)
        doc_end = self._find_document_end(latex_content)

        if doc_start == -1 or doc_end == -1:
            # No document environment, parse entire content
            doc_start = 0
            doc_end = len(latex_content)

        # Extract content within document environment
        document_content = latex_content[doc_start:doc_end]

        # Calculate line offset (how many lines before document_content starts)
        line_offset = latex_content[:doc_start].count('\n')

        # Find all section markers
        section_matches = []
        for pattern, section_type in self.SECTION_PATTERNS:
            for match in re.finditer(pattern, document_content):
                # Count lines within document_content, then add offset for actual line number
                line_num = document_content[:match.start()].count('\n') + 1 + line_offset
                section_matches.append({
                    'title': match.group(1),
                    'type': section_type,
                    'start': match.start(),
                    'line': line_num
                })

        # Sort by position
        section_matches.sort(key=lambda x: x['start'])

        # Extract content for each section
        for i, section in enumerate(section_matches):
            content_start = section['start']
            content_end = section_matches[i + 1]['start'] if i + 1 < len(section_matches) else len(document_content)

            content = document_content[content_start:content_end]
            line_end = section['line'] + content.count('\n')

            # Determine section type based on title
            section_type = self._classify_section(section['title'])

            sections.append(Section(
                title=section['title'],
                content=content,
                section_type=section_type,
                line_start=section['line'],
                line_end=line_end
            ))

        # If no sections found, treat entire document as one section
        if not sections:
            sections.append(Section(
                title="Document",
                content=document_content,
                section_type="general",
                line_start=1,
                line_end=len(lines)
            ))

        return sections

    def _find_document_start(self, content: str) -> int:
        """Find the start of the document environment."""
        match = re.search(r'\\begin\{document\}', content)
        return match.end() if match else -1

    def _find_document_end(self, content: str) -> int:
        """Find the end of the document environment."""
        match = re.search(r'\\end\{document\}', content)
        return match.start() if match else -1

    def _classify_section(self, title: str) -> str:
        """
        Classify section based on title.

        Args:
            title: Section title

        Returns:
            Section type classification
        """
        title_lower = title.lower()

        if any(keyword in title_lower for keyword in ['introduction', 'intro']):
            return 'introduction'
        elif any(keyword in title_lower for keyword in ['method', 'approach', 'design']):
            return 'methodology'
        elif any(keyword in title_lower for keyword in ['result', 'experiment', 'evaluation']):
            return 'results'
        elif any(keyword in title_lower for keyword in ['discussion']):
            return 'discussion'
        elif any(keyword in title_lower for keyword in ['conclusion', 'summary']):
            return 'conclusion'
        elif any(keyword in title_lower for keyword in ['related work', 'background', 'literature']):
            return 'background'
        else:
            return 'general'


# Singleton instance
latex_parser = LatexParser()
