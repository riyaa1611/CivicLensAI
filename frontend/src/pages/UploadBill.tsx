import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, Zap, Search, CheckCircle } from 'lucide-react'
import UploadDropzone from '../components/UploadDropzone'
import type { UploadResponse } from '../types'

export default function UploadBill() {
  const navigate = useNavigate()
  const [result, setResult] = useState<UploadResponse | null>(null)

  const handleSuccess = (res: UploadResponse) => {
    setResult(res)
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10">
      {/* Header */}
      <div className="text-center mb-8 animate-fade-in">
        <div className="w-12 h-12 rounded-2xl bg-brand-600 flex items-center justify-center mx-auto mb-4">
          <Upload className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload a Bill</h1>
        <p className="text-gray-500">
          Upload any government document, bill, or policy PDF to analyze it
          with AI and make it searchable.
        </p>
      </div>

      {/* Upload card */}
      <div className="card p-6 mb-6">
        <UploadDropzone onSuccess={handleSuccess} />
      </div>

      {/* Success action */}
      {result && result.status === 'processing' && (
        <div className="card p-6 border-green-100 bg-green-50/30 animate-slide-up">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-green-800 mb-1">{result.title}</h3>
              <p className="text-sm text-green-600 mb-4">{result.message}</p>
              <div className="flex gap-3">
                <button
                  onClick={() => navigate(`/policy/${result.policy_id}`)}
                  className="btn-primary text-sm"
                >
                  <FileText className="w-4 h-4" />
                  View Policy
                </button>
                <button
                  onClick={() =>
                    navigate(`/ask?q=${encodeURIComponent(`Tell me about ${result.title}`)}`)
                  }
                  className="btn-secondary text-sm"
                >
                  <Search className="w-4 h-4" />
                  Ask about it
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* How it works */}
      <div className="mt-8 card p-6">
        <h2 className="font-semibold text-gray-900 mb-4 text-sm">What happens after upload?</h2>
        <div className="space-y-3">
          {[
            {
              icon: FileText,
              title: 'Text extraction',
              desc: 'PDF text is extracted using PyMuPDF for high quality parsing',
            },
            {
              icon: Zap,
              title: 'AI analysis',
              desc: 'LLM generates a 3-point summary and identifies key provisions',
            },
            {
              icon: Search,
              title: 'Vector indexing',
              desc: 'Document chunks are embedded with BAAI/bge-large-en and stored for search',
            },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-brand-50 flex items-center justify-center flex-shrink-0">
                <Icon className="w-4 h-4 text-brand-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">{title}</p>
                <p className="text-xs text-gray-400 mt-0.5">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
