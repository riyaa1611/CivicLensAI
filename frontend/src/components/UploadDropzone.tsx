import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import { uploadBill } from '../services/api'
import type { UploadResponse } from '../types'

interface Props {
  onSuccess?: (result: UploadResponse) => void
}

type Status = 'idle' | 'uploading' | 'success' | 'error'

export default function UploadDropzone({ onSuccess }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [result, setResult] = useState<UploadResponse | null>(null)
  const [error, setError] = useState<string>('')

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) {
      setFile(accepted[0])
      setStatus('idle')
      setError('')
      setResult(null)
      // Pre-fill title from filename
      const name = accepted[0].name
        .replace(/\.[^.]+$/, '')
        .replace(/[_-]+/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase())
      setTitle(name)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'text/html': ['.html'],
    },
    maxFiles: 1,
    maxSize: 20 * 1024 * 1024, // 20MB
  })

  const handleUpload = async () => {
    if (!file) return
    setStatus('uploading')
    setError('')
    try {
      const res = await uploadBill(file, title || undefined)
      setResult(res)
      setStatus('success')
      onSuccess?.(res)
    } catch (e: any) {
      setStatus('error')
      setError(e.response?.data?.detail || 'Upload failed. Please try again.')
    }
  }

  const reset = () => {
    setFile(null)
    setTitle('')
    setStatus('idle')
    setError('')
    setResult(null)
  }

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={clsx(
          'relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200',
          isDragActive && !isDragReject && 'border-brand-400 bg-brand-50/50',
          isDragReject && 'border-red-400 bg-red-50/50',
          !isDragActive && 'border-gray-200 hover:border-brand-300 hover:bg-brand-50/20',
          status === 'success' && 'border-green-400 bg-green-50/30'
        )}
      >
        <input {...getInputProps()} />

        {status === 'success' && result ? (
          <div className="flex flex-col items-center gap-3">
            <CheckCircle className="w-12 h-12 text-green-500" />
            <div>
              <p className="font-semibold text-green-700">{result.title}</p>
              <p className="text-sm text-gray-500 mt-1">{result.message}</p>
            </div>
            <button onClick={(e) => { e.stopPropagation(); reset() }}
                    className="btn-secondary text-sm mt-2">
              Upload another
            </button>
          </div>
        ) : file ? (
          <div className="flex flex-col items-center gap-3">
            <FileText className="w-12 h-12 text-brand-500" />
            <div>
              <p className="font-medium text-gray-700">{file.name}</p>
              <p className="text-sm text-gray-400">
                {(file.size / 1024).toFixed(0)} KB · Click to change
              </p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className={clsx('w-12 h-12', isDragActive ? 'text-brand-500' : 'text-gray-300')} />
            <div>
              <p className="font-medium text-gray-600">
                {isDragActive ? 'Drop it here' : 'Drag & drop a document'}
              </p>
              <p className="text-sm text-gray-400 mt-1">
                PDF, TXT, or HTML · Max 20MB
              </p>
            </div>
            <span className="btn-secondary text-sm">Browse files</span>
          </div>
        )}
      </div>

      {/* Title input */}
      {file && status !== 'success' && (
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Document title <span className="text-gray-400">(optional)</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter a title for this document"
              className="input-field"
            />
          </div>

          {/* Error */}
          {status === 'error' && error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 rounded-lg text-red-700 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handleUpload}
              disabled={status === 'uploading'}
              className="btn-primary flex-1"
            >
              {status === 'uploading' ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Uploading & Processing...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Upload & Index
                </>
              )}
            </button>
            <button onClick={reset} className="btn-secondary px-3">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
