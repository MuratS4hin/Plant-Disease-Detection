import { useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/predict'

function App() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [output, setOutput] = useState<string>('')
  const [error, setError] = useState<string>('')

  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null
    setSelectedImage(file)
    setOutput('')
    setError('')
  }

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragActive(false)
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragActive(false)

    const droppedFile = event.dataTransfer.files?.[0] ?? null
    if (droppedFile && droppedFile.type.startsWith('image/')) {
      setSelectedImage(droppedFile)
      setOutput('')
      setError('')
    } else {
      setError('Please drop a valid image file.')
    }
  }

  const handleScan = async () => {
    if (!selectedImage) {
      setError('Please select an image first.')
      return
    }

    setIsLoading(true)
    setError('')
    setOutput('')

    try {
      const formData = new FormData()
      formData.append('image', selectedImage)

      const response = await fetch(API_URL, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }

      const contentType = response.headers.get('content-type') ?? ''

      if (contentType.includes('application/json')) {
        const data = await response.json()
        setOutput(JSON.stringify(data, null, 2))
      } else {
        const text = await response.text()
        setOutput(text)
      }
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : 'Something went wrong while sending the request.'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="app">
      <section className="card">
        <h1 className="title">scan your sick plant.</h1>

        <div
          className={`upload-box ${dragActive ? 'drag-active' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <p className="upload-text">Yüklemek İçin Dosyayı Sürükle</p>
          <div className="upload-icon" aria-hidden="true">
            ☁️
          </div>

          <label className="browse-button" htmlFor="plant-image-input">
            Gözat
          </label>
          <input
            id="plant-image-input"
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            className="file-input"
          />

          <p className="upload-note">(En Fazla 10 MB, Resim Dosyası Olmalı)</p>
        </div>

        <button className="scan-button" onClick={handleScan} disabled={isLoading}>
          {isLoading ? 'Scanning...' : 'Send for Scan'}
        </button>

        {selectedImage && <p className="selected-file">Selected: {selectedImage.name}</p>}

        {error && <p className="error-text">{error}</p>}

        {output && (
          <div className="output-box">
            <h2>Output</h2>
            <pre>{output}</pre>
          </div>
        )}
      </section>
    </main>
  )
}

export default App
