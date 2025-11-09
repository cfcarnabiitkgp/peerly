import { useState, useEffect, useRef } from 'react'
import LatexEditor from './LatexEditor'
import FileManager from './FileManager'
import SuggestionsPanel from './SuggestionsPanel'
import ResizeHandle from './ResizeHandle'
import axios from 'axios'
import './App.css'
import logo from './assets/Peerly_hi_res.jpg'
import angleLeftIcon from './assets/icons/angle-left.svg'
import angleRightIcon from './assets/icons/angle-right.svg'
import downloadIcon from './assets/icons/download-alt.svg'
import compileIcon from './assets/icons/rotate-360.svg'

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  const [latex, setLatex] = useState('')
  const [compiledHtml, setCompiledHtml] = useState('')
  const [isCompiling, setIsCompiling] = useState(false)
  const [compileStatus, setCompileStatus] = useState('')
  const [pdfAvailable, setPdfAvailable] = useState(false)
  const [pdfUrl, setPdfUrl] = useState('')
  const [showFileManager, setShowFileManager] = useState(true)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [fileManagerCollapsed, setFileManagerCollapsed] = useState(false)
  const [suggestions, setSuggestions] = useState([]) // AI suggestions from analysis
  const [expandedSection, setExpandedSection] = useState(null) // Track which section to expand
  const [editorFontSize, setEditorFontSize] = useState(14)
  const [zoomControls, setZoomControls] = useState({ zoomIn: null, zoomOut: null, resetZoom: null })

  // Panel widths (file manager in pixels, others in flex ratios)
  const [fileManagerWidth, setFileManagerWidth] = useState(250)

  // Main panels use flex ratios (relative sizes that always fill screen)
  const [editorFlex, setEditorFlex] = useState(2)    // 2 parts
  const [previewFlex, setPreviewFlex] = useState(2)  // 2 parts
  const [suggestionsFlex, setSuggestionsFlex] = useState(1) // 1 part
  // Total = 5 parts, so editor and preview get 40% each, suggestions gets 20%

  const previewRef = useRef(null)

  // Initialize MathJax
  useEffect(() => {
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']],
        processEscapes: true,
      },
      svg: {
        fontCache: 'global'
      }
    }

    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js'
    script.async = true
    document.head.appendChild(script)

    return () => {
      document.head.removeChild(script)
    }
  }, [])

  // Convert LaTeX to HTML preview (simplified)
  const renderPreview = (latexContent) => {
    // Extract content between \begin{document} and \end{document}
    const docMatch = latexContent.match(/\\begin{document}([\s\S]*?)\\end{document}/)
    if (!docMatch) {
      return '<p style="color: red;">Missing \\begin{document} or \\end{document}</p>'
    }

    let content = docMatch[1]

    // Remove LaTeX comments (lines starting with %)
    content = content.replace(/^%.*$/gm, '')

    // Counters for numbering
    let sectionNum = 0
    let subsectionNum = 0
    let subsubsectionNum = 0

    // Convert basic LaTeX to HTML
    content = content
      // Sections with numbering
      .replace(/\\section\{([^}]+)\}/g, function(match, title) {
        sectionNum++
        subsectionNum = 0
        subsubsectionNum = 0
        return `<h2>${sectionNum} ${title}</h2>`
      })
      .replace(/\\subsection\{([^}]+)\}/g, function(match, title) {
        subsectionNum++
        subsubsectionNum = 0
        return `<h3>${sectionNum}.${subsectionNum} ${title}</h3>`
      })
      .replace(/\\subsubsection\{([^}]+)\}/g, function(match, title) {
        subsubsectionNum++
        return `<h4>${sectionNum}.${subsectionNum}.${subsubsectionNum} ${title}</h4>`
      })

      // Title, author, date
      .replace(/\\maketitle/g, '')
      .replace(/\\title\{([^}]+)\}/g, '<h1 class="title">$1</h1>')
      .replace(/\\author\{([^}]+)\}/g, '<p class="author">$1</p>')
      .replace(/\\date\{([^}]+)\}/g, '<p class="date">$1</p>')
      .replace(/\\today/g, new Date().toLocaleDateString())

      // Text formatting
      .replace(/\\textbf\{([^}]+)\}/g, '<strong>$1</strong>')
      .replace(/\\textit\{([^}]+)\}/g, '<em>$1</em>')
      .replace(/\\emph\{([^}]+)\}/g, '<em>$1</em>')

      // Lists
      .replace(/\\begin\{itemize\}/g, '<ul>')
      .replace(/\\end\{itemize\}/g, '</ul>')
      .replace(/\\begin\{enumerate\}/g, '<ol>')
      .replace(/\\end\{enumerate\}/g, '</ol>')
      .replace(/\\item\s+/g, '<li>')

      // Paragraphs
      .replace(/\n\n+/g, '</p><p>')

    content = '<div class="latex-preview"><p>' + content + '</p></div>'

    return content
  }

  // Update preview when latex changes
  useEffect(() => {
    const html = renderPreview(latex)
    setCompiledHtml(html)

    // Trigger MathJax to re-render
    if (window.MathJax && previewRef.current) {
      setTimeout(() => {
        window.MathJax.typesetPromise([previewRef.current]).catch((err) => {
          console.error('MathJax error:', err)
        })
      }, 100)
    }
  }, [latex])

  const compileToPDF = async () => {
    setIsCompiling(true)
    setCompileStatus('Compiling...')

    try {
      const response = await axios.post(`${API_URL}/compile`, {
        content: latex
      })

      if (response.data.success) {
        setCompileStatus('Compilation successful!')
        setPdfAvailable(true)
        // Update PDF preview with cache-busting timestamp
        setPdfUrl(`${API_URL}/preview-pdf?t=${Date.now()}`)
        setTimeout(() => setCompileStatus(''), 3000)
      } else {
        setCompileStatus(`Error: ${response.data.error}`)
        setPdfUrl('')
      }
    } catch (error) {
      setCompileStatus(`Error: ${error.message}`)
      setPdfUrl('')
    } finally {
      setIsCompiling(false)
    }
  }

  const downloadPDF = () => {
    window.open(`${API_URL}/download-pdf`, '_blank')
  }

  const loadTexContent = async (content, filename = 'template') => {
    setLatex(content)
    setCompileStatus(`Loading ${filename}... Compiling...`)

    // Auto-compile after loading
    try {
      const response = await axios.post(`${API_URL}/compile`, {
        content: content
      })

      if (response.data.success) {
        setPdfAvailable(true)
        setPdfUrl(`${API_URL}/preview-pdf?t=${Date.now()}`)
        setCompileStatus(`${filename} loaded and compiled successfully!`)
        setTimeout(() => setCompileStatus(''), 3000)
      } else {
        setCompileStatus(`${filename} loaded but compilation failed: ${response.data.error}`)
      }
    } catch (error) {
      setCompileStatus(`${filename} loaded but compilation failed: ${error.message}`)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <img src={logo} alt="Peerly Logo" className="app-logo" />
        </div>
        <div className="controls">
          {!showSuggestions && (
            <button
              className="summon-insights-btn"
              onClick={() => {
                console.log('Opening suggestions panel')
                setShowSuggestions(true)
              }}
              title="Show AI insights"
            >
              Summon AI Insights
            </button>
          )}
        </div>
      </header>

      {compileStatus && (
        <div className={`status ${compileStatus.includes('Error') ? 'error' : 'success'}`}>
          {compileStatus}
        </div>
      )}

      <div className="editor-container-flex">
        {showFileManager && (
          <>
            <div
              className={`files-panel ${fileManagerCollapsed ? 'collapsed' : ''}`}
              style={{
                width: fileManagerCollapsed ? '40px' : `${fileManagerWidth}px`,
                minWidth: fileManagerCollapsed ? '40px' : '150px',
                maxWidth: '400px'
              }}
            >
              <div className="panel-header">
                <button
                  className="collapse-btn-icon"
                  onClick={() => setFileManagerCollapsed(!fileManagerCollapsed)}
                  title={fileManagerCollapsed ? 'Expand files' : 'Collapse files'}
                >
                  <img
                    src={fileManagerCollapsed ? angleRightIcon : angleLeftIcon}
                    alt={fileManagerCollapsed ? 'Expand' : 'Collapse'}
                    className="collapse-icon"
                  />
                </button>
              </div>
              {!fileManagerCollapsed && (
                <div className="file-manager-content">
                  <FileManager onLoadTexFile={loadTexContent} />
                </div>
              )}
            </div>
            {!fileManagerCollapsed && (
              <ResizeHandle
                direction="vertical"
                onResize={(delta) => {
                  setFileManagerWidth(prev => Math.max(150, Math.min(400, prev + delta)))
                }}
              />
            )}
          </>
        )}

        <div
          className="editor-panel"
          style={{
            flex: `${editorFlex} 1 0`,
            minWidth: '300px'
          }}
        >
          <div className="panel-header">
            <span className="panel-title">LaTeX Editor</span>
            <div className="editor-zoom-controls">
              <button
                onClick={() => zoomControls.zoomOut && zoomControls.zoomOut()}
                title="Zoom Out"
                className="zoom-btn"
                disabled={!zoomControls.zoomOut}
              >
                <span>−</span>
              </button>
              <button
                onClick={() => zoomControls.resetZoom && zoomControls.resetZoom()}
                title="Reset Zoom"
                className="zoom-btn zoom-reset"
                disabled={!zoomControls.resetZoom}
              >
                {editorFontSize}px
              </button>
              <button
                onClick={() => zoomControls.zoomIn && zoomControls.zoomIn()}
                title="Zoom In"
                className="zoom-btn"
                disabled={!zoomControls.zoomIn}
              >
                <span>+</span>
              </button>
            </div>
          </div>
          <LatexEditor
            value={latex}
            onChange={(value) => setLatex(value || '')}
            suggestions={suggestions}
            onMarkerClick={(line, sectionName) => {
              console.log('onMarkerClick called - line:', line, 'section:', sectionName, 'showSuggestions:', showSuggestions)
              // Open panel if closed
              if (!showSuggestions) {
                console.log('Opening suggestions panel')
                setShowSuggestions(true)
              }
              // Expand the clicked section
              console.log('Setting expanded section to:', sectionName)
              setExpandedSection(sectionName)
            }}
            onZoomChange={(fontSize, controls) => {
              if (fontSize !== undefined) setEditorFontSize(fontSize)
              if (controls) setZoomControls(controls)
            }}
          />
        </div>

        <ResizeHandle
          direction="vertical"
          onResize={(delta) => {
            // Convert pixel delta to flex delta (smaller conversion factor = more sensitive)
            const flexDelta = delta / 100
            setEditorFlex(prev => Math.max(0.5, prev + flexDelta))
            setPreviewFlex(prev => Math.max(0.5, prev - flexDelta))
          }}
        />

        <div
          className="preview-panel"
          style={{
            flex: `${previewFlex} 1 0`,
            minWidth: '300px'
          }}
        >
          <div className="panel-header">
            <span className="panel-title">PDF Preview</span>
            <div className="preview-actions">
              <button
                onClick={compileToPDF}
                disabled={isCompiling}
                className="compile-pdf-btn"
                title="Compile"
              >
                <img src={compileIcon} alt="Compile" className={`compile-icon ${isCompiling ? 'spinning' : ''}`} />
              </button>
              {pdfAvailable && (
                <button onClick={downloadPDF} className="download-pdf-btn" title="Download PDF">
                  <img src={downloadIcon} alt="Download" className="download-icon" />
                </button>
              )}
            </div>
          </div>
          <div className="preview-content">
            {pdfUrl ? (
              <iframe
                src={pdfUrl}
                className="pdf-viewer"
                title="PDF Preview"
              />
            ) : (
              <div className="no-preview">
                <p>No PDF preview available</p>
                <p>Click "Compile to PDF" or enable "Auto-compile" to see the preview</p>
              </div>
            )}
          </div>
        </div>

        <div
          className="suggestions-drawer"
          style={{ display: showSuggestions ? 'flex' : 'none' }}
        >
          <SuggestionsPanel
            latexContent={latex}
            onClose={() => {
              setShowSuggestions(false)
              setExpandedSection(null) // Reset expanded section when closing
            }}
            onSuggestionsChange={(newSuggestions) => setSuggestions(newSuggestions)}
            expandedSectionFromMarker={expandedSection}
          />
        </div>
      </div>
    </div>
  )
}

export default App
