import { useState, useEffect } from 'react'
import axios from 'axios'
import './FileManager.css'
import trashIcon from './assets/icons/trash-alt.svg'

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function FileManager({ onLoadTexFile }) {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    loadFiles()
  }, [])

  const loadFiles = async () => {
    try {
      const response = await axios.get(`${API_URL}/list-files`)
      if (response.data.success) {
        setFiles(response.data.files)
      }
    } catch (error) {
      console.error('Error loading files:', error)
    }
  }

  const handleFileUpload = async (event) => {
    const fileList = event.target.files
    if (!fileList || fileList.length === 0) return

    setUploading(true)
    setMessage('')

    try {
      for (const file of fileList) {
        const formData = new FormData()
        formData.append('file', file)

        const response = await axios.post(`${API_URL}/upload-file`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })

        if (!response.data.success) {
          setMessage(`Error uploading ${file.name}: ${response.data.error}`)
          break
        }
      }

      setMessage('Files uploaded successfully!')
      await loadFiles()
      setTimeout(() => setMessage(''), 3000)
    } catch (error) {
      setMessage(`Error: ${error.message}`)
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const handleDeleteFile = async (filename) => {
    if (!confirm(`Delete ${filename}?`)) return

    try {
      const response = await axios.delete(`${API_URL}/delete-file/${filename}`)

      if (response.data.success) {
        setMessage(`${filename} deleted`)
        await loadFiles()
        setTimeout(() => setMessage(''), 3000)
      } else {
        setMessage(`Error: ${response.data.error}`)
      }
    } catch (error) {
      setMessage(`Error: ${error.message}`)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const getFileIcon = (type) => {
    const icons = {
      '.png': '🖼️',
      '.jpg': '🖼️',
      '.jpeg': '🖼️',
      '.pdf': '📄',
      '.bib': '📚',
      '.sty': '🎨',
      '.cls': '🎨',
      '.tex': '📝',
    }
    return icons[type] || '📎'
  }

  const handleLoadTexFile = async (filename) => {
    try {
      // Fetch the .tex file content from the project directory
      const response = await axios.get(`${API_URL}/get-file/${filename}`)

      if (response.data.success) {
        onLoadTexFile(response.data.content, filename)
        setMessage(`Loaded ${filename} into editor`)
        setTimeout(() => setMessage(''), 3000)
      } else {
        setMessage(`Error: ${response.data.error}`)
      }
    } catch (error) {
      setMessage(`Error loading file: ${error.message}`)
    }
  }

  return (
    <div className="file-manager">
      <div className="file-manager-header">
        <h3>Project Directory</h3>
      </div>

      {message && (
        <div className={`file-message ${message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      {uploading && <div className="file-uploading">Uploading...</div>}

      <div className="file-list">
        {files.length === 0 ? (
          <div className="no-files">
            <p>No files uploaded yet</p>
            <p className="hint">Upload images, .bib, .sty files, etc.</p>
          </div>
        ) : (
          files.map((file) => (
            <div key={file.name} className="file-item">
              <span className="file-icon">{getFileIcon(file.type)}</span>
              <div className="file-info">
                <div className="file-name">{file.name}</div>
                <div className="file-size">{formatFileSize(file.size)}</div>
              </div>
              <div className="file-actions">
                {file.type === '.tex' && (
                  <button
                    className="load-file-btn"
                    onClick={() => handleLoadTexFile(file.name)}
                    title="Load into editor"
                  >
                    📂
                  </button>
                )}
                <button
                  className="delete-file-btn"
                  onClick={() => handleDeleteFile(file.name)}
                  title="Delete file"
                >
                  <img src={trashIcon} alt="Delete" className="delete-icon" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="file-manager-footer">
        <label htmlFor="files-upload" className="upload-files-btn">
          Upload Files
        </label>
        <input
          id="files-upload"
          type="file"
          multiple
          onChange={handleFileUpload}
          style={{ display: 'none' }}
          accept=".png,.jpg,.jpeg,.pdf,.bib,.sty,.cls,.tex"
        />
      </div>
    </div>
  )
}

export default FileManager
