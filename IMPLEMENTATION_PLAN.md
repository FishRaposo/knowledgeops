# Implementation Plan

## Phase 1: Core Pipeline (Weeks 1-3)

**Goal:** End-to-end document ingestion and retrieval working locally.

### Week 1: Infrastructure & Gateway

- [x] Docker Compose with PostgreSQL (pgvector), Redis, and Nginx
- [x] Database schema: documents, chunks, embeddings, users, api_keys tables
- [x] API Gateway: FastAPI service with health aggregation and request routing
- [x] Shared Python library: config, logging, health, common models
- [x] Environment variable management with `.env.example`

### Week 2: Ingestion Pipeline

- [x] Ingestion Service: FastAPI with async worker architecture
- [x] Parsers: PDF (PyMuPDF), Markdown, HTML (BeautifulSoup), DOCX (python-docx)
- [x] Processing: text chunking with overlap, SHA-256 deduplication, document versioning
- [x] Redis queue integration for async document processing
- [x] Embedding generation using OpenAI text-embedding-3-small

### Week 3: Retrieval & Basic Frontend

- [x] Retrieval Service: hybrid vector + keyword search
- [x] Reranking with cross-encoder scoring
- [x] Citation assembly linking chunks to source documents
- [x] Answer generation with grounded retrieval and refusal capability
- [x] Web App: Next.js scaffold with sidebar navigation
- [x] Chat interface connected to retrieval pipeline
- [x] Document manager with upload and status tracking

---

## Phase 2: LLM Operations & Quality (Weeks 4-6)

**Goal:** LLM Gateway, evaluation harness, and observability working.

### Week 4: LLM Gateway

- [x] LLM Gateway: Express.js service with OpenAI-compatible proxy API
- [x] Provider abstraction: OpenAI provider with mock provider for testing
- [x] Request routing based on model and provider configuration
- [x] Caching middleware: Redis-backed response cache with TTL
- [x] Budget middleware: per-user and per-team spend tracking and enforcement
- [x] Logging middleware: structured request/response logging

### Week 5: Evaluation & Auth

- [x] Eval Service: FastAPI with RAG evaluation runner
- [x] Semantic match judge: cosine similarity between expected and actual answers
- [x] Citation check judge: verify claims are grounded in cited documents
- [x] Refusal check judge: validate appropriate refusal on out-of-scope queries
- [x] Markdown reporter: generate human-readable eval reports
- [x] Auth Service: API key management with CRUD endpoints
- [x] User sessions with JWT tokens
- [x] RBAC roles: admin, user, viewer

### Week 6: Observability

- [x] Trace Service: trace collector API receiving OpenTelemetry spans
- [x] Trace storage with PostgreSQL backend and query interface
- [x] Trace viewer UI in the web app with filtering and detail views
- [x] Replay engine placeholder for reproducing past requests
- [x] Cost dashboard showing spend by service, user, and model

---

## Phase 3: Polish & Production (Weeks 7-8)

**Goal:** Admin panel, monitoring, full test coverage, deployment readiness.

### Week 7: Admin & Monitoring

- [x] Admin panel: user management, system configuration, service health overview
- [x] Cost tracking integration across all LLM-calling services
- [x] Alerting thresholds for budget overruns and service failures
- [x] Database migration scripts with version tracking
- [x] Production Docker Compose override with resource limits

### Week 8: Testing & Documentation

- [x] Integration tests: health checks, document upload+retrieval, query+citation
- [x] Eval suite execution tests with sample data
- [x] Trace collection and query tests
- [x] Load testing with realistic document volumes
- [x] Complete API documentation with OpenAPI schemas
- [x] Architecture decision records for key design choices
- [x] Deployment guide for AWS ECS, GCP Cloud Run, and bare metal

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Document ingestion | PDF, MD, HTML, DOCX parsed correctly |
| Retrieval accuracy | >80% on basic RAG eval suite |
| End-to-end latency | <5s for a standard query |
| Cost visibility | Per-request cost tracked for all LLM calls |
| Test coverage | >70% on core services |
| Deployment | Single `docker compose up` brings up full platform |
