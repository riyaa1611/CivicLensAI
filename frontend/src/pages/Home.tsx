import { useNavigate } from 'react-router-dom'
import { Landmark, Sparkles, ArrowRight } from 'lucide-react'
import PolicyFeed from '../components/PolicyFeed'
import AskBox from '../components/AskBox'

export default function Home() {
  const navigate = useNavigate()

  const handleQuickAsk = (query: string) => {
    navigate(`/ask?q=${encodeURIComponent(query)}`)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Hero */}
      <div className="text-center mb-12 animate-fade-in">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-brand-50 rounded-full
                        text-brand-700 text-xs font-medium mb-4">
          <Sparkles className="w-3.5 h-3.5" />
          AI-powered civic intelligence
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight leading-tight mb-4">
          Understand every policy
          <span className="text-brand-600"> that affects you</span>
        </h1>
        <p className="text-lg text-gray-500 max-w-2xl mx-auto leading-relaxed">
          CivicLens tracks government policies from PRS, PIB, and Gazette —
          summarizes them in plain language and answers your questions using AI.
        </p>
      </div>

      {/* Quick ask */}
      <div className="max-w-2xl mx-auto mb-12">
        <AskBox
          onSubmit={handleQuickAsk}
          placeholder="Ask about any policy — e.g., 'What does the Data Protection Act mean for me?'"
        />
      </div>

      {/* Quick question chips */}
      <div className="flex flex-wrap gap-2 justify-center mb-12">
        {[
          'What is the Digital Personal Data Protection Act?',
          'How does GST affect small businesses?',
          'What are my rights as a gig worker?',
          'Explain the Telecom Act 2023',
        ].map((q) => (
          <button
            key={q}
            onClick={() => handleQuickAsk(q)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white border border-gray-200
                       rounded-full text-sm text-gray-600 hover:border-brand-300 hover:text-brand-700
                       hover:bg-brand-50 transition-all group"
          >
            <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 -ml-1 transition-opacity" />
            {q}
          </button>
        ))}
      </div>

      {/* Policy Feed */}
      <div>
        <div className="flex items-center gap-3 mb-6">
          <div className="flex items-center gap-2">
            <Landmark className="w-5 h-5 text-brand-600" />
            <h2 className="section-header">Latest Policies</h2>
          </div>
          <span className="text-sm text-gray-400">Updated every 6 hours</span>
        </div>
        <PolicyFeed />
      </div>
    </div>
  )
}
