# KnowledgeOps Setup Guide

## Prerequisites

- Docker 24+
- Docker Compose 2.x

## Start All Services

```bash
docker compose up -d
```

## Verify Services

```bash
docker compose ps
```

## Access Points

- Web App: http://localhost
- API Gateway: http://localhost/api/
- Individual services (direct access):
  - Gateway: http://localhost:8000
  - Auth: http://localhost:8001
  - Ingestion: http://localhost:8002
  - Retrieval: http://localhost:8003
  - LLM Gateway: http://localhost:8004

## Logs

```bash
docker compose logs -f gateway
```

## Stop

```bash
docker compose down
```
