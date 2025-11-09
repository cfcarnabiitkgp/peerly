import { useState, useEffect } from 'react'
import axios from 'axios'
import './SuggestionsPanel.css'
import angleRightIcon from './assets/icons/angle-right.svg'
import channelIcon from './assets/icons/channel.svg'
import searchIcon from './assets/icons/search-alt.svg'
import sigmaIcon from './assets/icons/sigma.svg'
import trashIcon from './assets/icons/trash-alt.svg'
import redIcon from './assets/icons/red.png'
import yellowIcon from './assets/icons/yellow.png'
import blueIcon from './assets/icons/blue.png'

const BACKEND_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function SuggestionsPanel({ latexContent, onClose, onSuggestionsChange, expandedSectionFromMarker }) {
  const [expandedSection, setExpandedSection] = useState(expandedSectionFromMarker)
  const [suggestions, setSuggestions] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [totalStats, setTotalStats] = useState({ clarity: 0, rigor: 0 })
  const [severityStats, setSeverityStats] = useState({ error: 0, warning: 0, info: 0 })
  const [selectedAgent, setSelectedAgent] = useState('all') // 'clarity', 'rigor', 'all'
  const [hasRun, setHasRun] = useState(false)
  const [expandedExplanations, setExpandedExplanations] = useState(new Set())

  // When a marker is clicked, expand that section
  useEffect(() => {
    if (expandedSectionFromMarker) {
      console.log('Expanding section from marker click:', expandedSectionFromMarker)
      setExpandedSection(expandedSectionFromMarker)
    }
  }, [expandedSectionFromMarker])

  // Notify parent when suggestions change
  useEffect(() => {
    if (onSuggestionsChange) {
      onSuggestionsChange(suggestions)
    }
  }, [suggestions])

  // Fetch suggestions from backend
  const fetchSuggestions = async (agent = 'all') => {
    if (!latexContent || latexContent.trim().length < 50) {
      setSuggestions([])
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      // Prepare agents list based on selection
      const agentsList = agent === 'all' ? ['clarity', 'rigor'] : [agent]

      const response = await axios.post(`${BACKEND_URL}/api/review`, {
        content: latexContent,
        agents: agentsList
      })

      if (response.data.success) {
        setSuggestions(response.data.sections)

        // Calculate agent-based stats
        const stats = { clarity: 0, rigor: 0, ethics: 0, style: 0, grammar: 0 }
        const sevStats = { error: 0, warning: 0, info: 0 }

        response.data.sections.forEach(section => {
          section.suggestions.forEach(group => {
            if (stats[group.type] !== undefined) {
              stats[group.type] += group.count
            }
            // Count by severity
            group.items.forEach(item => {
              if (sevStats[item.severity] !== undefined) {
                sevStats[item.severity] += 1
              }
            })
          })
        })

        setTotalStats(stats)
        setSeverityStats(sevStats)
      } else {
        setError(response.data.error || 'Failed to fetch suggestions')
        setSuggestions([])
      }
    } catch (err) {
      console.error('Error fetching suggestions:', err)
      setError(err.response?.data?.detail || 'Failed to connect to backend. Make sure the backend is running.')
      setSuggestions([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleRunAgent = () => {
    // Clear previous suggestions before running new analysis
    setSuggestions([])
    setTotalStats({ clarity: 0, rigor: 0 })
    setSeverityStats({ error: 0, warning: 0, info: 0 })
    setError(null)
    setHasRun(true)
    fetchSuggestions(selectedAgent)
  }

  const handleClearSuggestions = () => {
    setSuggestions([])
    setTotalStats({ clarity: 0, rigor: 0 })
    setSeverityStats({ error: 0, warning: 0, info: 0 })
    setError(null)
    setHasRun(false)
    // Notify parent to clear markers
    if (onSuggestionsChange) {
      onSuggestionsChange([])
    }
  }

  const handleRefreshSuggestions = () => {
    fetchSuggestions(selectedAgent)
  }

  const getSuggestionIcon = (type) => {
    const iconMap = {
      clarity: { type: 'svg', icon: searchIcon },
      rigor: { type: 'svg', icon: sigmaIcon },
      ethics: { type: 'emoji', icon: '⚖️' },
      style: { type: 'emoji', icon: '✨' },
      grammar: { type: 'emoji', icon: '📝' }
    }
    return iconMap[type] || { type: 'emoji', icon: '💭' }
  }

  const getSeverityBadge = (severity) => {
    const badges = {
      error: { icon: redIcon, label: 'Error', class: 'severity-error', color: '#EF4444' },
      warning: { icon: yellowIcon, label: 'Warning', class: 'severity-warning', color: '#F59E0B' },
      info: { icon: blueIcon, label: 'Info', class: 'severity-info', color: '#3B82F6' }
    }
    return badges[severity] || badges.info
  }

  const toggleSection = (sectionName) => {
    console.log('toggleSection called:', sectionName, 'current expanded:', expandedSection)
    setExpandedSection(expandedSection === sectionName ? null : sectionName)
  }

  const toggleExplanation = (itemId) => {
    setExpandedExplanations(prev => {
      const newSet = new Set(prev)
      if (newSet.has(itemId)) {
        newSet.delete(itemId)
      } else {
        newSet.add(itemId)
      }
      return newSet
    })
  }

  return (
    <div className="suggestions-panel">
      {/* Vertical tab handle on left edge */}
      <button
        className="drawer-handle"
        onClick={() => {
          console.log('Closing suggestions panel')
          onClose()
        }}
        title="Close panel (click here to minimize)"
      >
        <img src={angleRightIcon} alt="Close" className="drawer-handle-icon" />
      </button>

      {/* Stats and Clear button bar */}
      <div className="suggestions-actions-bar">
        <div className="suggestions-stats">
          {totalStats.clarity > 0 && (
            <span className="stat-badge clarity">
              <img src={searchIcon} alt="" className="stat-icon" />
              {totalStats.clarity}
            </span>
          )}
          {totalStats.rigor > 0 && (
            <span className="stat-badge rigor">
              <img src={sigmaIcon} alt="" className="stat-icon" />
              {totalStats.rigor}
            </span>
          )}
          {totalStats.ethics > 0 && <span className="stat-badge ethics">⚖️ {totalStats.ethics}</span>}
        </div>
        {hasRun && suggestions.length > 0 && (
          <button
            className="clear-suggestions-btn"
            onClick={handleClearSuggestions}
            title="Clear all suggestions"
          >
            <img src={trashIcon} alt="" className="clear-icon" />
            Clear
          </button>
        )}
      </div>

      {/* Severity Statistics */}
      {hasRun && (severityStats.error > 0 || severityStats.warning > 0 || severityStats.info > 0) && (
        <div className="severity-stats-bar">
          <div className="severity-stats">
            {severityStats.error > 0 && (
              <span className="severity-stat-badge error">
                <img src={redIcon} alt="" className="severity-stat-icon" />
                <span className="severity-stat-label">Errors:</span>
                <span className="severity-stat-count">{severityStats.error}</span>
              </span>
            )}
            {severityStats.warning > 0 && (
              <span className="severity-stat-badge warning">
                <img src={yellowIcon} alt="" className="severity-stat-icon" />
                <span className="severity-stat-label">Warnings:</span>
                <span className="severity-stat-count">{severityStats.warning}</span>
              </span>
            )}
            {severityStats.info > 0 && (
              <span className="severity-stat-badge info">
                <img src={blueIcon} alt="" className="severity-stat-icon" />
                <span className="severity-stat-label">Info:</span>
                <span className="severity-stat-count">{severityStats.info}</span>
              </span>
            )}
          </div>
        </div>
      )}

      {/* Agent Selection Controls */}
      <div className="agent-controls">
        <div className="agent-selection">
          <button
            className={`agent-btn ${selectedAgent === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedAgent('all')}
          >
            <img src={channelIcon} alt="" className="agent-icon" />
            <span className="agent-name">All Agents</span>
          </button>
          <button
            className={`agent-btn ${selectedAgent === 'clarity' ? 'active' : ''}`}
            onClick={() => setSelectedAgent('clarity')}
          >
            <img src={searchIcon} alt="" className="agent-icon" />
            <span className="agent-name">Clarity</span>
          </button>
          <button
            className={`agent-btn ${selectedAgent === 'rigor' ? 'active' : ''}`}
            onClick={() => setSelectedAgent('rigor')}
          >
            <img src={sigmaIcon} alt="" className="agent-icon" />
            <span className="agent-name">Rigor</span>
          </button>
        </div>
        <button
          className="run-agent-btn"
          onClick={handleRunAgent}
          disabled={isLoading || !latexContent || latexContent.trim().length < 50}
        >
          <span className="run-icon">▶</span>
          <span>Run Analysis</span>
        </button>
      </div>

      <div className="suggestions-list">
        {isLoading ? (
          <div className="loading-state">
            <div className="quantum-dots">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="quantum-container"
                  style={{
                    animationDelay: `${i * 0.3}s`
                  }}
                >
                  <div className="quantum-dot"></div>
                </div>
              ))}
            </div>
            <p>Pontificating...</p>
            <p className="hint">this may take some time</p>
          </div>
        ) : error ? (
          <div className="error-state">
            <p className="error-text">⚠️ {error}</p>
            <button onClick={handleRefreshSuggestions} className="retry-btn">
              Try Again
            </button>
          </div>
        ) : !hasRun ? (
          <div className="no-suggestions">
            <p>Ready to analyze</p>
            <p className="hint">Select an agent above and click "Run Analysis" to get AI-powered feedback</p>
          </div>
        ) : suggestions.length === 0 ? (
          <div className="no-suggestions">
            <p>No suggestions found</p>
            <p className="hint">Your content looks good! Try writing more or selecting a different agent.</p>
          </div>
        ) : (
          suggestions.map((section, idx) => {
            const isExpanded = expandedSection === section.section
            console.log('Rendering section:', section.section, 'expandedSection:', expandedSection, 'isExpanded:', isExpanded)
            return (
              <div key={idx} className="suggestion-section">
                <div
                  className="section-header"
                  onClick={() => toggleSection(section.section)}
                >
                  <span className={`section-icon ${isExpanded ? 'expanded' : ''}`}>
                    <img src={angleRightIcon} alt="" className="section-arrow" />
                  </span>
                  <span className="section-name">{section.section}</span>
                  <span className="section-line">Line {section.line}</span>
                </div>

                {isExpanded && (
                <div className="section-content">
                  {section.suggestions.map((suggestionGroup, gIdx) => (
                    <div key={gIdx} className="suggestion-group">
                      <div className="suggestion-type">
                        <span className="type-icon">
                          {(() => {
                            const iconData = getSuggestionIcon(suggestionGroup.type);
                            return iconData.type === 'svg' ? (
                              <img src={iconData.icon} alt="" className="type-icon-svg" />
                            ) : (
                              iconData.icon
                            );
                          })()}
                        </span>
                        <span className="type-name">
                          {suggestionGroup.type.charAt(0).toUpperCase() + suggestionGroup.type.slice(1)}
                        </span>
                        <span className="type-count">({suggestionGroup.count})</span>
                      </div>

                      <div className="suggestion-items">
                        {suggestionGroup.items.map((item, iIdx) => {
                          const severityBadge = getSeverityBadge(item.severity)
                          const itemId = `${idx}-${gIdx}-${iIdx}`
                          const isExplanationExpanded = expandedExplanations.has(itemId)
                          return (
                            <div key={iIdx} className={`suggestion-item ${severityBadge.class}`}>
                              <div className="item-header">
                                <div className="severity-info">
                                  <span className="severity-badge">
                                    <img src={severityBadge.icon} alt={severityBadge.label} className="severity-icon" />
                                    {severityBadge.label}
                                  </span>
                                  {item.severity_score !== undefined && item.severity_score !== null && (
                                    <span className="severity-score">
                                      {item.severity_score.toFixed(2)}
                                    </span>
                                  )}
                                </div>
                                <span className="item-line">Line {item.line}</span>
                              </div>
                              <div className="item-text">
                                <span className="item-label">Issue:</span> {item.text}
                              </div>
                              {item.explanation && (
                                <>
                                  <button
                                    className="explanation-toggle"
                                    onClick={() => toggleExplanation(itemId)}
                                  >
                                    {isExplanationExpanded ? '▼' : '▶'} Explanation
                                  </button>
                                  {isExplanationExpanded && (
                                    <div className="item-explanation">{item.explanation}</div>
                                  )}
                                </>
                              )}
                              {item.suggested_fix && (
                                <div className="item-fix">
                                  {item.suggested_fix}
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default SuggestionsPanel
