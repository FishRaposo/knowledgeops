# Contributing to KnowledgeOps

## Monorepo Architecture

KnowledgeOps is a monorepo containing multiple microservices that form a complete AI knowledge platform. Each service is independently deployable and communicates through the API Gateway.

```
knowledgeops/
├── services/          # Individual microservices
│   ├── web-app/       # Next.js frontend (port 3000)
│   ├── api-gateway/   # FastAPI request router (port 8000)
│   ├── auth-service/  # Auth, API keys, RBAC (port 8001)
│   ├── ingestion-service/  # Document processing (port 8002)
│   ├── retrieval-service/  # Search and RAG (port 8003)
│   ├── llm-gateway/   # LLM provider proxy (port 8004)
│   ├── eval-service/  # Evaluation harness (port 8005)
│   └── trace-service/ # Observability (port 8006)
├── shared/            # Shared libraries
│   ├── python/        # Common Python utilities (config, logging, models)
│   └── ts/            # Shared TypeScript interfaces and API client
├── infra/             # Infrastructure config (postgres, nginx)
├── data/              # Sample data and eval suites
├── tests/             # Integration tests
└── docs/              # Documentation
```

## Service Descriptions

### Python Services (FastAPI)

| Service | Description |
|---------|-------------|
| **api-gateway** | Central entry point that routes requests to downstream services. Handles authentication forwarding, request aggregation, and health checks. |
| **auth-service** | Manages user accounts, API key generation/revocation, JWT token exchange, and role-based access control (admin/user/viewer). |
| **ingestion-service** | Parses documents (PDF, Markdown, HTML, DOCX), chunks text, generates embeddings via the LLM Gateway, deduplicates content, and manages document versions. |
| **retrieval-service** | Hybrid search combining vector similarity and keyword matching. Reranks results and assembles citations for RAG responses. |
| **eval-service** | Runs automated RAG evaluations including semantic match scoring, citation verification, and refusal detection using LLM judges. |
| **trace-service** | Collects request-level traces across all services. Stores and replays traces for debugging and evaluation. |

### TypeScript Services

| Service | Description |
|---------|-------------|
| **web-app** | Next.js frontend with chat interface, document browser, eval dashboard, trace viewer, cost analytics, and admin panel. |
| **llm-gateway** | Express proxy for LLM provider calls. Handles provider routing, response caching (Redis), budget enforcement, and request logging. |

## Getting Started

```bash
# Install all dependencies
make install

# Start all services
make dev

# Run integration tests
make test

# Check code quality
make lint
```

## Adding a New Service

1. **Create the service directory** under `services/`:
   - Python: include `pyproject.toml`, `Dockerfile`, `app/main.py`
   - TypeScript: include `package.json`, `Dockerfile`, `tsconfig.json`, `src/`

2. **Define the service in `docker-compose.yml`** with appropriate port, environment variables, and health checks.

3. **Add the service to the Makefile** install target.

4. **Register routes** in the API Gateway if the service exposes public endpoints.

5. **Add shared dependencies**: If your service needs common utilities, import from `shared/python/` or `shared/ts/`.

6. **Write tests**: Unit tests go in `services/<service>/tests/`. Integration tests go in `tests/`.

## Testing

- **Unit tests**: Run per-service with `cd services/<service> && pytest tests/ -v` (Python) or `npm test` (TypeScript).
- **Integration tests**: Require `docker compose up -d` first, then `pytest tests/ -v`.
- All PRs should include tests for new functionality.

## Code Style

- **Python**: 4-space indentation, follow PEP 8. Format with `ruff format`, lint with `ruff check`.
- **TypeScript**: 2-space indentation. Format with Prettier.
- **Commits**: Conventional commit messages preferred (`feat:`, `fix:`, `docs:`, etc.).
- No inline comments unless strictly necessary for clarity.
