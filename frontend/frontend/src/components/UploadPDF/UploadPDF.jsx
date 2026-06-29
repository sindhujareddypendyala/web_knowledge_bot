import { useRef, useState } from 'react'
import { FiCheckCircle, FiFileText, FiUploadCloud } from 'react-icons/fi'
import { uploadPDF } from '../../services/api.js'

export default function UploadPDF({ onUploaded }) {
  const inputRef = useRef(null)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('idle')
  const [fileName, setFileName] = useState('')

  async function handleFile(file) {
    if (!file || (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf'))) {
      setStatus('error')
      return
    }
    setFileName(file.name)
    setStatus('uploading')
    setProgress(5)
    
    try {
      await uploadPDF(file, (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          setProgress(percentCompleted)
        }
      })
      setStatus('success')
      onUploaded?.(file)
    } catch (err) {
      console.error('Failed to upload PDF:', err)
      setStatus('error')
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload PDF documentation"
      onClick={() => inputRef.current?.click()}
      onKeyDown={(event) => event.key === 'Enter' && inputRef.current?.click()}
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault()
        handleFile(event.dataTransfer.files[0])
      }}
      className="focus-ring rounded-lg border border-dashed border-blue-400/60 bg-blue-500/10 p-4 text-center transition hover:bg-blue-500/15"
    >
      <input ref={inputRef} type="file" accept="application/pdf" className="sr-only" onChange={(event) => handleFile(event.target.files[0])} />
      <div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-blue-600 text-xl text-white">
        {status === 'success' ? <FiCheckCircle aria-hidden="true" /> : <FiUploadCloud aria-hidden="true" />}
      </div>
      <p className="mt-3 font-semibold text-white">{status === 'success' ? 'PDF Uploaded Successfully' : 'Drag and drop PDF documentation'}</p>
      <p className="mt-1 text-sm text-slate-400">{fileName || 'Choose File - PDF only'}</p>
      {status === 'uploading' && (
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
          <div className="h-full rounded-full bg-blue-500 transition-all" style={{ width: `${progress}%` }} />
        </div>
      )}
      {status === 'error' && (
        <p className="mt-3 text-sm text-rose-300">
          <FiFileText className="inline" aria-hidden="true" />
          Upload failed. Please ensure the file is a valid PDF and the backend is reachable.
        </p>
      )}
    </div>
  )
}
