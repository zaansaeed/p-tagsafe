import { useEffect, useRef, useState } from 'react'
import './App.css'

const PAGES = {
  IMAGE: 'image',
  TEXT: 'text',
}

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'
const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/webp']
const initialInsightsState = {
  tags: [],
  generatedDescription: '',
  isChecking: false,
  error: '',
}

const extractNiceClass = (label = '') => {
  const match = label.match(/Class\s*(\d+)/i)
  return match ? match[1] : ''
}

const InsightsPanel = ({
  analysis,
  analysisTextLabel,
  placeholder,
  onCheck,
  checkDisabled,
  checkState,
}) => {
  const [copySuccess, setCopySuccess] = useState(false)

  const handleCopyTags = () => {
    const tagText = checkState.tags.join(', ')
    navigator.clipboard.writeText(tagText).then(() => {
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    }).catch(err => {
      console.error('Failed to copy:', err)
    })
  }

  if (!analysis) {
    return (
      <div className="placeholder-panel">
        <p>{placeholder}</p>
      </div>
    )
  }

  return (
    <div className="results-stack">
      <div className="stat-block">
        <p className="stat-heading">Nice Class</p>
        <div className="stat-card">
          <p className="stat-value">
            {analysis?.niceClassLabel || 'Processing…'}
          </p>
        </div>
      </div>
      <div className="stat-block">
        <p className="stat-heading">{analysisTextLabel}</p>
        <div className="stat-card">
          <p className="extracted-text">
            {analysis?.text || `No ${analysisTextLabel.toLowerCase()} available.`}
          </p>
        </div>
      </div>
      <button
        type="button"
        className="check-btn"
        onClick={onCheck}
        disabled={checkDisabled}
      >
        {checkState.isChecking ? 'Checking…' : 'Check'}
      </button>
      {checkState.error && <p className="error-text">{checkState.error}</p>}
      {checkState.tags.length > 0 && (
        <div className="safe-terms">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ margin: 0 }}>Non-trademark Terms</h3>
            <button
              type="button"
              onClick={handleCopyTags}
              style={{
                padding: '0.5rem 1rem',
                fontSize: '0.875rem',
                fontWeight: '500',
                backgroundColor: copySuccess ? '#10b981' : '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => !copySuccess && (e.target.style.backgroundColor = '#2563eb')}
              onMouseLeave={(e) => !copySuccess && (e.target.style.backgroundColor = '#3b82f6')}
            >
              {copySuccess ? '✓ Copied!' : 'Copy All'}
            </button>
          </div>
          <div className="chip-grid">
            {checkState.tags.map((term) => (
              <span className="chip" key={term}>
                {term}
              </span>
            ))}
          </div>
          <p style={{
            marginTop: '1rem',
            fontSize: '0.75rem',
            color: '#6b7280',
            fontStyle: 'italic',
            lineHeight: '1.4'
          }}>
            Disclaimer: These terms are AI-generated suggestions. We are not responsible for any trademark, copyright, or intellectual property issues arising from the use of these terms. Please conduct your own due diligence before use.
          </p>
        </div>
      )}
      {checkState.generatedDescription && (
        <div className="description-block">
          <p className="stat-heading">Example Product Description</p>
          <div className="description-card">
            <p className="description-text">{checkState.generatedDescription}</p>
          </div>
        </div>
      )}
    </div>
  )
}

