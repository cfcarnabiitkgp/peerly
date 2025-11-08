import { useEffect, useRef, useState, useCallback } from 'react'
import { EditorView, keymap, lineNumbers, gutter, GutterMarker, Decoration, ViewPlugin } from '@codemirror/view'
import { EditorState, StateField, StateEffect, RangeSetBuilder } from '@codemirror/state'
import { defaultKeymap, indentWithTab } from '@codemirror/commands'
import { autocompletion } from '@codemirror/autocomplete'
import { syntaxHighlighting, HighlightStyle } from '@codemirror/language'
import { tags } from '@lezer/highlight'

// Group suggestions by line number
function groupSuggestionsByLine(suggestions) {
  const issuesByLine = {}

  suggestions.forEach(section => {
    section.suggestions.forEach(group => {
      group.items.forEach(item => {
        const line = item.line - 1 // CodeMirror lines are 0-indexed
        if (!issuesByLine[line]) {
          issuesByLine[line] = []
        }
        issuesByLine[line].push({
          severity: item.severity,
          type: group.type,
          text: item.text,
          explanation: item.explanation,
          suggested_fix: item.suggested_fix,
          section: section.section
        })
      })
    })
  })

  return issuesByLine
}

// Get highest severity for a line
function getHighestSeverity(issues) {
  const priority = { error: 3, warning: 2, info: 1 }
  return issues.reduce((highest, issue) => {
    return priority[issue.severity] > priority[highest] ? issue.severity : highest
  }, 'info')
}

// Severity colors
const severityColors = {
  error: '#EF4444',
  warning: '#F59E0B',
  info: '#3B82F6'
}

// StateEffect to trigger decoration updates when suggestions change
const updateDecorationsEffect = StateEffect.define()

// Custom gutter marker class
class IssueMarker extends GutterMarker {
  constructor(severity, count, issues, onClick) {
    super()
    this.severity = severity
    this.count = count
    this.issues = issues
    this.onClick = onClick
  }

  toDOM() {
    const marker = document.createElement('div')
    marker.className = 'issue-marker'
    marker.style.cssText = `
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: ${severityColors[this.severity]};
      cursor: pointer;
      position: relative;
      box-shadow: 0 0 4px ${severityColors[this.severity]}80;
    `

    // Add small dot indicator if multiple issues
    if (this.count > 1) {
      const dot = document.createElement('div')
      dot.style.cssText = `
        position: absolute;
        right: -3px;
        top: -3px;
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: ${severityColors[this.severity]};
        border: 1px solid white;
      `
      marker.appendChild(dot)
    }

    // Tooltip content
    const tooltip = document.createElement('div')
    tooltip.className = 'issue-tooltip'
    tooltip.style.cssText = `
      display: none;
      position: absolute;
      left: 20px;
      top: -10px;
      background: white;
      border: 1px solid #E2E8F0;
      border-radius: 6px;
      padding: 12px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      z-index: 1000;
      min-width: 250px;
      max-width: 350px;
      font-size: 12px;
      line-height: 1.5;
    `

    if (this.count === 1) {
      const issue = this.issues[0]
      tooltip.innerHTML = `
        <div style="font-weight: 600; color: ${severityColors[this.severity]}; margin-bottom: 8px;">
          ${this.severity.charAt(0).toUpperCase() + this.severity.slice(1)}: ${issue.type.charAt(0).toUpperCase() + issue.type.slice(1)}
        </div>
        <div style="color: #64748B; margin-bottom: 6px;">${issue.text}</div>
        ${issue.explanation ? `<div style="font-size: 11px; color: #94A3B8; margin-bottom: 6px;">${issue.explanation}</div>` : ''}
        <div style="font-size: 11px; color: #9ca3af; margin-top: 8px; padding-top: 8px; border-top: 1px solid #E2E8F0;">
          Click to view in suggestions panel →
        </div>
      `
    } else {
      const issuesList = this.issues.map(issue => `
        <div style="margin-bottom: 4px;">
          <span style="color: ${severityColors[issue.severity]};">●</span>
          <span style="font-weight: 500;">${issue.type.charAt(0).toUpperCase() + issue.type.slice(1)}:</span>
          <span style="color: #64748B;">${issue.text.substring(0, 50)}${issue.text.length > 50 ? '...' : ''}</span>
        </div>
      `).join('')

      tooltip.innerHTML = `
        <div style="font-weight: 600; margin-bottom: 8px;">
          ${this.count} issues on this line:
        </div>
        ${issuesList}
        <div style="font-size: 11px; color: #9ca3af; margin-top: 8px; padding-top: 8px; border-top: 1px solid #E2E8F0;">
          Click to view all →
        </div>
      `
    }

    marker.appendChild(tooltip)

    // Hover handlers
    marker.addEventListener('mouseenter', () => {
      tooltip.style.display = 'block'
    })
    marker.addEventListener('mouseleave', () => {
      tooltip.style.display = 'none'
    })

    // Click handler
    marker.addEventListener('click', (e) => {
      e.preventDefault()
      e.stopPropagation()
      console.log('Marker clicked! Issues:', this.issues)
      if (this.onClick) {
        this.onClick(this.issues)
      }
    })

    return marker
  }
}

