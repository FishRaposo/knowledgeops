# Quickstart Guide

## Prerequisites

Ensure you have the following installed:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2)
- 4GB+ RAM available for Docker
- An OpenAI API key

## Step 1: Clone and Configure

```bash
git clone <repo-url> knowledgeops
cd knowledgeops

cp .env.example .env
```

Edit `.env` and set your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-actual-key-here
```

## Step 2: Start All Services

```bash
docker compose up --build
```

This will:

1. Build all 8 application service containers
2. Start PostgreSQL with pgvector
3. Start Redis
4. Start Nginx reverse proxy
5. Initialize the database schema

Wait for all services to report healthy (typically 30-60 seconds on first run).

## Step 3: Access the Platform

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost |
| **API Documentation** | http://localhost/api/docs |
| **API Gateway Health** | http://localhost/api/health |

## Step 4: Upload a Document

Using the UI:

1. Navigate to **Documents** in the sidebar
2. Click **Upload**
3. Select a file (PDF, Markdown, HTML, or DOCX)
4. Wait for processing to complete

Using the API:

```bash
curl -X POST http://localhost/api/documents/upload \
  -F "file=@data/sample/company_handbook.md"
```

## Step 5: Query Your Documents

Using the UI:

1. Navigate to **Chat** in the sidebar
2. Type a question about your uploaded documents
3. View the answer with citations

Using the API:

```bash
curl -X POST http://localhost/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the company refund policy?", "top_k": 5}'
```

## Step 6: Run an Evaluation

Using the UI:

1. Navigate to **Evals** in the sidebar
2. Select the sample eval suite
3. Click **Run**
4. View the results and scores

Using the API:

```bash
curl -X POST http://localhost/api/evals/run \
  -H "Content-Type: application/json" \
  -d '{"suite_path": "data/sample/eval_suites/basic_rag.yaml"}'
```

## Step 7: View Traces

1. Navigate to **Traces** in the sidebar
2. Browse recent traces from your queries and evals
3. Click a trace to see the full span detail

## Step 8: Check Costs

1. Navigate to **Costs** in the sidebar
2. View spending breakdown by service, model, and time period

## Troubleshooting

### Services won't start

```bash
# Check logs for a specific service
docker compose logs api-gateway
docker compose logs ingestion-service

# Restart a specific service
docker compose restart retrieval-service
```

### Database connection errors

```bash
# Check if PostgreSQL is ready
docker compose logs db

# Manually verify the connection
docker compose exec db psql -U knowledgeops -c "SELECT 1"
```

### Out of memory

Increase Docker's memory allocation in Docker Desktop settings (recommended: 4GB+).

### Port conflicts

If ports 80, 3000, 5432, 6379, or 8000-8006 are in use, edit `.env` to use different ports.
