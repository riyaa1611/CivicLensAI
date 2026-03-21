import { Link } from 'react-router-dom'
import { ExternalLink, Calendar, Tag } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import clsx from 'clsx'
import type { Policy } from '../types'

interface Props {
  policy: Policy
}

const SOURCE_STYLES: Record<string, string> = {
  PRS: 'tag-source-prs',
  PIB: 'tag-source-pib',
  Gazette: 'tag-source-gazette',
  Upload: 'tag-source-upload',
}

export default function PolicyCard({ policy }: Props) {
  const sourceStyle = SOURCE_STYLES[policy.source] || 'tag'
  const dateLabel = policy.date
    ? format(parseISO(policy.date), 'MMM d, yyyy')
    : 'Unknown date'

  const summaryPreview = policy.summary
    ? policy.summary.split('\n')[0].replace(/^•\s*/, '')
    : 'No summary available.'

  return (
    <Link
      to={`/policy/${policy.id}`}
      className="card p-5 flex flex-col gap-3 group animate-fade-in"
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={clsx('tag text-xs', sourceStyle)}>{policy.source}</span>
          <span className="flex items-center gap-1 text-xs text-gray-400">
            <Calendar className="w-3 h-3" />
            {dateLabel}
          </span>
        </div>
        {policy.link && !policy.link.startsWith('upload://') && (
          <a
            href={policy.link}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-gray-300 hover:text-brand-500 transition-colors flex-shrink-0"
            title="View original"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        )}
      </div>

      {/* Title */}
      <h3 className="font-semibold text-gray-900 text-base leading-snug
                     group-hover:text-brand-700 transition-colors line-clamp-2">
        {policy.title}
      </h3>

      {/* Summary preview */}
      <p className="text-sm text-gray-500 leading-relaxed line-clamp-2">
        {summaryPreview}
      </p>

      {/* Tags */}
      {policy.tags.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap mt-1">
          <Tag className="w-3 h-3 text-gray-300" />
          {policy.tags.slice(0, 4).map((tag) => (
            <span key={tag} className="tag text-xs">
              {tag}
            </span>
          ))}
          {policy.tags.length > 4 && (
            <span className="text-xs text-gray-400">+{policy.tags.length - 4}</span>
          )}
        </div>
      )}
    </Link>
  )
}
