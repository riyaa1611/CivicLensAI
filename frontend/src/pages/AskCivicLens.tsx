import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, Loader2, MessageSquare, History } from 'lucide-react'
import AskBox from '../components/AskBox'
import AnswerCard from '../components/AnswerCard'
import { queryPolicies } from '../services/api'
import type { QueryResponse } from '../types'

interface ConversationItem {
  query: string
  result: QueryResponse
  timestamp: number
}

const EXAMPLE_QUESTIONS = [
  'What does the Digital Personal Data Protection Act mean for app developers?',
  'How does the new Telecom Act affect consumers?',
  'What are the GST rules for startups in India?',
  'Explain the rights of gig workers under the Social Security Code',
  'What are the key provisions of the Jan Vishwas Act?',
  'How does SEBI regulate listed companies?',
]

export default function AskCivicLens() {
  const [searchParams] = useSearchParams()
  const [conversation, setConversation] = useState<ConversationItem[]>([])
  const [currentQuery, setCurrentQuery] = useState('')

  const mutation = useMutation({
    mutationFn: (q: string) => queryPolicies(q, 5),
    onSuccess: (data, query) => {
      setConversation((prev) => [
        { query, result: data, timestamp: Date.now() },
        ...prev,
      ])
    },
  })

  // Handle query from URL param (coming from home page)
  useEffect(() => {
    const q = searchParams.get('q')
    if (q && !mutation.isPending) {
      setCurrentQuery(q)
      mutation.mutate(q)
    }
  }, []) // eslint-disable-line

  const handleSubmit = (q: string) => {
    setCurrentQuery(q)
    mutation.mutate(q)
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10">
      {/* Header */}
      <div className="text-center mb-8 animate-fade-in">
        <div className="w-12 h-12 rounded-2xl bg-brand-600 flex items-center justify-center mx-auto mb-4">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Ask CivicLens</h1>
        <p className="text-gray-500">
          Ask anything about Indian government policies, laws, and regulations.
          <br />
          Powered by RAG + intelligent context optimization.
        </p>
      </div>

      {/* Ask box */}
      <div className="mb-8">
        <AskBox
          onSubmit={handleSubmit}
          loading={mutation.isPending}
          initialQuery={searchParams.get('q') || ''}
        />
      </div>

      {/* Loading */}
      {mutation.isPending && (
        <div className="card p-8 flex flex-col items-center gap-3 text-center animate-pulse-slow">
          <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
          <div>
            <p className="font-medium text-gray-700">Searching policy database...</p>
            <p className="text-sm text-gray-400 mt-1">
              Retrieving chunks → context optimization → LLM response
            </p>
          </div>
        </div>
      )}

      {/* Latest result */}
      {!mutation.isPending && conversation.length > 0 && (
        <div className="mb-8 animate-slide-up">
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-600">
              "{conversation[0].query}"
            </span>
          </div>
          <AnswerCard result={conversation[0].result} query={conversation[0].query} />
        </div>
      )}

      {/* Error */}
      {mutation.isError && !mutation.isPending && (
        <div className="card p-6 text-center border-red-100 bg-red-50/50">
          <p className="text-red-600 text-sm">
            Failed to get an answer. Please check your connection and try again.
          </p>
        </div>
      )}

      {/* Previous conversation */}
      {conversation.length > 1 && (
        <div className="mt-8 space-y-6">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-gray-400" />
            <h3 className="text-sm font-medium text-gray-500">Previous questions</h3>
          </div>
          {conversation.slice(1).map((item) => (
            <div key={item.timestamp} className="opacity-75 hover:opacity-100 transition-opacity">
              <div className="flex items-center gap-2 mb-2">
                <MessageSquare className="w-3.5 h-3.5 text-gray-300" />
                <span className="text-xs text-gray-400">"{item.query}"</span>
              </div>
              <AnswerCard result={item.result} query={item.query} />
            </div>
          ))}
        </div>
      )}

      {/* Example questions (only when no conversation) */}
      {conversation.length === 0 && !mutation.isPending && (
        <div className="mt-8 animate-fade-in">
          <p className="text-sm text-gray-400 mb-3 text-center">Try asking:</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {EXAMPLE_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => handleSubmit(q)}
                className="text-left p-3 text-sm text-gray-600 bg-white border border-gray-100
                           rounded-xl hover:border-brand-200 hover:bg-brand-50/50 hover:text-brand-700
                           transition-all leading-relaxed"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
