# Architecture

## System Overview

KnowledgeOps is a microservices platform composed of 8 application services and 3 infrastructure services, communicating through an API Gateway pattern.

## Service Topology

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web App<br/>Next.js :3000]
    end

    subgraph "Gateway Layer"
        NGINX[Nginx<br/>:80]
        GW[API Gateway<br/>FastAPI :8000]
    end

    subgraph "Application Services"
        AUTH[Auth Service<br/>:8001]
        INGEST[Ingestion Service<br/>:8002]
        RETRIEVE[Retrieval Service<br/>:8003]
        LLM[LLM Gateway<br/>Express :8004]
        EVAL[Eval Service<br/>:8005]
        TRACE[Trace Service<br/>:8006]
    end

    subgraph "Infrastructure"
        DB[(PostgreSQL<br/>+ pgvector :5432)]
        REDIS[(Redis<br/>:6379)]
    end

    subgraph "External"
        OPENAI[OpenAI API]
    end

    WEB --> NGINX
    NGINX --> GW
    GW --> AUTH
    GW --> INGEST
    GW --> RETRIEVE
    GW --> EVAL
    GW --> TRACE
    RETRIEVE --> LLM
    EVAL --> LLM
    INGEST --> LLM
    LLM --> OPENAI
    INGEST --> DB
    INGEST --> REDIS
    RETRIEVE --> DB
    RETRIEVE --> REDIS
    AUTH --> DB
    TRACE --> DB
    EVAL --> DB
    LLM --> REDIS
```

## Inter-Service Communication

### Synchronous (HTTP/REST)

| From | To | Purpose |
|------|----|---------|
| Web App | API Gateway | All client requests |
| API Gateway | Auth Service | Token validation, user lookup |
| API Gateway | Ingestion Service | Document upload, status check |
| API Gateway | Retrieval Service | Query execution |
| API Gateway | Eval Service | Eval run management |
| API Gateway | Trace Service | Trace queries |
| Retrieval Service | LLM Gateway | Answer generation |
| Ingestion Service | LLM Gateway | Embedding generation |
| Eval Service | LLM Gateway | Judge LLM calls |

### Asynchronous (Redis Queue)

| Publisher | Consumer | Purpose |
|-----------|----------|---------|
| Ingestion Service | Ingestion Worker | Document processing pipeline |
| Trace Service | — | Span ingestion batching |

## Data Flow

### Document Ingestion Flow

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant ING as Ingestion Service
    participant W as Ingestion Worker
    participant LLM as LLM Gateway
    participant DB as PostgreSQL
    participant R as Redis

    U->>GW: POST /api/documents/upload
    GW->>ING: Forward request
    ING->>DB: Store document metadata
    ING->>R: Enqueue processing job
    ING-->>GW: 202 Accepted (job_id)
    GW-->>U: 202 Accepted

    R->>W: Dequeue job
    W->>ING: Parse document (PDF/MD/HTML/DOCX)
    W->>W: Chunk text with overlap
    W->>W: Deduplicate chunks
    W->>LLM: Generate embeddings
    LLM-->>W: Embedding vectors
    W->>DB: Store chunks + embeddings
    W->>DB: Update document status
```

### Query & Retrieval Flow

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant RET as Retrieval Service
    participant LLM as LLM Gateway
    participant DB as PostgreSQL
    participant TR as Trace Service

    U->>GW: POST /api/query
    GW->>RET: Forward query
    RET->>LLM: Generate query embedding
    LLM-->>RET: Query vector
    RET->>DB: Vector similarity search
    RET->>DB: Full-text keyword search
    RET->>RET: Hybrid score fusion
    RET->>RET: Rerank results
    RET->>RET: Assemble citations
    RET->>LLM: Generate grounded answer
    LLM-->>RET: Answer with citations
    RET->>TR: Log trace span
    RET-->>GW: Answer response
    GW-->>U: Answer + citations + metadata
```

## Database Schema

### Core Tables

```sql
-- Documents and chunks
documents (id, title, source, content_hash, version, status, created_at, updated_at)
chunks (id, document_id, content, chunk_index, embedding, metadata, created_at)

-- Users and auth
users (id, email, name, role, created_at)
api_keys (id, user_id, key_hash, name, last_used_at, created_at)

-- Evaluation
eval_runs (id, name, status, config, started_at, completed_at)
eval_results (id, run_id, query, expected, actual, scores, created_at)

-- Traces
traces (id, trace_id, service, operation, duration_ms, metadata, created_at)
trace_spans (id, trace_id, span_id, parent_span_id, operation, start_time, end_time, attributes)
```

## Design Decisions

### Monorepo with Docker Compose

A monorepo was chosen over polyrepo because all services share database schemas, Pydantic models, and deployment configuration. Docker Compose provides the simplest local development experience while remaining compatible with production orchestrators.

### API Gateway Pattern

The gateway centralizes authentication, routing, and health aggregation. This keeps individual services focused on their domain logic while providing a single entry point for the frontend.

### LLM Gateway as Separate Service

Isolating LLM calls behind a gateway enables provider swapping, response caching, budget enforcement, and cost tracking without modifying downstream services.

### PostgreSQL + pgvector

Using pgvector for embeddings avoids operational complexity of a separate vector database while providing sufficient performance for internal tooling workloads.
