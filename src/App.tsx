import { useEffect, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || '/predict'
const IMAGE_MIME_PREFIX = 'image/'

const isImageFile = (file: File) => file.type.startsWith(IMAGE_MIME_PREFIX)

function App() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [dragActive, setDragActive] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [popupDescription, setPopupDescription] = useState<string>('')
  const [popupConfidence, setPopupConfidence] = useState<number>(0)
  const [isPopupOpen, setIsPopupOpen] = useState(false)

  const resetMessages = () => {
    setError('')
    setPopupDescription('')
    setPopupConfidence(0)
    setIsPopupOpen(false)
  }

  const setImageAndReset = (file: File | null) => {
    setSelectedImage(file)
    resetMessages()
  }

  useEffect(() => {
    if (!selectedImage) {
      setPreviewUrl('')
      return
    }

    const objectUrl = URL.createObjectURL(selectedImage)
    setPreviewUrl(objectUrl)

    return () => {
      URL.revokeObjectURL(objectUrl)
    }
  }, [selectedImage])

  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null

    if (!file) {
      setImageAndReset(null)
      return
    }

    if (!isImageFile(file)) {
      setSelectedImage(null)
      setError('Please select a valid image file.')
      setPopupDescription('')
      setPopupConfidence(0)
      setIsPopupOpen(false)
      return
    }

    setImageAndReset(file)
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
    if (!droppedFile || !isImageFile(droppedFile)) {
      setError('Please drop a valid image file.')
      setPopupDescription('')
      setPopupConfidence(0)
      return
    }

    setImageAndReset(droppedFile)
  }

  const handleScan = async () => {
    if (!selectedImage) {
      setError('Please select an image first.')
      return
    }

    setIsLoading(true)
    resetMessages()

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
        const description = data?.prediction?.description
        const confidence = Math.round(data?.prediction?.confidence * 100) / 100

        if (typeof description !== 'string' || description.trim() === '') {
          throw new Error('Description was not found in the API response.')
        }

        setPopupDescription(description)
        setPopupConfidence(confidence)
        setIsPopupOpen(true)
      } else {
        throw new Error('Unexpected response format from the API.')
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
        <h1 className="title">Bitki Hastalıklarının Tespiti</h1>

        <div
          className={`upload-box ${dragActive ? 'drag-active' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {previewUrl ? (
            <img src={previewUrl} alt="Selected plant" className="upload-preview" />
          ) : (
            <>
              <p className="upload-text">Yüklemek İçin Dosyayı Sürükle</p>
              <div className="upload-icon" aria-hidden="true">
                ☁️
              </div>
            </>
          )}

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
          {isLoading ? 'Taranıyor...' : 'Taramak için Tıklayınız'}
        </button>

        {/* {selectedImage && <p className="selected-file">Selected: {selectedImage.name}</p>} */}

        {error && <p className="error-text">{error}</p>}
      </section>

      {isPopupOpen && (
        <div className="popup-overlay" onClick={() => setIsPopupOpen(false)}>
          <div className="popup-card" onClick={(event) => event.stopPropagation()}>
            <button className="popup-close" onClick={() => setIsPopupOpen(false)} type="button">
              ×
            </button>
            <p className="popup-description">Tahmin Edilen Sınıf: {popupDescription}</p>
            <p className="popup-description">Güven Skoru: %{popupConfidence*100}</p>
          </div>
        </div>
      )}
    </main>
  )
}

export default App
