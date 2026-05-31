export interface Document {
  id: string;
  title: string;
  source: string;
  content_hash: string;
  version: number;
  status: DocumentStatus;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export interface Chunk {
  id: string;
  document_id: string;
  content: string;
  chunk_index: number;
  content_hash: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface Citation {
  chunk_id: string;
  document_id: string;
  document_title: string;
  excerpt: string;
  relevance_score: number;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
  include_metadata?: boolean;
  filters?: Record<string, unknown>;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  refusal: boolean;
  refusal_reason?: string;
  chunks_used: string[];
  confidence: number;
  query: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  created_at: string;
}

export type UserRole = "admin" | "user" | "viewer";

export interface EvalRun {
  id: string;
  name: string;
  status: EvalStatus;
  config: Record<string, unknown>;
  started_at?: string;
  completed_at?: string;
}

export type EvalStatus = "pending" | "running" | "completed" | "failed";

export interface EvalResult {
  id: string;
  run_id: string;
  query: string;
  expected?: string;
  actual?: string;
  scores: Record<string, number>;
  created_at: string;
}

export interface TraceSpan {
  trace_id: string;
  span_id: string;
  parent_span_id?: string;
  service: string;
  operation: string;
  start_time: string;
  end_time: string;
  attributes: Record<string, unknown>;
}

export interface CostRecord {
  id: string;
  service: string;
  user_id?: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_cost_usd: number;
  request_id?: string;
  created_at: string;
}

export interface CostSummary {
  total_usd: number;
  by_service: Record<string, number>;
  by_model: Record<string, number>;
  by_user: Record<string, number>;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  costs: CostRecord[];
}

export interface AlertRecord {
  type: string;
  severity: "info" | "warning" | "critical";
  message: string;
  current_value?: number;
  threshold?: number;
  trace_id?: string;
  span_id?: string;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  service: string;
  version: string;
  timestamp: string;
  dependencies: Record<string, string>;
  metadata: Record<string, unknown>;
}
