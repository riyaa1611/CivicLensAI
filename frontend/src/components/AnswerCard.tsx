import { ExternalLink, Zap, TrendingDown, Clock } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { QueryResponse } from '../types'

interface Props {
  result: QueryResponse
  query: string
}

export default function AnswerCard({ result, query }: Props) {
  const { answer, sources, metrics, latency_ms } = result
  const hasCompression = !metrics.fallback && metrics.compression_ratio > 1.01

  return (
    <div className="space-y-4 animate-slide-up">
      {/* Answer */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
            <Zap className="w-3.5 h-3.5 text-white" />
          </div>
          <h3 className="font-semibold text-gray-900">CivicLens Answer</h3>
        </div>

        <div className="prose-civic text-sm leading-relaxed">
          <ReactMarkdown>{answer}</ReactMarkdown>
        </div>
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className="card p-5">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Sources used</h4>
          <div className="space-y-2">
            {sources.map((src, i) => (
              <div
                key={src.policy_id}
                className="flex items-center justify-between gap-3 py-2 border-b border-gray-50 last:border-0"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="w-5 h-5 rounded-full bg-brand-50 text-brand-600 text-xs
                                   flex items-center justify-center font-semibold flex-shrink-0">
                    {i + 1}
                  </span>
                  <span className="text-xs text-gray-600 truncate">{src.title}</span>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="tag text-xs">{src.source}</span>
                  <span className="text-xs text-gray-400">
                    {(src.score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Optimization metrics */}
      <div className="card p-4">
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Context Optimization
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <MetricPill
            label="Tokens In"
            value={metrics.original_tokens.toLocaleString()}
            icon={null}
          />
          <MetricPill
            label="Tokens Out"
            value={metrics.compressed_tokens.toLocaleString()}
            icon={hasCompression ? <TrendingDown className="w-3 h-3 text-green-500" /> : null}
            highlight={hasCompression}
          />
          <MetricPill
            label="Compression"
            value={hasCompression ? `${metrics.compression_ratio.toFixed(1)}×` : '—'}
            highlight={hasCompression}
          />
          <MetricPill
            label="Saved"
            value={hasCompression ? `${metrics.savings_percent.toFixed(0)}%` : '—'}
            highlight={hasCompression}
          />
        </div>
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-50">
          <span className="text-xs text-gray-400 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {latency_ms.toFixed(0)}ms total
          </span>
          <span className={`text-xs font-medium ${hasCompression ? 'text-green-600' : 'text-gray-400'}`}>
            {hasCompression ? 'Compression active' : metrics.status}
          </span>
        </div>
      </div>
    </div>
  )
}

function MetricPill({
  label,
  value,
  icon,
  highlight = false,
}: {
  label: string
  value: string
  icon?: React.ReactNode
  highlight?: boolean
}) {
  return (
    <div className={`rounded-lg p-2.5 ${highlight ? 'bg-green-50' : 'bg-gray-50'}`}>
      <div className="flex items-center gap-1 mb-0.5">
        {icon}
        <span className="text-xs text-gray-500">{label}</span>
      </div>
      <span className={`text-sm font-semibold ${highlight ? 'text-green-700' : 'text-gray-700'}`}>
        {value}
      </span>
    </div>
  )
}
