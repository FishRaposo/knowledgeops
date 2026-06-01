# KnowledgeOps — Improvement Plan

> Comprehensive audit of bugs, inconsistencies, missing features, and growth opportunities.
> Priority levels: **P0** (broken/blocking), **P1** (high value), **P2** (polish), **P3** (long-term growth).

---

## 1. P0 — Broken Code & Critical Fixes

### 1.1 In-memory stores everywhere — PostgreSQL schema unused

The PostgreSQL schema (`infra/postgres/init.sql`) defines 10 well-indexed tables with pgvector support, but most services use in-memory Python dicts instead:

| Service | Storage | What's Missing |
|---------|---------|----------------|
| **Retrieval** | `InMemoryIndex` dict | Doesn't use pgvector at all. Vectors stored as Python lists. |
| **Trace** | `_traces_store` dict | No persistence. Resets on restart. |
| **Ingestion** | `_documents_store`, `_chunks_store` dicts | SQLAlchemy models exist but parallel in-memory stores used for reads. |
| **Eval** | `_eval_runs` dict | No persistence. |

This is the single biggest gap between the designed architecture and the implementation.

**Action (per service):**
- **Retrieval:** Replace `InMemoryIndex` with pgvector queries. The `hybrid.py` endpoint should query PostgreSQL directly.
- **Trace:** Replace `_traces_store` with a `traces` table. Cost aggregation should use SQL queries.
- **Ingestion:** Remove in-memory `_documents_store` and `_chunks_store`. All reads should go through SQLAlchemy.
- **Eval:** Store eval runs in a `eval_runs` table.

### 1.2 Shared libraries not actually used by services

`shared/python/shared/models.py` defines 9 Pydantic models (`Document`, `Chunk`, `Citation`, `QueryRequest`, `QueryResponse`, etc.) but every service redefines its own models locally:

| Service | Redefined Models |
|---------|-----------------|
| Ingestion | `DocumentResponse`, `JobResponse`, `ChunkResponse` |
| Retrieval | `SearchRequest`, `SearchResult`, `SearchResponse`, `QueryRequest` |
| Eval | `EvalRunRequest`, `EvalRunResponse`, `EvalResult` |
| Trace | `SpanCreate`, `SpanResponse`, `CostReport` |

**Action:** Refactor each service to import from `shared.python.shared.models`. Add service-specific extension models only when needed.

### 1.3 Frontend types duplicated

`services/web-app/src/types/index.ts` duplicates the same types from `shared/ts/src/index.ts` rather than importing from the shared package.

**Action:** Have the web-app depend on `@knowledgeops/shared-ts` and import types directly.

### 1.4 K8s ConfigMap has incorrect ports

`k8s/base/configmap.yaml` uses port 8000 for all services and 3000 for LLM Gateway, inconsistent with actual service ports:
- API Gateway: 8000
- Auth: 8001
- Ingestion: 8002
- Retrieval: 8003
- LLM Gateway: 8004
- Eval: 8005
- Trace: 8006

**Action:** Fix all service URLs in the ConfigMap to use correct ports.

---

## 2. P1 — High-Value Fixes

### 2.1 In-memory versioning resets on restart

`services/ingestion-service/app/processing/versioning.py` tracks document versions in a Python dict.

**Action:** Use the `document_versions` table from the PostgreSQL schema.

### 2.2 Ingestion uses `asyncio.create_task()` instead of Redis queue

`docker-compose.yml` says "Redis queue integration for async document processing" but the code uses fire-and-forget `asyncio.create_task()`. Background tasks are lost on server restart.

**Action:** Implement Redis-based task queue (using `arq` or Celery) for document processing. At minimum, add task status persistence so processing can resume after restart.

### 2.3 No per-service unit tests

All `services/*/tests/__init__.py` files are empty. Only top-level `tests/` has tests.

**Action:** Add per-service test suites:
- **api-gateway:** Test proxy routing, auth forwarding, envelope normalization
- **auth-service:** Test JWT creation/verification, API key CRUD, RBAC
- **ingestion-service:** Test parsing, chunking, deduplication
- **retrieval-service:** Test hybrid search, reranking, citation assembly
- **llm-gateway:** Test provider routing, caching, budget enforcement
- **eval-service:** Test judges, runner, report generation
- **trace-service:** Test span ingestion, cost aggregation, replay

