import axios from 'axios'
import type { Policy, QueryResponse, DashboardStats, UploadResponse } from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// --------------------------------------------------------------------------
// Policies
// --------------------------------------------------------------------------

export async function fetchPolicies(params?: {
  skip?: number
  limit?: number
  source?: string
  tag?: string
  date_from?: string
}): Promise<Policy[]> {
  const { data } = await api.get<Policy[]>('/policies', { params })
  return data
}

export async function fetchPolicy(id: string): Promise<Policy> {
  const { data } = await api.get<Policy>(`/policy/${id}`)
  return data
}

// --------------------------------------------------------------------------
// Query (RAG)
// --------------------------------------------------------------------------

export async function queryPolicies(
  query: string,
  top_k = 5
): Promise<QueryResponse> {
  const { data } = await api.post<QueryResponse>('/query', { query, top_k })
  return data
}

// --------------------------------------------------------------------------
// Upload
// --------------------------------------------------------------------------

export async function uploadBill(
  file: File,
  title?: string
): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  if (title) form.append('title', title)

  const { data } = await api.post<UploadResponse>('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
  return data
}

// --------------------------------------------------------------------------
// Dashboard
// --------------------------------------------------------------------------

export async function fetchDashboard(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>('/dashboard')
  return data
}

// --------------------------------------------------------------------------
// Ingest (manual trigger)
// --------------------------------------------------------------------------

export async function triggerIngestion(): Promise<{ status: string; message: string }> {
  const { data } = await api.post('/ingest')
  return data
}
