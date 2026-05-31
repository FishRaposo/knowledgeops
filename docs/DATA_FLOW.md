# Data Flow

## Overview

This document describes the data models and data flow patterns across the KnowledgeOps platform.

## Core Data Models

### Document

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| title | string | Document title |
| source | string | Original source URI or filename |
| content_hash | string | SHA-256 hash of raw content |
| version | integer | Incremented on re-ingestion |
| status | enum | `pending`, `processing`, `completed`, `failed` |
| metadata | JSON | Arbitrary key-value metadata |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

### Chunk

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| document_id | UUID | Foreign key to document |
| content | text | Chunk text content |
| chunk_index | integer | Position within document |
| embedding | vector(1536) | pgvector embedding |
| metadata | JSON | Token count, section info, etc. |
| content_hash | string | SHA-256 of chunk content |
| created_at | datetime | Creation timestamp |

### Query

| Field | Type | Description |
|-------|------|-------------|
| query | string | User's natural language question |
| top_k | integer | Number of results to retrieve |
| include_metadata | boolean | Whether to include chunk metadata |
| filters | JSON | Optional document-level filters |

### Answer

| Field | Type | Description |
|-------|------|-------------|
| answer | string | Generated response text |
| citations | list[Citation] | Source citations |
| refusal | boolean | Whether the system refused to answer |
| refusal_reason | string | Reason for refusal if applicable |
| chunks_used | list[UUID] | IDs of chunks used in generation |
| confidence | float | Overall confidence score |

### Citation

| Field | Type | Description |
|-------|------|-------------|
| chunk_id | UUID | Source chunk |
| document_id | UUID | Source document |
| document_title | string | Document title for display |
| excerpt | string | Relevant excerpt from chunk |
| relevance_score | float | Relevance to the claim |

## Data Flow Patterns

### Pattern 1: Document Ingestion

```
User Upload
    │
    ▼
API Gateway ──► Ingestion Service
                     │
                     ├── Store metadata (PostgreSQL)
                     ├── Enqueue job (Redis)
                     │
                     ▼
              Ingestion Worker
                     │
                     ├── Parse → raw text
                     ├── Chunk → chunk list
                     ├── Deduplicate (SHA-256 check)
                     ├── Embed (via LLM Gateway)
                     │        │
                     │        ▼
                     │   OpenAI API
                     │
                     └── Store chunks + embeddings (PostgreSQL)
```

### Pattern 2: Query & Retrieval

```
User Query
    │
    ▼
API Gateway ──► Retrieval Service
                     │
                     ├── Embed query (via LLM Gateway)
                     │
                     ├── Vector search (pgvector)
                     │   SELECT chunks, cosine_distance(embedding, $query_vec)
                     │   ORDER BY distance LIMIT $top_k
                     │
                     ├── Keyword search (tsvector)
                     │   SELECT chunks WHERE to_tsvector(content) @@ plainto_tsquery($query)
                     │
                     ├── Reciprocal rank fusion
                     │   Combine vector and keyword rankings
                     │
                     ├── Rerank (cross-encoder or LLM)
                     │   Score and sort final candidates
                     │
                     ├── Check threshold
                     │   ├── Above → Assemble citations, generate answer
                     │   └── Below → Return refusal
                     │
                     └── Return Answer + Citations + Metadata
```

### Pattern 3: Evaluation

```
Eval Suite (YAML)
    │
    ▼
Eval Service
    │
    ├── Load test cases
    │
    ├── For each test case:
    │   ├── Send query to Retrieval Service
    │   ├── Get actual answer + citations
    │   ├── Run judges:
    │   │   ├── Semantic Match (cosine similarity)
    │   │   ├── Citation Check (grounding verification)
    │   │   └── Refusal Check (appropriate refusal)
    │   └── Record scores
    │
    ├── Aggregate results
    │
    └── Generate markdown report
```

### Pattern 4: Trace Collection

```
Service Request
    │
    ├── Start span (service, operation, timestamp)
    │
    ├── Execute operation
    │
    ├── End span (duration, status, attributes)
    │
    └── POST /traces/ingest ──► Trace Service
                                      │
                                      └── Store in PostgreSQL
                                             │
                                             ▼
                                      Web App Trace Viewer
```

## Data Persistence

### PostgreSQL

All persistent data is stored in PostgreSQL with the pgvector extension for vector similarity search.

**Key indexes:**
- `chunks.embedding` — IVFFlat index for approximate nearest neighbor search
- `chunks.document_id` — B-tree for document-chunk joins
- `documents.content_hash` — B-tree for deduplication lookups
- `traces.trace_id` — B-tree for trace queries
- `traces.created_at` — B-tree for time-range queries

### Redis

Redis serves two purposes:

1. **Job queue** — `LIST` operations for the ingestion worker (`BRPOP`/`LPUSH`)
2. **LLM response cache** — `STRING` with TTL for caching LLM responses by request hash
