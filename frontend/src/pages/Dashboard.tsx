import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  BarChart3, Database, MessageSquare, Zap, TrendingDown,
  RefreshCw, CheckCircle, XCircle, Play, Loader2
} from 'lucide-react'
import { fetchDashboard, triggerIngestion } from '../services/api'
import type { DashboardStats } from '../types'

function MetricCard({
  label, value, sub, icon: Icon, color = 'brand',
}: {
  label: string
  value: string | number
  sub?: string
  icon: React.ElementType
  color?: string
}) {
  const colorMap: Record<string, string> = {
    brand: 'bg-brand-50 text-brand-600',
    green: 'bg-green-50 text-green-600',
    blue: 'bg-blue-50 text-blue-600',
    orange: 'bg-orange-50 text-orange-600',
    purple: 'bg-purple-50 text-purple-600',
  }
  return (
    <div className="metric-card">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colorMap[color] || colorMap.brand}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        <p className="text-sm font-medium text-gray-600">{label}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

function SourceBar({ label, count, total }: { label: string; count: number; total: number }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  const colors: Record<string, string> = {
    PRS: 'bg-blue-400',
    PIB: 'bg-green-400',
    Gazette: 'bg-orange-400',
    Upload: 'bg-purple-400',
  }
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="font-medium text-gray-700">{label}</span>
        <span className="text-gray-400">{count} ({pct}%)</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${colors[label] || 'bg-brand-400'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

export default function Dashboard() {
  const queryClient = useQueryClient()

  const { data: stats, isLoading, isError, refetch } = useQuery<DashboardStats>({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    refetchInterval: 30000, // auto-refresh every 30s
  })

  const ingestMutation = useMutation({
    mutationFn: triggerIngestion,
    onSuccess: () => {
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ['dashboard'] }), 3000)
    },
  })

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 flex justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    )
  }

  if (isError || !stats) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
        <div className="card p-10 text-center">
          <p className="text-gray-500">Failed to load dashboard.</p>
          <button onClick={() => refetch()} className="btn-primary mt-3">Retry</button>
        </div>
      </div>
    )
  }

  const totalPolicies = stats.total_policies
  const sourceCounts = stats.source_counts || {}

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="section-header">Dashboard</h1>
          <p className="text-sm text-gray-400 mt-1">System metrics and optimization stats</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => refetch()}
            className="btn-secondary text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={() => ingestMutation.mutate()}
            disabled={ingestMutation.isPending}
            className="btn-primary text-sm"
          >
            {ingestMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Run Ingestion
          </button>
        </div>
      </div>

      {/* Ingestion status */}
      {ingestMutation.isSuccess && (
        <div className="card p-4 border-green-100 bg-green-50/30 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-green-500" />
          <span className="text-sm text-green-700">Ingestion started in background</span>
        </div>
      )}

      {/* Metric cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Policies"
          value={stats.total_policies.toLocaleString()}
          sub={`${stats.indexed_policies} indexed`}
          icon={Database}
          color="brand"
        />
        <MetricCard
          label="Queries Answered"
          value={stats.total_queries.toLocaleString()}
          icon={MessageSquare}
          color="blue"
        />
        <MetricCard
          label="Avg Compression"
          value={stats.avg_compression_ratio > 1 ? `${stats.avg_compression_ratio.toFixed(1)}×` : '—'}
          sub="via compression"
          icon={TrendingDown}
          color="green"
        />
        <MetricCard
          label="Tokens Saved"
          value={stats.total_token_savings > 0 ? stats.total_token_savings.toLocaleString() : '0'}
          sub="via compression"
          icon={Zap}
          color="orange"
        />
      </div>

      {/* Source breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-5">
            <BarChart3 className="w-4 h-4 text-brand-600" />
            <h2 className="font-semibold text-gray-900">Policy Sources</h2>
          </div>
          <div className="space-y-4">
            {Object.entries(sourceCounts).map(([src, cnt]) => (
              <SourceBar key={src} label={src} count={cnt} total={totalPolicies} />
            ))}
            {Object.keys(sourceCounts).length === 0 && (
              <p className="text-sm text-gray-400">No policies ingested yet</p>
            )}
          </div>
        </div>

        {/* Optimization status */}
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-5">
            <Zap className="w-4 h-4 text-brand-600" />
            <h2 className="font-semibold text-gray-900">Optimization Status</h2>
          </div>
          <div className="space-y-4">
            <StatusRow
              label="Context Compressor"
              active={stats.scaledown_status.compressor_available}
              desc={
                stats.scaledown_status.compressor_available
                  ? 'API-powered compression active'
                  : 'API key not configured'
              }
            />
            <StatusRow
              label="SemanticOptimizer"
              active={stats.scaledown_status.semantic_optimizer_available}
              desc={
                stats.scaledown_status.semantic_optimizer_available
                  ? 'Local FAISS semantic search active'
                  : 'Install sentence-transformers + faiss-cpu'
              }
            />
            <div className="pt-3 border-t border-gray-50">
              <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Active mode</p>
              <p className="text-sm font-medium text-gray-700">
                {stats.scaledown_status.mode}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Info box */}
      <div className="card p-5 bg-brand-50/50 border-brand-100">
        <h3 className="text-sm font-semibold text-brand-800 mb-2">About Context Optimization</h3>
        <p className="text-sm text-brand-700 leading-relaxed">
          CivicLens compresses retrieved policy chunks before sending them to the LLM.
          This reduces token usage (and cost) while preserving answer quality.
          The <code className="bg-brand-100 px-1 rounded">Context Compressor</code> uses
          an API-powered service, while <code className="bg-brand-100 px-1 rounded">SemanticOptimizer</code> runs
          locally using FAISS embeddings.
        </p>
      </div>
    </div>
  )
}

function StatusRow({
  label, active, desc,
}: { label: string; active: boolean; desc: string }) {
  return (
    <div className="flex items-start gap-3">
      {active ? (
        <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
      ) : (
        <XCircle className="w-5 h-5 text-gray-300 flex-shrink-0 mt-0.5" />
      )}
      <div>
        <p className="text-sm font-medium text-gray-700">{label}</p>
        <p className="text-xs text-gray-400 mt-0.5">{desc}</p>
      </div>
    </div>
  )
}