### 2.4 Module-level settings instantiation

Every Python file creates a module-level settings instance (`settings = GatewaySettings()` at top of every module). Settings load at import time, making testing harder.

**Action:** Use dependency injection via FastAPI's `Depends()`. Create a `get_settings()` function with `@lru_cache()`.

### 2.5 LLM Gateway creates new provider instances per request

`getProvider()` calls `new OpenAIProvider()` on every request instead of reusing instances. Creates a new OpenAI client per request.

**Action:** Cache provider instances. Use a registry/factory that reuses existing instances.

### 2.6 Duplicate Redis connections in LLM Gateway

Both `cache.ts` and `budget.ts` independently create their own Redis connections with identical logic.

**Action:** Extract a shared Redis connection factory. Single connection pool shared across middleware.

### 2.7 `_envelope()` function has questionable branch

`services/api-gateway/app/routes/proxy.py`: `if collection_key.endswith("s"): return {collection_key: [] if payload is None else payload}` — any plural key returns payload wrapped, even if it's a string or number.

**Action:** Add type checking. Only wrap when payload is an array or object.

### 2.8 Admin endpoints trust only `X-User-Role` header

Auth service's `list_users` and `create_api_key` endpoints trust the `X-User-Role` header without verifying the JWT token directly. The gateway verifies JWT first, but the auth service itself has no JWT verification.

**Action:** Add JWT verification middleware to the auth service's admin routes. Extract user role from verified token, not from a header.

### 2.9 Duplicate `nginx.conf`

Both `nginx/nginx.conf` and `infra/nginx/nginx.conf` exist (docker-compose uses `infra/nginx/nginx.conf`).

**Action:** Delete root-level `nginx/nginx.conf`.

### 2.10 Tests use fragile `importlib` loading

`test_local_services.py` and `test_load_smoke.py` use `importlib.util.spec_from_file_location` to dynamically load modules, bypassing normal Python import resolution.

**Action:** Make services installable (they have `pyproject.toml` already). Install in dev mode and use normal imports.

---

## 3. P2 — Polish & Depth

### 3.1 No CORS configuration in any service

None of the 8 services configure CORS. In a microservices architecture with a web frontend, this will cause issues.

**Action:** Add CORSMiddleware to each FastAPI service. Make allowed origins configurable via env var.

### 3.2 Hardcoded model names

`"gpt-4o-mini"` and `"text-embedding-3-small"` are hardcoded in `answer.py` and the retrieval index.

**Action:** Move to service config (`config.py`). Allow override via environment variable.

### 3.3 Token estimation is crude

`_estimate_tokens()` uses `len(text.split())` instead of a proper tokenizer.

**Action:** Use `tiktoken` for OpenAI models, or at minimum use a character-based heuristic (`len(text) / 4`).

### 3.4 Cost estimation is hardcoded

Uses flat rates ($0.00001/$0.00003 per token) rather than model-specific pricing.

**Action:** Add a pricing table (can import from `shared/` or create a pricing config file). Use model-specific rates.

### 3.5 LLM Gateway has no streaming support

The proxy handler defines a `stream` field but ignores it. All responses are non-streaming.

**Action:** Implement SSE streaming pass-through. Forward provider stream chunks to the client.

### 3.6 Trace replay is a placeholder

The replay engine only returns the plan of operations; `dry_run` defaults to True and actual execution just returns the same plan.

**Action:** Implement actual replay: re-execute the traced operations against the retrieval service and compare results.

### 3.7 `passlib` dependency unused

Auth service has `passlib` as a dependency but password hashing is not implemented anywhere.

**Action:** Either implement password hashing with passlib or remove the dependency.

### 3.8 Web App references external projects on dashboard

The dashboard shows "Connected Projects" (GroundTruth, LLM Gateway, EvalForge, AgentTrace) linking to localhost:3000-3003, which are separate projects not part of this repo.

**Action:** Either remove the section or make it configurable (load from env vars). Add a note that these are sibling portfolio projects.

### 3.9 Security checklist unchecked

`docs/SECURITY.md` has 4 items (secrets as files, DB not exposed, JWT rotation, network policies) — all remain unchecked.

