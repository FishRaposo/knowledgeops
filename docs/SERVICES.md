# Services Reference

## API Gateway (`services/api-gateway/`)

**Port:** 8000 | **Language:** Python/FastAPI

Central request router and health aggregator. All frontend requests flow through the gateway, which validates authentication and routes to the appropriate backend service.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Aggregated health from all services |
| GET | `/api/docs` | OpenAPI documentation |
| POST | `/api/documents/upload` | Upload document for ingestion |
| GET | `/api/documents` | List documents |
| POST | `/api/query` | Execute a retrieval query |
| POST | `/api/evals/run` | Start an evaluation run |
| GET | `/api/evals` | List evaluation runs |
| GET | `/api/traces` | Query traces |
| GET | `/api/costs` | Cost summary |

### Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTH_SERVICE_URL` | Auth service base URL | `http://auth-service:8001` |
| `INGESTION_SERVICE_URL` | Ingestion service base URL | `http://ingestion-service:8002` |
| `RETRIEVAL_SERVICE_URL` | Retrieval service base URL | `http://retrieval-service:8003` |
| `EVAL_SERVICE_URL` | Eval service base URL | `http://eval-service:8005` |
| `TRACE_SERVICE_URL` | Trace service base URL | `http://trace-service:8006` |

---

## Auth Service (`services/auth-service/`)

**Port:** 8001 | **Language:** Python/FastAPI

Manages API keys, user sessions, and role-based access control.

### Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access: manage users, keys, system config |
| `user` | Upload documents, query, view evals and traces |
| `viewer` | Read-only access to documents, evals, and traces |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/token` | Exchange API key for JWT |
| GET | `/auth/me` | Get current user info |
| POST | `/auth/keys` | Create new API key |
| GET | `/auth/keys` | List API keys |
| DELETE | `/auth/keys/{key_id}` | Revoke API key |
| GET | `/auth/users` | List users (admin only) |

---

## Ingestion Service (`services/ingestion-service/`)

**Port:** 8002 | **Language:** Python/FastAPI

Document ingestion pipeline with multi-format parsing, chunking, deduplication, and async processing.

### Supported Formats

| Format | Parser | Library |
|--------|--------|---------|
| PDF | `parsers.pdf` | PyMuPDF |
| Markdown | `parsers.markdown` | markdown-it-py |
| HTML | `parsers.html` | BeautifulSoup4 |
| DOCX | `parsers.docx` | python-docx |

### Processing Pipeline

1. **Parse** — Extract raw text from document format
2. **Chunk** — Split text into overlapping chunks (default: 512 tokens, 64 overlap)
3. **Deduplicate** — SHA-256 content hash to skip duplicate chunks
4. **Embed** — Generate vector embeddings via LLM Gateway
5. **Store** — Persist chunks and embeddings to PostgreSQL

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ingest/upload` | Upload document |
| GET | `/ingest/documents` | List documents |
| GET | `/ingest/documents/{id}` | Get document status |
| DELETE | `/ingest/documents/{id}` | Delete document |
| GET | `/ingest/jobs/{id}` | Get processing job status |

---

## Retrieval Service (`services/retrieval-service/`)

**Port:** 8003 | **Language:** Python/FastAPI

Hybrid retrieval with vector similarity, keyword search, reranking, citation assembly, and grounded answer generation.

### Search Pipeline

1. **Embed query** — Generate query vector via LLM Gateway
2. **Vector search** — pgvector cosine similarity against chunk embeddings
3. **Keyword search** — PostgreSQL full-text search with tsvector
4. **Hybrid fusion** — Reciprocal rank fusion of vector and keyword results
5. **Rerank** — Cross-encoder scoring on fused results
6. **Cite** — Assemble citations linking claims to source chunks
7. **Generate** — LLM answer grounded in retrieved context

### Refusal Behavior

When no chunks exceed the similarity threshold, the system returns a structured refusal instead of hallucinating an answer.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/retrieve/query` | Execute retrieval query |
| POST | `/retrieve/search` | Search without generation |
| GET | `/retrieve/citations/{doc_id}` | Get document citations |

---

## LLM Gateway (`services/llm-gateway/`)

**Port:** 8004 | **Language:** TypeScript/Express

OpenAI-compatible proxy with provider routing, caching, budget enforcement, and structured logging.

### Middleware Stack

| Middleware | Purpose |
|-----------|---------|
| `cache` | Redis-backed response cache with configurable TTL |
| `budget` | Per-user monthly spend tracking and enforcement |
| `logging` | Structured request/response logging to stdout |

### Supported Providers

| Provider | Models |
|----------|--------|
| OpenAI | gpt-4o, gpt-4o-mini, text-embedding-3-small |
| Mock | Any model (returns deterministic responses for testing) |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/chat/completions` | OpenAI-compatible chat |
| POST | `/v1/embeddings` | OpenAI-compatible embeddings |
| GET | `/v1/models` | List available models |
| GET | `/health` | Health check |

---

## Eval Service (`services/eval-service/`)

**Port:** 8005 | **Language:** Python/FastAPI

Automated RAG evaluation with configurable judges and report generation.

### Judges

| Judge | Metric | Description |
|-------|--------|-------------|
| Semantic Match | 0.0-1.0 | Cosine similarity between expected and actual answer |
| Citation Check | pass/fail | Verifies claims are grounded in cited chunks |
| Refusal Check | pass/fail | Validates appropriate refusal on out-of-scope queries |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/eval/run` | Start evaluation run |
| GET | `/eval/runs` | List runs |
| GET | `/eval/runs/{id}` | Get run results |
| GET | `/eval/runs/{id}/report` | Get markdown report |
| POST | `/eval/suites` | Upload eval suite YAML |

---

## Trace Service (`services/trace-service/`)

**Port:** 8006 | **Language:** Python/FastAPI

Distributed tracing collection, storage, and query interface for observability.

### Features

- **Collection** — HTTP endpoint for receiving trace spans from all services
- **Storage** — PostgreSQL-backed trace storage with indexing
- **Query** — Filter by service, operation, duration, and time range
- **Replay** — Placeholder for reproducing past request chains

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/traces/ingest` | Ingest trace spans |
| GET | `/traces` | Query traces |
| GET | `/traces/{trace_id}` | Get trace detail |
| POST | `/traces/{trace_id}/replay` | Replay a trace |
