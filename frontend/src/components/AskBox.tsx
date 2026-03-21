import { useState, useRef, FormEvent } from 'react'
import { Send, Loader2, Sparkles } from 'lucide-react'
import clsx from 'clsx'

interface Props {
  onSubmit: (query: string) => void
  loading?: boolean
  placeholder?: string
  initialQuery?: string
}

export default function AskBox({
  onSubmit,
  loading = false,
  placeholder = 'Ask about any government policy, act, or regulation...',
  initialQuery = '',
}: Props) {
  const [query, setQuery] = useState(initialQuery)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = query.trim()
    if (!trimmed || loading) return
    onSubmit(trimmed)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as unknown as FormEvent)
    }
  }

  const autoResize = () => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className={clsx(
        'relative flex items-end gap-3 p-3 bg-white rounded-2xl border',
        'shadow-sm transition-shadow duration-200',
        loading ? 'border-brand-300 shadow-brand-100/50 shadow-md' : 'border-gray-200 hover:border-gray-300 focus-within:border-brand-400 focus-within:shadow-md'
      )}>
        <Sparkles className="w-5 h-5 text-brand-400 flex-shrink-0 mb-2.5" />
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            autoResize()
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          disabled={loading}
          className="flex-1 resize-none bg-transparent text-gray-900 placeholder-gray-400
                     text-sm leading-relaxed focus:outline-none min-h-[36px] max-h-[160px]
                     disabled:opacity-50 py-1.5"
        />
        <button
          type="submit"
          disabled={!query.trim() || loading}
          className={clsx(
            'flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-colors',
            query.trim() && !loading
              ? 'bg-brand-600 text-white hover:bg-brand-700'
              : 'bg-gray-100 text-gray-300 cursor-not-allowed'
          )}
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </div>
      <p className="text-xs text-gray-400 mt-2 text-center">
        Press Enter to send · Shift+Enter for new line
      </p>
    </form>
  )
}
