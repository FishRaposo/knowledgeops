// Re-export all shared KnowledgeOps types from the shared-ts package.

export {
  type Document,
  type DocumentStatus,
  type Chunk,
  type Citation,
  type QueryRequest,
  type QueryResponse,
  type User,
  type UserRole,
  type EvalRun,
  type EvalStatus,
  type EvalResult,
  type TraceSpan,
  type CostRecord,
  type CostSummary,
  type AlertRecord,
  type HealthResponse,
  type ApiError,
  ApiClient,
} from "@knowledgeops/shared-ts";
