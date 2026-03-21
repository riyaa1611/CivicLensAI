import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { ArrowLeft, Calendar, Loader2, MessageSquare } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import SummaryPanel from '../components/SummaryPanel'
import AskBox from '../components/AskBox'
import AnswerCard from '../components/AnswerCard'
import { fetchPolicy, queryPolicies } from '../services/api'
import type { QueryResponse } from '../types'

export default function PolicyDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null)
  const [currentQuery, setCurrentQuery] = useState('')

  const { data: policy, isLoading, isError } = useQuery({
    queryKey: ['policy', id],
    queryFn: () => fetchPolicy(id!),
    enabled: !!id,
  })

  const queryMutation = useMutation({
    mutationFn: (q: string) => queryPolicies(q),
    onSuccess: (data) => setQueryResult(data),
  })

  const handleQuery = (q: string) => {
    setCurrentQuery(q)
    queryMutation.mutate(q)
  }

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
        </div>
      </div>
    )
  }

  if (isError || !policy) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
        <div className="card p-10 text-center">
          <p className="text-gray-500">Policy not found.</p>
          <Link to="/" className="btn-primary mt-4">Go back</Link>
        </div>
      </div>
    )
  }

  const dateLabel = policy.date
    ? format(parseISO(policy.date), 'MMMM d, yyyy')
    : 'Unknown date'

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 animate-fade-in">
      {/* Back */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className={`tag tag-source-${policy.source.toLowerCase()}`}>
            {policy.source}
          </span>
          <span className="flex items-center gap-1 text-sm text-gray-400">
            <Calendar className="w-3.5 h-3.5" />
            {dateLabel}
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight">
          {policy.title}
        </h1>
      </div>

      {/* Main layout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Summary panel */}
        <div className="lg:col-span-3">
          <SummaryPanel policy={policy} />
        </div>

        {/* Ask box */}
        <div className="lg:col-span-2">
          <div className="sticky top-24 space-y-4">
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-4">
                <MessageSquare className="w-4 h-4 text-brand-600" />
                <h3 className="font-semibold text-gray-900 text-sm">Ask about this policy</h3>
              </div>
              <AskBox
                onSubmit={handleQuery}
                loading={queryMutation.isPending}
                placeholder={`Ask anything about "${policy.title.substring(0, 40)}..."`}
              />
            </div>

            {queryMutation.isPending && (
              <div className="card p-6 flex items-center justify-center gap-2 text-gray-400">
                <Loader2 className="w-5 h-5 animate-spin text-brand-500" />
                <span className="text-sm">Searching and optimizing context...</span>
              </div>
            )}

            {queryResult && !queryMutation.isPending && (
              <AnswerCard result={queryResult} query={currentQuery} />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
