import { BookOpen, List, Tag, ExternalLink } from 'lucide-react'
import type { Policy } from '../types'

interface Props {
  policy: Policy
}

export default function SummaryPanel({ policy }: Props) {
  const summaryLines = policy.summary
    ? policy.summary
        .split('\n')
        .map((l) => l.trim())
        .filter((l) => l.length > 0)
    : ['No summary available.']

  return (
    <div className="space-y-6">
      {/* Summary */}
      <section className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <BookOpen className="w-5 h-5 text-brand-600" />
          <h2 className="font-semibold text-gray-900">AI Summary</h2>
        </div>
        <ul className="space-y-3">
          {summaryLines.map((line, i) => (
            <li key={i} className="flex gap-3">
              <span className="w-6 h-6 rounded-full bg-brand-50 text-brand-600 text-xs
                               flex items-center justify-center font-semibold flex-shrink-0 mt-0.5">
                {i + 1}
              </span>
              <span className="text-sm text-gray-700 leading-relaxed">
                {line.replace(/^[•\-]\s*/, '')}
              </span>
            </li>
          ))}
        </ul>
      </section>

      {/* Key clauses */}
      {policy.key_clauses.length > 0 && (
        <section className="card p-6">
          <div className="flex items-center gap-2 mb-4">
            <List className="w-5 h-5 text-brand-600" />
            <h2 className="font-semibold text-gray-900">Key Provisions</h2>
          </div>
          <ul className="space-y-2">
            {policy.key_clauses.map((clause, i) => (
              <li key={i} className="flex gap-3 py-2 border-b border-gray-50 last:border-0">
                <span className="w-1.5 h-1.5 rounded-full bg-brand-400 flex-shrink-0 mt-2" />
                <span className="text-sm text-gray-700 leading-relaxed">{clause}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Tags */}
      {policy.tags.length > 0 && (
        <section className="card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Tag className="w-4 h-4 text-brand-600" />
            <h2 className="font-semibold text-gray-900 text-sm">Impact Areas</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {policy.tags.map((tag) => (
              <span key={tag} className="tag capitalize">{tag}</span>
            ))}
          </div>
        </section>
      )}

      {/* Source link */}
      {policy.link && !policy.link.startsWith('upload://') && (
        <a
          href={policy.link}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary w-full justify-center"
        >
          <ExternalLink className="w-4 h-4" />
          View Original Document
        </a>
      )}
    </div>
  )
}
