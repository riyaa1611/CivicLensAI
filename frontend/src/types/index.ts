export interface Policy {
  id: string
  title: string
  source: 'PRS' | 'PIB' | 'Gazette' | 'Upload' | string
  date: string | null
  summary: string | null
  tags: string[]
  key_clauses: string[]
  link: string | null
  is_indexed: boolean
  created_at: string | null
}

export interface QuerySource {
  policy_id: string
  title: string
  source: string
  score: number
}

export interface OptimizationMetrics {
  status: string
  fallback: boolean
  original_tokens: number
  compressed_tokens: number
  compression_ratio: number
  savings_percent: number
  latency_ms?: number
}

export interface QueryResponse {
  answer: string
  sources: QuerySource[]
  metrics: OptimizationMetrics
  latency_ms: number
}

export interface UploadResponse {
  policy_id: string
  title: string
  status: string
  message: string
  chars: number
}

export interface DashboardStats {
  total_policies: number
  total_queries: number
  avg_compression_ratio: number
  total_token_savings: number
  source_counts: Record<string, number>
  indexed_policies: number
  scaledown_status: {
    compressor_available: boolean
    semantic_optimizer_available: boolean
    mode: string
  }
}