**Action:** Implement each item and check them off:
- Mount secrets as Docker secrets or files
- Don't expose PostgreSQL port in production compose
- Add JWT rotation mechanism
- Add network policies (Docker networks at minimum)

### 3.10 Budget period resets not automated

No cron/scheduler resets monthly budgets. Budget enforcement will incorrectly deny requests after month boundary.

**Action:** Add a monthly reset job. Can use a simple timestamp check in the budget middleware.

---

## 4. P3 — Growth & Long-Term

### 4.1 Phase 2 roadmap items

| Item | Description |
|------|-------------|
| Service mesh (Istio/Linkerd) | Add service mesh for traffic management, observability, and security |
| Centralized logging (ELK/Loki) | Aggregate logs from all 8 services into a single queryable store |
| Metrics aggregation | Centralize Prometheus metrics from all services |
| Multi-tenant deployment | Add workspace isolation at the platform level |

### 4.2 Phase 3 roadmap items

| Item | Description |
|------|-------------|
| Kubernetes production manifests | Current K8s manifests are early-stage stubs |
| Auto-scaling | Horizontal pod autoscaling based on request volume |
| Backup/DR strategy | Automated database backups, point-in-time recovery |
| Security hardening | mTLS between services, network policies, pod security |

### 4.3 Terraform improvements

`terraform/main.tf` defines AWS VPC, EKS, RDS, ElastiCache, S3 but is a single file with no modules.

**Action:** Refactor into Terraform modules:
- `modules/vpc/` — networking
- `modules/eks/` — Kubernetes cluster
- `modules/rds/` — PostgreSQL with pgvector
- `modules/elasticache/` — Redis
- `modules/s3/` — document storage

### 4.4 Add health check endpoints per service

Only the API gateway has aggregated health. Individual services should expose their own `/health` endpoints checking their dependencies (DB, Redis).

**Action:** Add `/health` and `/health/ready` to each service using the shared `HealthResponse` model.

### 4.5 Document processing pipeline enhancement

Current pipeline: upload -> parse -> chunk -> embed -> store. Missing:
- Language detection
- Image extraction from PDFs
- Table extraction and structured storage
- Metadata extraction (author, date, title)

**Action:** Add processing stages. Make the pipeline configurable (enable/disable stages per document type).

### 4.6 Multi-provider embedding support

Retrieval service only uses OpenAI embeddings via the LLM Gateway.

**Action:** Support multiple embedding providers (already defined in GroundTruth's factory pattern). Allow per-collection embedding model configuration.

### 4.7 Evaluation framework enhancement

Current eval service has 3 judges: semantic match, citation check, refusal check.

**Action:** Add judges for:
- **Faithfulness** — does the answer faithfully reflect the sources?
- **Relevance** — is the answer relevant to the question?
- **Completeness** — does the answer cover all aspects of the question?
- **Conciseness** — is the answer appropriately concise?

### 4.8 WebSocket support

Currently all communication is REST + SSE. No WebSocket support.

**Action:** Add WebSocket endpoints for real-time document processing status, query progress, and trace streaming.

---

## 5. Implementation Priority Order

```
 1. Fix broken imports (app.db.base_class -> app.db.session)       (4 models can't load)
 2. Replace in-memory stores with PostgreSQL queries                (architecture gap)
 3. Refactor services to use shared model library                   (eliminate duplication)
 4. Fix K8s ConfigMap ports                                         (deployment broken)
 5. Fix frontend types to use shared-ts package                     (eliminate duplication)
 6. Delete duplicate nginx.conf                                     (dead code)
 7. Add per-service unit tests                                      (0% coverage on most services)
 8. Add dependency injection for settings                           (testability)
 9. Cache provider instances in LLM Gateway                         (performance)
10. Share Redis connection in LLM Gateway                           (resource waste)
11. Implement Redis-based task queue for ingestion                  (data loss on restart)
12. Add CORS to all services                                        (cross-origin issues)
13. Move hardcoded model names to config                            (configurability)
14. Implement LLM Gateway streaming                                 (feature gap)
15. Implement trace replay execution                                (placeholder removal)
16. Implement security checklist items                              (production readiness)
17. Build Kubernetes production manifests                           (deployment)
18. Implement Phase 2 roadmap items                                 (operational maturity)
```