const ImagePage = () => {
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [isClassifying, setIsClassifying] = useState(false)
  const [classifyError, setClassifyError] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [checkState, setCheckState] = useState(initialInsightsState)
  const fileInputRef = useRef(null)

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  const resetInsights = () => {
    setAnalysis(null)
    setClassifyError('')
    setCheckState(initialInsightsState)
  }

  const handleFileSelection = (files) => {
    const file = files?.[0]
    if (!file) return

    const isTypeValid =
      ACCEPTED_TYPES.includes(file.type) ||
      (file.type === '' &&
        /\.(png|jpe?g|webp)$/i.test(file.name || file?.path || ''))

    if (!isTypeValid) {
      alert('Please upload a PNG, JPG, JPEG, or WebP image.')
      return
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    resetInsights()
  }

  const handleInputChange = (event) => {
    handleFileSelection(event.target.files)
    event.target.value = ''
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    handleFileSelection(event.dataTransfer.files)
  }

  const handleDragOver = (event) => {
    event.preventDefault()
    if (!isDragging) setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleRemove = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setSelectedFile(null)
    setPreviewUrl('')
    resetInsights()
  }

  const openFilePicker = () => {
    fileInputRef.current?.click()
  }

  const handleClassify = async () => {
    if (!selectedFile) return
    setIsClassifying(true)
    setClassifyError('')
    setAnalysis(null)
    setCheckState(initialInsightsState)

    const formData = new FormData()
    formData.append('image', selectedFile)

    try {
      const response = await fetch(`${API_BASE}/parser/v1/parse-image`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || 'Unable to classify image.')
      }

      const payload = await response.json()
      const result = payload?.result || {}
      const niceClassLabel = result.object_type || 'Unavailable'
      const niceClass = extractNiceClass(niceClassLabel)

      setAnalysis({
        niceClassLabel,
        niceClass,
        text: result.text?.trim() || '',
        description: result.description?.trim() || '',
      })
    } catch (error) {
      setClassifyError(error.message || 'Classification failed. Try again.')
    } finally {
      setIsClassifying(false)
    }
  }

  const handleCheckTerms = async () => {
    if (!analysis?.text || !selectedFile) {
      setCheckState((prev) => ({
        ...prev,
        error: 'Classify an image first to extract text and Nice Class.',
      }))
      return
    }

    setCheckState({
      tags: [],
      generatedDescription: '',
      isChecking: true,
      error: '',
    })

    const formData = new FormData()
    formData.append('nice_class', analysis.niceClass || '0')
    formData.append('product_text', analysis.text)
    formData.append('image_file', selectedFile)

    try {
      const response = await fetch(`${API_BASE}/tags/generate`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || 'Failed to generate tag suggestions.')
      }

      const data = await response.json()
      const tagList = data?.tags || []

      let generatedDescription = ''
      if (tagList.length) {
        try {
          const descResponse = await fetch(
            `${API_BASE}/compose/safe-description`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                safe_phrases: tagList,
                title: analysis.text?.slice(0, 160) || '',
              }),
            },
          )
          if (descResponse.ok) {
            const descData = await descResponse.json()
            generatedDescription =
              descData?.safe_listing_description?.trim() || ''
          }
        } catch (descError) {
          console.error('Description generation failed', descError)
        }
      }

      setCheckState({
        tags: tagList,
        generatedDescription,
        isChecking: false,
        error: '',
      })
    } catch (error) {
      setCheckState({
        tags: [],
        generatedDescription: '',
        isChecking: false,
        error: error.message || 'Failed to generate suggestions.',
      })
    }
  }

  return (
    <section className="image-page">
      <div className="drop-stack">
        <h2 className="stack-title">Upload Your Product Photo Below</h2>
        <div
          className={`drop-area ${isDragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".png,.jpg,.jpeg,.webp"
            ref={fileInputRef}
            className="visually-hidden"
            onChange={handleInputChange}
          />
          <div className="preview-frame">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Uploaded preview"
                className="preview"
              />
            ) : (
              <span className="preview-watermark">
                Your uploaded image will appear here
              </span>
            )}
          </div>
          <p className="drop-hint">
            Drag and drop your product photo here (PNG, JPG, JPEG, or WebP) or click to
            browse
          </p>
          <button
            type="button"
            className="upload-btn"
            onClick={openFilePicker}
          >
            {previewUrl ? 'Replace Image' : 'Upload Photo'}
          </button>
          {previewUrl && (
            <button type="button" className="remove-btn" onClick={handleRemove}>
              Remove Image
            </button>
          )}
        </div>
        <button
          type="button"
          className="classify-btn"
          onClick={handleClassify}
          disabled={!selectedFile || isClassifying}
        >
          {isClassifying ? 'Classifying…' : 'Classify'}
        </button>
        {classifyError && <p className="error-text">{classifyError}</p>}
      </div>
      <div className="results-panel">
        <InsightsPanel
          analysis={analysis}
          analysisTextLabel="Text on Uploaded Product Image"
          placeholder="Upload and classify a product image to detect Nice Class assignments, extract visible text, and surface trademark-safe wording."
          onCheck={handleCheckTerms}
          checkDisabled={
            !analysis || !selectedFile || isClassifying || checkState.isChecking
          }
          checkState={checkState}
        />
      </div>
    </section>
  )
}

const TextPage = () => {
  const [description, setDescription] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [isClassifying, setIsClassifying] = useState(false)
  const [classifyError, setClassifyError] = useState('')
  const [checkState, setCheckState] = useState(initialInsightsState)

  const normalizedDescription = description.trim()

  const resetInsights = () => {
    setAnalysis(null)
    setClassifyError('')
    setCheckState(initialInsightsState)
  }

  const handleClassify = async () => {
    if (!normalizedDescription) {
      setClassifyError('Enter a product description to classify.')
      return
    }

    setIsClassifying(true)
    setClassifyError('')
    setAnalysis(null)
    setCheckState(initialInsightsState)

    try {
      const response = await fetch(`${API_BASE}/parser/v1/parse-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: normalizedDescription }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || 'Unable to classify description.')
      }

      const payload = await response.json()
      const result = payload?.result || {}
      const niceClassLabel = result.object_type || 'Unavailable'
      const niceClass =
        result.nice_class ?? extractNiceClass(niceClassLabel) ?? ''

      setAnalysis({
        niceClassLabel,
        niceClass,
        text: normalizedDescription,
      })
    } catch (error) {
      setClassifyError(error.message || 'Classification failed. Try again.')
    } finally {
      setIsClassifying(false)
    }
  }

  const handleCheckTerms = async () => {
    if (!analysis?.text) {
      setCheckState((prev) => ({
        ...prev,
        error: 'Classify your description first.',
      }))
      return
    }

    setCheckState({
      tags: [],
      generatedDescription: '',
      isChecking: true,
      error: '',
    })

    const formData = new FormData()
    formData.append('nice_class', analysis.niceClass || '0')
    formData.append('product_text', analysis.text)

    try {
      const response = await fetch(`${API_BASE}/tags/generate`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || 'Failed to generate tag suggestions.')
      }

      const data = await response.json()
      const tagList = data?.tags || []

      let generatedDescription = ''
      if (tagList.length) {
        try {
          const descResponse = await fetch(
            `${API_BASE}/compose/safe-description`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                safe_phrases: tagList,
                title: analysis.text?.slice(0, 160) || '',
              }),
            },
          )
          if (descResponse.ok) {
            const descData = await descResponse.json()
            generatedDescription =
              descData?.safe_listing_description?.trim() || ''
          }
        } catch (descError) {
          console.error('Description generation failed', descError)
        }
      }

      setCheckState({
        tags: tagList,
        generatedDescription,
        isChecking: false,
        error: '',
      })
    } catch (error) {
      setCheckState({
        tags: [],
        generatedDescription: '',
        isChecking: false,
        error: error.message || 'Failed to generate suggestions.',
      })
    }
  }

  const handleInputChange = (event) => {
    setDescription(event.target.value)
    if (analysis) {
      resetInsights()
    }
  }

  return (
    <section className="text-page">
      <div className="text-stack">
        <h2 className="stack-title">Describe Your Product</h2>
        <textarea
          className="description-input"
          placeholder="Paste or type the description you plan to publish. We'll classify it and check for safer terms."
          value={description}
          onChange={handleInputChange}
        />
        <button
          type="button"
          className="classify-btn"
          onClick={handleClassify}
          disabled={!normalizedDescription || isClassifying}
        >
          {isClassifying ? 'Classifying…' : 'Classify'}
        </button>
        {classifyError && <p className="error-text">{classifyError}</p>}
      </div>
      <div className="results-panel">
        <InsightsPanel
          analysis={analysis}
          analysisTextLabel="Inputted Product Description"
          placeholder="Enter a product description and classify it to detect Nice Class assignments and safer language."
          onCheck={handleCheckTerms}
          checkDisabled={!analysis || isClassifying || checkState.isChecking}
          checkState={checkState}
        />
      </div>
    </section>
  )
}

function App() {
  const [activePage, setActivePage] = useState(PAGES.IMAGE)
  const isImage = activePage === PAGES.IMAGE

  return (
    <div className="app">
      <header className="app-header">
        <h1>TagSafe</h1>
      </header>
      <main className="content">
        {isImage ? <ImagePage /> : <TextPage />}
      </main>
      <nav className="bottom-nav" aria-label="Primary">
        <button
          type="button"
          className={`nav-btn ${isImage ? 'active' : ''}`}
          onClick={() => setActivePage(PAGES.IMAGE)}
          aria-pressed={isImage}
        >
          Image
        </button>
        <button
          type="button"
          className={`nav-btn ${!isImage ? 'active' : ''}`}
          onClick={() => setActivePage(PAGES.TEXT)}
          aria-pressed={!isImage}
        >
          Text Description
        </button>
      </nav>
    </div>
  )
}

export default App
