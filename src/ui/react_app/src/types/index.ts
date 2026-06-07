export interface UploadResponse {
  session_id: string
  file_name: string
  file_size_mb: number
  sheets: string[]
  schemas: Record<string, SchemaInfo>
}

export interface SchemaInfo {
  columns: string[]
  row_count: number
  column_types: Record<string, string>
  missing_values: Record<string, number>
  suggested_roles?: Record<string, string>
  numeric_columns?: string[]
  datetime_columns?: string[]
  categorical_columns?: string[]
}

export interface AnalyzeRequest {
  session_id: string
  question: string
}

export interface AnalyzeResponse {
  session_id: string
  question: string
  intent: Record<string, unknown>
  result: Record<string, unknown> | null
  chart_html: string | null
  narrative: string
  recommendation: string | null
  error: string | null
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  question?: string
  narrative?: string
  recommendation?: string | null
  chartHtml?: string | null
  error?: string | null
  timestamp: Date
}

export interface KnowledgeStatus {
  last_update: string
  total_entries: number
  total_papers_indexed: number
  topics_tracked: string[]
  crawl_enabled: boolean
  next_scheduled_crawl: string | null
}
