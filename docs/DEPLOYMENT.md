# Deployment

## Local Development

The simplest way to run KnowledgeOps is with Docker Compose:

```bash
cp .env.example .env
# Edit .env with your API keys
docker compose up --build
```

This starts all 11 services. The frontend is available at `http://localhost`.

## Production Deployment

### Prerequisites

- A host or cluster with Docker and Docker Compose v2+
- At least 4GB RAM and 2 CPU cores
- PostgreSQL 16+ with pgvector extension (or use the included container)
- An OpenAI API key (or compatible provider)

### Step 1: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with production values:

| Variable | Production Guidance |
|----------|-------------------|
| `JWT_SECRET` | Generate with `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | Strong random password |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `ENVIRONMENT` | Set to `production` |
| `LOG_LEVEL` | Set to `WARNING` or `INFO` |

### Step 2: Resource Limits

Create `docker-compose.override.yml` with resource limits:

```yaml
services:
  api-gateway:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.5"
  ingestion-service:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: "1.0"
  retrieval-service:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: "1.0"
  llm-gateway:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.5"
```

### Step 3: SSL/TLS Termination

For production, place an Nginx reverse proxy or load balancer in front with TLS:

```nginx
server {
    listen 443 ssl http2;
    server_name knowledgeops.yourcompany.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    location / {
        proxy_pass http://knowledgeops-web:3000;
    }

    location /api/ {
        proxy_pass http://knowledgeops-gateway:8000;
    }
}
```

### Step 4: Database Backups

Set up periodic PostgreSQL backups:

```bash
# Manual backup
docker compose exec db pg_dump -U knowledgeops knowledgeops > backup.sql

# Restore
docker compose exec -T db psql -U knowledgeops knowledgeops < backup.sql
```

### Step 5: Monitoring

Add health check monitoring to all services:

```yaml
services:
  api-gateway:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Cloud Deployment

### AWS ECS

1. Build and push images to ECR
2. Create ECS task definitions for each service
3. Use Application Load Balancer for routing
4. Use RDS for PostgreSQL with pgvector extension
5. Use ElastiCache for Redis

### GCP Cloud Run

1. Build and push images to Artifact Registry
2. Deploy each service as a Cloud Run service
3. Use Cloud SQL for PostgreSQL with pgvector
4. Use Memorystore for Redis
5. Use Cloud Load Balancing for routing

### Bare Metal / VM

1. Install Docker and Docker Compose on the host
2. Clone the repository
3. Configure `.env`
4. Run `docker compose up -d`
5. Set up Nginx with TLS as reverse proxy
6. Configure systemd for service management

## Scaling Considerations

| Service | Scaling Strategy |
|---------|-----------------|
| Web App | Stateless, scale horizontally |
| API Gateway | Stateless, scale horizontally behind LB |
| Ingestion Service | Scale workers independently |
| Retrieval Service | Scale horizontally, share DB connection pool |
| LLM Gateway | Stateless, scale horizontally |
| Eval Service | Scale based on eval queue depth |
| Trace Service | Scale based on ingest volume |
| PostgreSQL | Vertical scaling, read replicas for queries |
| Redis | Cluster mode for high availability |
