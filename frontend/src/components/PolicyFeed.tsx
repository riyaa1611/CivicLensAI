import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Filter, RefreshCw } from 'lucide-react'
import PolicyCard from './PolicyCard'
import { fetchPolicies } from '../services/api'

const SOURCES = ['All', 'PRS', 'PIB', 'Gazette', 'Upload']
const TAGS = [
  'All', 'citizens', 'startups', 'students', 'taxpayers',
  'healthcare', 'privacy', 'technology', 'business', 'education', 'finance',
]

// Cutoff dates for smart fallback
const RECENT_DAYS = 30
const FALLBACK_DATE = '2025-11-01'

function getRecentCutoff(): string {
  const d = new Date()
  d.setDate(d.getDate() - RECENT_DAYS)
  return d.toISOString().split('T')[0]
}

function CardSkeleton() {
  return (
    <div className="card p-5 flex flex-col gap-3">
      <div className="flex gap-2">
        <div className="skeleton h-5 w-12 rounded-full" />
        <div className="skeleton h-5 w-24 rounded-full" />
      </div>
      <div className="skeleton h-5 w-full" />
      <div className="skeleton h-4 w-4/5" />
      <div className="flex gap-1.5">
        <div className="skeleton h-4 w-16 rounded-full" />
        <div className="skeleton h-4 w-20 rounded-full" />
      </div>
    </div>
  )
}

export default function PolicyFeed() {
  const [source, setSource] = useState('All')
  const [tag, setTag] = useState('All')
  const [limit] = useState(20)

  const recentCutoff = getRecentCutoff()

  // Primary query: policies from the last 30 days
  const {
    data: recentPolicies,
    isLoading: isLoadingRecent,
    isError: isErrorRecent,
    refetch: refetchRecent,
    isFetching: isFetchingRecent,
  } = useQuery({
    queryKey: ['policies', 'recent', source, tag, limit, recentCutoff],
    queryFn: () =>
      fetchPolicies({
        limit,
        source: source !== 'All' ? source : undefined,
        tag: tag !== 'All' ? tag : undefined,
        date_from: recentCutoff,
      }),
    staleTime: 1000 * 60 * 2,
  })

  // Fallback query: policies from Nov 2025 onwards — only runs if recent returns empty
  const needsFallback = recentPolicies !== undefined && recentPolicies.length === 0
  const {
    data: fallbackPolicies,
    isLoading: isLoadingFallback,
    isError: isErrorFallback,
    refetch: refetchFallback,
    isFetching: isFetchingFallback,
  } = useQuery({
    queryKey: ['policies', 'fallback', source, tag, limit, FALLBACK_DATE],
    queryFn: () =>
      fetchPolicies({
        limit,
        source: source !== 'All' ? source : undefined,
        tag: tag !== 'All' ? tag : undefined,
        date_from: FALLBACK_DATE,
      }),
    enabled: needsFallback,
    staleTime: 1000 * 60 * 2,
  })

  const isLoading = isLoadingRecent || (needsFallback && isLoadingFallback)
  const isError = isErrorRecent || (needsFallback && isErrorFallback)
  const isFetching = isFetchingRecent || isFetchingFallback
  const policies = needsFallback ? fallbackPolicies : recentPolicies
  const isFallback = needsFallback && (fallbackPolicies?.length ?? 0) > 0

  function refetch() {
    refetchRecent()
    if (needsFallback) refetchFallback()
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Filter className="w-4 h-4" />
            <span>Filters</span>
          </div>
          <button
            onClick={refetch}
            disabled={isFetching}
            className="btn-secondary text-xs py-1.5 px-3"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Source filter */}
        <div className="flex flex-wrap gap-1.5">
          {SOURCES.map((s) => (
            <button
              key={s}
              onClick={() => setSource(s)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                source === s
                  ? 'bg-brand-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-600 hover:border-brand-300 hover:text-brand-600'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Tag filter */}
        <div className="flex flex-wrap gap-1.5">
          {TAGS.map((t) => (
            <button
              key={t}
              onClick={() => setTag(t)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                tag === t
                  ? 'bg-gray-900 text-white'
                  : 'bg-white border border-gray-200 text-gray-500 hover:border-gray-400 hover:text-gray-700'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Fallback notice */}
      {isFallback && (
        <div className="text-xs text-gray-400 px-1">
          No policies in the last 30 days — showing policies from November 2025 onwards.
        </div>
      )}

      {/* Policy grid */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      )}

      {isError && (
        <div className="card p-8 text-center">
          <p className="text-gray-500">Failed to load policies.</p>
          <button onClick={refetch} className="btn-primary mt-3 text-sm">
            Retry
          </button>
        </div>
      )}

      {!isLoading && policies && policies.length === 0 && (
        <div className="card p-10 text-center">
          <p className="text-gray-500 text-sm">
            No policies found. Try changing filters or trigger an ingestion.
          </p>
        </div>
      )}

      {policies && policies.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {policies.map((policy) => (
            <PolicyCard key={policy.id} policy={policy} />
          ))}
        </div>
      )}
    </div>
  )
}
