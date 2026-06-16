# AGENTS.md — knowledgeops

## What This Is

The KnowledgeOps capstone: an 8-service platform that integrates document ingestion,
hybrid retrieval + grounded RAG, automated evaluation, distributed tracing, and an LLM
gateway behind a Next.js console. It is the "final boss" showcase project — the one that
ties the other portfolio concepts together. Migrated out of `General Projects/` onto the
`shared_core` standard.

## Layout (multi-service)

```
knowledgeops/
├── services/
│   ├── api-gateway/      app/   (FastAPI; router + health aggregator)
│   ├── auth-service/     app/   (FastAPI; JWT + RBAC, alembic)
│   ├── ingestion-service/ app/  (FastAPI + arq worker; parsing/chunking/dedup)
│   ├── retrieval-service/ app/  (FastAPI; hybrid search, citation, generation)
│   ├── eval-service/     app/   (FastAPI; semantic/citation/refusal judges)
│   ├── trace-service/    app/   (FastAPI; collector/storage/replay)
│   ├── llm-gateway/      src/   (TypeScript/Express — KEPT as-is)
│   └── web-app/          src/   (Next.js — KEPT as-is)
├── shared/
│   ├── python/shared/    (knowledgeops-shared: domain DTO models ONLY)
│   └── ts/               (frontend TS types — KEPT as-is)
├── examples/run_demo.py  (offline shared-core pipeline demo)
├── infra/  k8s/  terraform/  data/  docs/
├── docker-compose.yml    (db=knowledgeops_postgres, redis=knowledgeops_redis + 8 services)
├── Makefile  ruff.toml  pyrightconfig.json  requirements.txt  .env.example
└── .github/workflows/ci.yml
```

**Layout note:** each Python service keeps `app/` as its package (not `src/<pkg>/`). This is
the established per-service convention here; tests run from inside each service dir so `app`
resolves. This is a documented exception to the flat `src/<package>/` template layout.

## shared-core adoption (the deep refactor)

The old `shared/python` infra reimplementation was **deleted** and replaced by `shared_core`:

| Old (`shared/python`) | Now |
|---|---|
| `shared.config.BaseServiceSettings` (lowercase fields) | `shared_core.config.BaseAppConfig` (UPPERCASE `DATABASE_URL`/`REDIS_URL`/`LOG_LEVEL`); each service subclasses it |
| `shared.db.create_async_engine_and_session` / `is_db_available` | `shared_core.database.AsyncDatabaseManager` (its URL rewrite now handles plain `postgresql://`) |
| `shared.logging.configure_logging` | `shared_core.logging.setup_logging` + each `main.py` registers `application_error_handler` |
| `shared.health.HealthResponse` | services return a light `/health`; `shared_core.health.async_check_health` available |
| `shared.config.estimate_cost` / `MODEL_PRICING` | `shared_core.pricing.calculate_cost` |
| `shared.models.TraceSpan` / `CostRecord` | also in `shared_core.tracing` (kept in `shared.models` for compatibility) |

`shared/python` now ships **only** the cross-service domain DTOs (`Document`, `Chunk`,
`Citation`, `QueryRequest/Response`, `User`, `EvalRun`, `EvalResult`, `DocumentStatus`).

## Commands

```bash
make install      # pip install -e '../shared-core[docparse,embeddings]'; pip install -e shared/python; pip install -r requirements.txt
make test         # run each Python service's pytest (cd services/<svc> && pytest)
make lint         # ruff check services shared/python
make format       # ruff format services shared/python
make typecheck    # pyright per service
make docker-up    # docker compose up -d (pgvector + redis + 8 services + nginx)
make demo         # python examples/run_demo.py (offline shared-core pipeline)
make worker       # ingestion arq worker
make clean        # remove caches
```

Local verification uses a single `.venv` at the repo root (shared-core + knowledgeops-shared
+ `requirements.txt`). Each service's unit tests are run from its own directory so the six
`app` packages don't collide.

## Current State

**Functional, migrated, green.** All six Python services adopt `shared_core` for
config/logging/errors/DB and route pricing through `shared_core.pricing`. Unit tests pass
(api-gateway 1, auth 1, ingestion 2, retrieval 2, eval 2, trace 2 = 10). `ruff check`/`ruff
format --check` clean. `make demo` runs the ingestion→retrieval→cost→eval pipeline offline.
The TypeScript llm-gateway and Next.js web-app are unchanged (meta-structure only).

## Domain-convergence status

**Adopted (golden-gated, safe):**
- `ingestion-service/app/processing/deduplication.py::compute_hash` now delegates to
  `shared_core.docparse.compute_hash`. Byte-identical; gated by
  `ingestion-service/tests/test_convergence.py`.

**Added capability:**
- Every Python service exposes `GET /ready`, a readiness probe that re-checks the database
  with bounded exponential backoff via `shared/python/shared/readiness.py`
  (`probe_database` / `readiness_payload`).
- `trace-service` `GET /traces/costs` route ordering fixed (was shadowed by
  `/traces/{trace_id}`); regression-tested.

**Still deferred (would change numeric/structural output — needs golden gating):**
- `ingestion-service/app/parsers/*` + `processing/chunking` → `shared_core.docparse`
  (parser metadata shape differs).
- `eval-service/app/judges/*` → `shared_core.evaljudge` (`JudgeResult` vs float-score).
- `retrieval-service`/`eval-service` cosine similarity → `shared_core.embeddings`
  (numpy vs pure-python differ by ~1e-16; rounded values match but the raw return could
  flip the 4th decimal in rare cases).
- `trace-service` cost records → `shared_core.tracing.CostRecord` (field names differ).

## When to Update This AGENTS.md

- A service is added/removed or its `app/` layout changes
- The shared-core adoption surface changes (new module adopted, signature change)
- Makefile targets, docker-compose services, or CI steps change
- `shared/python` domain models change
