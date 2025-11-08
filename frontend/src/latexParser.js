/**
 * Parse LaTeX content to extract sections
 */
export function parseSections(latexContent) {
  const sections = []
  const lines = latexContent.split('\n')

  // Track hierarchy: chapter > section > subsection > subsubsection
  let currentChapter = null
  let currentSection = null
  let currentSubsection = null

  lines.forEach((line, index) => {
    const lineNumber = index + 1

    // Match chapter
    const chapterMatch = line.match(/\\chapter\{([^}]+)\}/)
    if (chapterMatch) {
      currentChapter = {
        type: 'chapter',
        title: chapterMatch[1],
        line: lineNumber,
        startLine: lineNumber,
        endLine: null,
        content: '',
        children: []
      }
      sections.push(currentChapter)
      currentSection = null
      currentSubsection = null
      return
    }

    // Match section
    const sectionMatch = line.match(/\\section\{([^}]+)\}/)
    if (sectionMatch) {
      // Close previous section
      if (currentSection) {
        currentSection.endLine = lineNumber - 1
      }

      currentSection = {
        type: 'section',
        title: sectionMatch[1],
        line: lineNumber,
        startLine: lineNumber,
        endLine: null,
        content: '',
        children: []
      }

      if (currentChapter) {
        currentChapter.children.push(currentSection)
      } else {
        sections.push(currentSection)
      }
      currentSubsection = null
      return
    }

    // Match subsection
    const subsectionMatch = line.match(/\\subsection\{([^}]+)\}/)
    if (subsectionMatch) {
      // Close previous subsection
      if (currentSubsection) {
        currentSubsection.endLine = lineNumber - 1
      }

      currentSubsection = {
        type: 'subsection',
        title: subsectionMatch[1],
        line: lineNumber,
        startLine: lineNumber,
        endLine: null,
        content: '',
        children: []
      }

      if (currentSection) {
        currentSection.children.push(currentSubsection)
      } else if (currentChapter) {
        currentChapter.children.push(currentSubsection)
      } else {
        sections.push(currentSubsection)
      }
      return
    }

    // Match subsubsection
    const subsubsectionMatch = line.match(/\\subsubsection\{([^}]+)\}/)
    if (subsubsectionMatch) {
      const subsubsection = {
        type: 'subsubsection',
        title: subsubsectionMatch[1],
        line: lineNumber,
        startLine: lineNumber,
        endLine: null,
        content: ''
      }

      if (currentSubsection) {
        currentSubsection.children.push(subsubsection)
      } else if (currentSection) {
        currentSection.children.push(subsubsection)
      } else if (currentChapter) {
        currentChapter.children.push(subsubsection)
      } else {
        sections.push(subsubsection)
      }
      return
    }

    // Add content to current section
    if (currentSubsection) {
      currentSubsection.content += line + '\n'
    } else if (currentSection) {
      currentSection.content += line + '\n'
    } else if (currentChapter) {
      currentChapter.content += line + '\n'
    }
  })

  // Close last section
  if (currentSection) {
    currentSection.endLine = lines.length
  }
  if (currentSubsection) {
    currentSubsection.endLine = lines.length
  }

  return sections
}

/**
 * Flatten section hierarchy for easier processing
 */
export function flattenSections(sections, level = 0) {
  const flattened = []

  sections.forEach(section => {
    flattened.push({
      ...section,
      level,
      displayTitle: getDisplayTitle(section, level)
    })

    if (section.children && section.children.length > 0) {
      flattened.push(...flattenSections(section.children, level + 1))
    }
  })

  return flattened
}

/**
 * Get display title with proper indentation
 */
function getDisplayTitle(section, level) {
  const indent = '  '.repeat(level)
  const icon = getSectionIcon(section.type)
  return `${indent}${icon} ${section.title}`
}

/**
 * Get icon for section type
 */
function getSectionIcon(type) {
  const icons = {
    chapter: '📖',
    section: '📄',
    subsection: '📝',
    subsubsection: '📌'
  }
  return icons[type] || '📄'
}

/**
 * Find which section a line belongs to
 */
export function findSectionForLine(sections, lineNumber) {
  for (const section of sections) {
    if (lineNumber >= section.startLine &&
        (section.endLine === null || lineNumber <= section.endLine)) {
      // Check children first
      if (section.children && section.children.length > 0) {
        const childSection = findSectionForLine(section.children, lineNumber)
        if (childSection) return childSection
      }
      return section
    }
  }
  return null
}