// LaTeX syntax highlighting (Light theme with purple sections)
const latexHighlighting = HighlightStyle.define([
  { tag: tags.keyword, color: '#0066cc' },
  { tag: tags.comment, color: '#008000', fontStyle: 'italic' },
  { tag: tags.string, color: '#a31515' },
  { tag: tags.bracket, color: '#795e26' },
  { tag: tags.heading, color: '#6563ff', fontWeight: '700' }, // Purple sections
])

// Section highlighting decoration
const sectionMark = Decoration.mark({
  class: 'cm-section-command',
})

// ViewPlugin for highlighting LaTeX section commands
function createSectionHighlighter() {
  return ViewPlugin.fromClass(
    class {
      constructor(view) {
        this.decorations = this.buildDecorations(view)
      }

      update(update) {
        if (update.docChanged || update.viewportChanged) {
          this.decorations = this.buildDecorations(update.view)
        }
      }

      buildDecorations(view) {
        const builder = new RangeSetBuilder()

        for (let { from, to } of view.visibleRanges) {
          const text = view.state.doc.sliceString(from, to)
          const regex = /\\(section|subsection|subsubsection|chapter|part|paragraph)\{/g
          let match

          while ((match = regex.exec(text)) !== null) {
            const start = from + match.index
            const end = start + match[0].length - 1
            builder.add(start, end, sectionMark)
          }
        }

        return builder.finish()
      }
    },
    {
      decorations: (v) => v.decorations,
    }
  )
}

// Comprehensive LaTeX autocompletions
const latexCompletions = (context) => {
  const word = context.matchBefore(/\\[a-zA-Z]*/)
  if (!word) return null
  if (word.from === word.to && !context.explicit) return null

  const completions = [
    // Document structure
    { label: '\\documentclass{}', detail: 'Document class', apply: '\\documentclass{article}' },
    { label: '\\begin{}', detail: 'Begin environment', apply: '\\begin{${1:environment}}\n\t$0\n\\end{${1:environment}}', type: 'snippet' },
    { label: '\\end{}', detail: 'End environment', apply: '\\end{${1:environment}}' },

    // Sections
    { label: '\\section{}', detail: 'Section', apply: '\\section{$0}' },
    { label: '\\subsection{}', detail: 'Subsection', apply: '\\subsection{$0}' },
    { label: '\\subsubsection{}', detail: 'Subsubsection', apply: '\\subsubsection{$0}' },
    { label: '\\chapter{}', detail: 'Chapter', apply: '\\chapter{$0}' },
    { label: '\\part{}', detail: 'Part', apply: '\\part{$0}' },
    { label: '\\paragraph{}', detail: 'Paragraph', apply: '\\paragraph{$0}' },

    // Math environments
    { label: '\\begin{equation}', detail: 'Numbered equation', apply: '\\begin{equation}\n\t$0\n\\end{equation}' },
    { label: '\\begin{align}', detail: 'Aligned equations', apply: '\\begin{align}\n\t$0\n\\end{align}' },
    { label: '\\begin{gather}', detail: 'Gathered equations', apply: '\\begin{gather}\n\t$0\n\\end{gather}' },
    { label: '\\begin{matrix}', detail: 'Matrix', apply: '\\begin{matrix}\n\t$0\n\\end{matrix}' },
    { label: '\\begin{pmatrix}', detail: 'Matrix with parentheses', apply: '\\begin{pmatrix}\n\t$0\n\\end{pmatrix}' },
    { label: '\\begin{bmatrix}', detail: 'Matrix with brackets', apply: '\\begin{bmatrix}\n\t$0\n\\end{bmatrix}' },
    { label: '\\begin{cases}', detail: 'Cases', apply: '\\begin{cases}\n\t$0\n\\end{cases}' },

    // Lists
    { label: '\\begin{itemize}', detail: 'Bullet list', apply: '\\begin{itemize}\n\t\\item $0\n\\end{itemize}' },
    { label: '\\begin{enumerate}', detail: 'Numbered list', apply: '\\begin{enumerate}\n\t\\item $0\n\\end{enumerate}' },
    { label: '\\begin{description}', detail: 'Description list', apply: '\\begin{description}\n\t\\item[$0]\n\\end{description}' },
    { label: '\\item', detail: 'List item', apply: '\\item ' },

    // Text formatting
    { label: '\\textbf{}', detail: 'Bold text', apply: '\\textbf{$0}' },
    { label: '\\textit{}', detail: 'Italic text', apply: '\\textit{$0}' },
    { label: '\\underline{}', detail: 'Underline text', apply: '\\underline{$0}' },
    { label: '\\emph{}', detail: 'Emphasize text', apply: '\\emph{$0}' },
    { label: '\\texttt{}', detail: 'Typewriter text', apply: '\\texttt{$0}' },

    // Math commands
    { label: '\\frac{}{}', detail: 'Fraction', apply: '\\frac{$1}{$2}' },
    { label: '\\sqrt{}', detail: 'Square root', apply: '\\sqrt{$0}' },
    { label: '\\sum', detail: 'Summation', apply: '\\sum_{$1}^{$2}' },
    { label: '\\int', detail: 'Integral', apply: '\\int_{$1}^{$2}' },
    { label: '\\lim', detail: 'Limit', apply: '\\lim_{$1}' },
    { label: '\\prod', detail: 'Product', apply: '\\prod_{$1}^{$2}' },
    { label: '\\infty', detail: 'Infinity', apply: '\\infty' },
    { label: '\\partial', detail: 'Partial derivative', apply: '\\partial' },
    { label: '\\nabla', detail: 'Nabla', apply: '\\nabla' },

    // Greek letters
    { label: '\\alpha', detail: 'Alpha', apply: '\\alpha' },
    { label: '\\beta', detail: 'Beta', apply: '\\beta' },
    { label: '\\gamma', detail: 'Gamma', apply: '\\gamma' },
    { label: '\\delta', detail: 'Delta', apply: '\\delta' },
    { label: '\\epsilon', detail: 'Epsilon', apply: '\\epsilon' },
    { label: '\\theta', detail: 'Theta', apply: '\\theta' },
    { label: '\\lambda', detail: 'Lambda', apply: '\\lambda' },
    { label: '\\mu', detail: 'Mu', apply: '\\mu' },
    { label: '\\pi', detail: 'Pi', apply: '\\pi' },
    { label: '\\sigma', detail: 'Sigma', apply: '\\sigma' },
    { label: '\\phi', detail: 'Phi', apply: '\\phi' },
    { label: '\\omega', detail: 'Omega', apply: '\\omega' },

    // Packages
    { label: '\\usepackage{}', detail: 'Use package', apply: '\\usepackage{$0}' },
    { label: '\\usepackage{amsmath}', detail: 'AMS math package', apply: '\\usepackage{amsmath}' },
    { label: '\\usepackage{amssymb}', detail: 'AMS symbols', apply: '\\usepackage{amssymb}' },
    { label: '\\usepackage{graphicx}', detail: 'Graphics package', apply: '\\usepackage{graphicx}' },

    // Document metadata
    { label: '\\title{}', detail: 'Document title', apply: '\\title{$0}' },
    { label: '\\author{}', detail: 'Document author', apply: '\\author{$0}' },
    { label: '\\date{}', detail: 'Document date', apply: '\\date{$0}' },
    { label: '\\maketitle', detail: 'Make title', apply: '\\maketitle' },

    // References
    { label: '\\label{}', detail: 'Label', apply: '\\label{$0}' },
    { label: '\\ref{}', detail: 'Reference', apply: '\\ref{$0}' },
    { label: '\\cite{}', detail: 'Citation', apply: '\\cite{$0}' },

    // Figures and tables
    { label: '\\begin{figure}', detail: 'Figure environment', apply: '\\begin{figure}[h]\n\t\\centering\n\t\\includegraphics{$0}\n\t\\caption{}\n\\end{figure}' },
    { label: '\\begin{table}', detail: 'Table environment', apply: '\\begin{table}[h]\n\t\\centering\n\t\\begin{tabular}{$1}\n\t\t$0\n\t\\end{tabular}\n\t\\caption{}\n\\end{table}' },
    { label: '\\includegraphics{}', detail: 'Include graphics', apply: '\\includegraphics{$0}' },
    { label: '\\caption{}', detail: 'Caption', apply: '\\caption{$0}' },
  ]

  return {
    from: word.from,
    options: completions,
    filter: false,
  }
}

function LatexEditor({ value, onChange, suggestions = [], onMarkerClick, onZoomChange }) {
  const editorRef = useRef(null)
  const viewRef = useRef(null)
  const [isStale, setIsStale] = useState(false)
  const [fontSize, setFontSize] = useState(14)

  // Use a ref to store issues so the gutter can access the latest data
  const issuesByLineRef = useRef({})
  const isStaleRef = useRef(false)

  // Use useCallback to avoid stale closures
  const zoomIn = useCallback(() => {
    setFontSize(prev => {
      const newSize = Math.min(prev + 2, 32)
      if (onZoomChange) onZoomChange(newSize)
      return newSize
    })
  }, [onZoomChange])

  const zoomOut = useCallback(() => {
    setFontSize(prev => {
      const newSize = Math.max(prev - 2, 8)
      if (onZoomChange) onZoomChange(newSize)
      return newSize
    })
  }, [onZoomChange])

  const resetZoom = useCallback(() => {
    setFontSize(14)
    if (onZoomChange) onZoomChange(14)
  }, [onZoomChange])

  // Expose zoom functions to parent
  useEffect(() => {
    if (onZoomChange) {
      onZoomChange(fontSize, { zoomIn, zoomOut, resetZoom })
    }
  }, [fontSize, zoomIn, zoomOut, resetZoom, onZoomChange])

  useEffect(() => {
    if (!editorRef.current) return

    console.log('LatexEditor: Building editor')

    // Create issue gutter and line decorations
    // The gutter will read from issuesByLineRef.current to get the latest data

    // Create line decorations for left borders
    const createDecorations = (state) => {
      const decorations = []
      const doc = state.doc

      Object.entries(issuesByLineRef.current).forEach(([lineNum, issues]) => {
        const lineNumber = parseInt(lineNum)
        if (lineNumber >= 0 && lineNumber < doc.lines) {
          const line = doc.line(lineNumber + 1)
          const severity = getHighestSeverity(issues)
          const color = severityColors[severity]
          const opacity = isStaleRef.current ? '40' : ''

          decorations.push(
            Decoration.line({
              attributes: {
                style: `border-left: 2px solid ${color}${opacity}; padding-left: 4px; opacity: ${isStaleRef.current ? '0.3' : '1'};`
              }
            }).range(line.from)
          )
        }
      })

      return Decoration.set(decorations)
    }

    const lineDecorationsField = StateField.define({
      create: createDecorations,
      update(decorations, tr) {
        // If our custom effect is present, recreate decorations
        if (tr.effects.some(e => e.is(updateDecorationsEffect))) {
          return createDecorations(tr.state)
        }
        // Otherwise just map them through document changes
        return decorations.map(tr.changes)
      },
      provide: f => EditorView.decorations.from(f)
    })

    const issueGutter = gutter({
      class: 'cm-issue-gutter',
      lineMarker(view, line) {
        const lineNum = view.state.doc.lineAt(line.from).number - 1
        const issues = issuesByLineRef.current[lineNum]

        if (!issues || issues.length === 0) return null

        const severity = getHighestSeverity(issues)
        const count = issues.length

        return new IssueMarker(severity, count, issues, (clickedIssues) => {
          console.log('IssueMarker callback triggered! onMarkerClick exists?', !!onMarkerClick)
          console.log('clickedIssues:', clickedIssues)
          if (onMarkerClick) {
            const firstIssue = clickedIssues[0]
            console.log('Calling onMarkerClick with line:', lineNum + 1, 'section:', firstIssue.section)
            onMarkerClick(lineNum + 1, firstIssue.section)
          } else {
            console.log('onMarkerClick is not defined!')
          }
        })
      },
    })

    const startState = EditorState.create({
      doc: value,
      extensions: [
        lineNumbers(),
        lineDecorationsField,
        issueGutter,
        createSectionHighlighter(),
        EditorView.lineWrapping,
        keymap.of([...defaultKeymap, indentWithTab]),
        autocompletion({
          override: [latexCompletions],
          activateOnTyping: true,
        }),
        syntaxHighlighting(latexHighlighting),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            onChange(update.state.doc.toString())
            // Mark as stale on user edit
            if (update.transactions.some(tr => tr.isUserEvent('input')) && suggestions.length > 0 && !isStale) {
              setIsStale(true)
              isStaleRef.current = true
              // Update decorations to reflect stale state (dimmed)
              setTimeout(() => {
                if (viewRef.current) {
                  viewRef.current.dispatch({
                    effects: updateDecorationsEffect.of(null)
                  })
                }
              }, 0)
            }
          }
        }),
        EditorView.theme({
          '&': {
            height: '100%',
            width: '100%',
            fontSize: `${fontSize}px`,
            backgroundColor: '#ffffff',
            color: '#1a1a1a',
          },
          '.cm-content': {
            fontFamily: '"JetBrains Mono", "Fira Code", "Source Code Pro", "Consolas", monospace',
            padding: '10px',
            minHeight: '100%',
            caretColor: '#333333',
            lineHeight: '1.6',
          },
          '.cm-scroller': {
            overflow: 'auto',
            fontFamily: '"JetBrains Mono", "Fira Code", "Source Code Pro", "Consolas", monospace',
            height: '100%',
          },
          '.cm-gutters': {
            backgroundColor: '#f8f8f8',
            borderRight: '1px solid #e0e0e0',
            color: '#666666',
            minWidth: '50px',
          },
          '.cm-lineNumbers': {
            minWidth: '35px',
            color: '#999999',
            fontSize: '11px !important',
            fontFamily: '"JetBrains Mono", "Fira Code", monospace',
          },
          '.cm-lineNumbers .cm-gutterElement': {
            padding: '0 10px 0 8px',
            textAlign: 'right',
            minWidth: '35px',
            fontSize: '11px !important',
            lineHeight: '1.4',
          },
          '.cm-issue-gutter': {
            width: '20px',
            paddingLeft: '4px',
          },
          '.cm-activeLineGutter': {
            backgroundColor: '#e8f4fd',
          },
          '.cm-activeLine': {
            backgroundColor: '#f5f5f5',
          },
          '.cm-selectionBackground, ::selection': {
            backgroundColor: '#add6ff !important',
          },
          '.cm-cursor': {
            borderLeftColor: '#333333',
          },
          '.cm-section-command': {
            color: '#6563ff',
            fontWeight: '700',
            background: 'linear-gradient(135deg, #6563ff08 0%, #8B5CF608 100%)',
            padding: '2px 4px',
            borderRadius: '3px',
          },
        }),
      ],
    })

    const view = new EditorView({
      state: startState,
      parent: editorRef.current,
    })

    viewRef.current = view

    return () => {
      view.destroy()
      viewRef.current = null
    }
  }, []) // Only create once

  // Update font size dynamically via CSS
  useEffect(() => {
    if (!viewRef.current) return

    // Apply font size directly to the editor DOM element
    const editorElement = viewRef.current.dom
    if (editorElement) {
      editorElement.style.fontSize = `${fontSize}px`
    }
  }, [fontSize])

  // Update editor content when value prop changes (e.g., when loading a file)
  useEffect(() => {
    if (!viewRef.current) return

    const currentContent = viewRef.current.state.doc.toString()
    if (currentContent !== value) {
      console.log('Updating editor content from value prop')
      viewRef.current.dispatch({
        changes: {
          from: 0,
          to: currentContent.length,
          insert: value
        }
      })
    }
  }, [value])

  // Update when suggestions change
  useEffect(() => {
    if (!viewRef.current) return

    console.log('Updating suggestions:', suggestions.length, 'sections')

    // Update the ref with new issues data
    issuesByLineRef.current = groupSuggestionsByLine(suggestions)
    console.log('Updated issuesByLineRef with', Object.keys(issuesByLineRef.current).length, 'lines')

    // Reset stale state when new suggestions arrive
    setIsStale(false)
    isStaleRef.current = false

    // Force gutters and decorations to update
    // Dispatch our custom effect to trigger decoration recreation
    viewRef.current.dispatch({
      effects: updateDecorationsEffect.of(null)
    })

    // Also request a measure to ensure gutters update
    viewRef.current.requestMeasure()
  }, [suggestions])

  return (
    <div style={{ height: '100%', width: '100%' }}>
      <div ref={editorRef} style={{ height: '100%', overflow: 'hidden' }} />
    </div>
  )
}

export default LatexEditor
