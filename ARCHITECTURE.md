# KnowledgeOps Architecture

## Overview

Integrated AI platform combining 8 microservices into a single deployable system.

## Service Map

| Service | Port | Purpose | Dependencies |
|---------|------|---------|-------------|
| db | 5432 | PostgreSQL + pgvector | — |
| redis | 6379 | Cache / queues | — |
| gateway | 8000 | API gateway | db, redis |
| auth | 8001 | Authentication | db |
| ingestion | 8002 | Document ETL | db, redis |
| retrieval | 8003 | Search / RAG | db |
| llm-gateway | 8004 | LLM proxy | redis |
| eval | 8005 | Evaluation | db |
| trace | 8006 | Observability | db, redis |
| web-app | 3000 | Next.js frontend | gateway |
| nginx | 80 | Reverse proxy | gateway, web-app |

## Deployment

```bash
docker compose up -d
```

## Health Checks

Every service exposes a `/health` endpoint. Docker Compose waits for dependencies before starting dependents.
