// Static demo dataset used when the backend API is unreachable. This lets the
// KnowledgeOps console render a fully populated, interactive UI with zero
// backend services running — useful for portfolio demos and offline review.

import type {
  AlertRecord,
  Citation,
  CostRecord,
  CostSummary,
  Document,
  EvalRun,
  QueryResponse,
  TraceSpan,
} from "../types";

export const demoDocuments: Document[] = [
  {
    id: "demo-doc-1",
    title: "Employee Handbook 2026",
    source: "handbook.pdf",
    content_hash: "demo-hash-1",
    version: 3,
    status: "completed",
    metadata: { pages: 42, format: "pdf" },
    created_at: "2026-05-01T10:00:00Z",
    updated_at: "2026-05-12T09:30:00Z",
  },
  {
    id: "demo-doc-2",
    title: "Refund & Returns Policy",
    source: "refund-policy.md",
    content_hash: "demo-hash-2",
    version: 1,
    status: "completed",
    metadata: { format: "markdown" },
    created_at: "2026-04-18T14:22:00Z",
    updated_at: "2026-04-18T14:22:00Z",
  },
  {
    id: "demo-doc-3",
    title: "Q2 Architecture Review (processing)",
    source: "arch-review.docx",
    content_hash: "demo-hash-3",
    version: 1,
    status: "processing",
    metadata: { format: "docx" },
    created_at: "2026-06-14T08:05:00Z",
    updated_at: "2026-06-14T08:05:00Z",
  },
];

const demoCitations: Citation[] = [
  {
    chunk_id: "demo-chunk-1",
    document_id: "demo-doc-2",
    document_title: "Refund & Returns Policy",
    excerpt:
      "Customers may request a full refund within 30 days of purchase, provided the item is unused and in its original packaging.",
    relevance_score: 0.92,
  },
];

export function demoQueryResponse(query: string): QueryResponse {
  const lowered = query.toLowerCase();
  const isRefusal =
    lowered.length > 0 &&
    !["refund", "return", "policy", "handbook", "leave", "vacation"].some((t) =>
      lowered.includes(t)
    );

  if (isRefusal) {
    return {
      answer:
        "I cannot answer this question based on the available documents in the demo knowledge base.",
      citations: [],
      refusal: true,
      chunks_used: [],
      confidence: 0,
      query,
    };
  }

  return {
    answer:
      "Based on the Refund & Returns Policy, customers may request a full refund within 30 days of purchase as long as the item is unused and in its original packaging. [Chunk 1]",
    citations: demoCitations,
    refusal: false,
    chunks_used: ["demo-chunk-1"],
    confidence: 0.92,
    query,
  };
}

export const demoCostRecords: CostRecord[] = [
  {
    id: "demo-cost-1",
    service: "retrieval-service",
    user_id: "demo-user",
    model: "gpt-4o-mini",
    prompt_tokens: 1820,
    completion_tokens: 240,
    total_cost_usd: 0.00041,
    request_id: "demo-req-1",
    created_at: "2026-06-15T11:02:00Z",
  },
  {
    id: "demo-cost-2",
    service: "eval-service",
    user_id: "demo-user",
    model: "gpt-4o-mini",
    prompt_tokens: 640,
    completion_tokens: 110,
    total_cost_usd: 0.00015,
    request_id: "demo-req-2",
    created_at: "2026-06-15T11:05:00Z",
  },
];

export const demoCostSummary: CostSummary = {
  total_usd: 0.00056,
  by_service: { "retrieval-service": 0.00041, "eval-service": 0.00015 },
  by_model: { "gpt-4o-mini": 0.00056 },
  by_user: { "demo-user": 0.00056 },
  total_prompt_tokens: 2460,
  total_completion_tokens: 350,
  costs: demoCostRecords,
};

export const demoAlerts: AlertRecord[] = [
  {
    type: "budget_overrun",
    severity: "warning",
    message: "Demo budget at 56% of the configured $0.001 ceiling.",
    current_value: 0.00056,
    threshold: 0.001,
  },
];

export const demoTraces: TraceSpan[] = [
  {
    trace_id: "demo-trace-aaaa1111",
    span_id: "demo-span-1",
    service: "retrieval-service",
    operation: "answer_generation",
    start_time: "2026-06-15T11:02:00.000Z",
    end_time: "2026-06-15T11:02:00.480Z",
    attributes: { model: "gpt-4o-mini", prompt_tokens: 1820, status: "ok" },
  },
  {
    trace_id: "demo-trace-bbbb2222",
    span_id: "demo-span-2",
    service: "eval-service",
    operation: "eval_run",
    start_time: "2026-06-15T11:05:00.000Z",
    end_time: "2026-06-15T11:05:01.120Z",
    attributes: { run_name: "basic_rag", total_cases: 3, status: "ok" },
  },
];

export const demoEvalRun: EvalRun = {
  id: "demo-eval-1",
  name: "basic_rag (demo)",
  status: "completed",
  config: { suite: "basic_rag", total_cases: 3 },
  started_at: "2026-06-15T11:05:00Z",
  completed_at: "2026-06-15T11:05:01Z",
};

// Maps an API path + method to the demo payload that should be returned when the
// backend is unreachable. Returns `undefined` when no demo data is defined for
// the route (the caller then re-throws the original error).
export function getDemoResponse(path: string, method: string, body?: unknown): unknown {
  const m = method.toUpperCase();

  if (path === "/health") {
    return {
      status: "demo",
      services: {
        "auth-service": "demo",
        "ingestion-service": "demo",
        "retrieval-service": "demo",
        "eval-service": "demo",
        "trace-service": "demo",
      },
    };
  }
  if (path === "/documents" && m === "GET") return { documents: demoDocuments };
  if (path === "/documents/upload" && m === "POST") {
    return {
      document: {
        ...demoDocuments[0],
        id: `demo-doc-${Date.now()}`,
        title: "Uploaded (demo) document",
        status: "processing",
        version: 1,
      },
    };
  }
  if (path === "/query" && m === "POST") {
    const query =
      typeof body === "string"
        ? (JSON.parse(body) as { query?: string }).query ?? ""
        : "";
    return demoQueryResponse(query);
  }
  if (path === "/costs" && m === "GET") return demoCostSummary;
  if (path === "/alerts" && m === "GET") return { alerts: demoAlerts };
  if (path === "/traces" && m === "GET") return { traces: demoTraces };
  if (path === "/evals/run" && m === "POST") return { eval_run: demoEvalRun };
  if (path === "/evals" && m === "GET") return { evals: [demoEvalRun] };
  if (path === "/evals/runs" && m === "GET") return { evals: [demoEvalRun] };

  return undefined;
}
