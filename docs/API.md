# KnowledgeOps API

KnowledgeOps exposes service APIs through the API Gateway. Local web clients should set `NEXT_PUBLIC_API_URL=/api` and may set `NEXT_PUBLIC_DEMO_TOKEN=dev-admin-token` only when the gateway runs with `ALLOW_DEV_AUTH=true`.

Production callers must send `Authorization: Bearer <jwt>` on every `/api/*` request. Admin routes require the verified user role to be `admin`.

## Gateway Routes

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Aggregated service health. |
| `GET` | `/api/documents` | Returns `{ "documents": [...] }`. |
| `POST` | `/api/documents/upload` | Multipart `file` upload; returns `{ "document": {...} }`. |
| `POST` | `/api/query` | Runs retrieval plus grounded generation and returns answer, citations, confidence, refusal fields, and chunk ids. |
| `POST` | `/api/evals/run` | Runs an eval suite and returns `{ "eval_run": {...} }`. |
| `GET` | `/api/evals` | Returns `{ "evals": [...] }`. |
| `GET` | `/api/traces?service=<name>` | Returns `{ "traces": [...] }` with optional service filtering. |
| `GET` | `/api/costs` | Returns total spend, tokens, `by_service`, `by_model`, `by_user`, and `costs`. |
| `GET` | `/api/alerts` | Returns budget and service failure alerts. |
| `GET` | `/api/admin/users` | Admin-only user list, `{ "users": [...] }`. |
| `GET` | `/api/admin/health` | Admin-only health overview. |
| `POST` | `/api/admin/keys` | Admin-only API key creation. |

## Request Examples

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/documents
```

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the refund policy?","top_k":5}'
```

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@data/sample/policies/refund_policy.md"
```

Each FastAPI service also serves an OpenAPI schema at `/openapi.json` and Swagger UI at `/docs` when running locally.
