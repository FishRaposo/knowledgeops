# Deployment Targets

## AWS ECS

Build each service image with the existing Dockerfiles and push them to ECR. Run PostgreSQL with pgvector on RDS, Redis on ElastiCache, and place the API Gateway plus Web App behind an Application Load Balancer. Store `OPENAI_API_KEY`, `JWT_SECRET`, database URLs, and Redis URLs in AWS Secrets Manager.

## GCP Cloud Run

Deploy stateless services to Cloud Run using the per-service Dockerfiles. Use Cloud SQL for PostgreSQL with pgvector support, Memorystore for Redis, and Secret Manager for provider keys and JWT secrets. Route public traffic through the API Gateway and serve the web app as the default frontend service.

## Bare Metal

Use `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` on a Linux host. Terminate TLS in an external reverse proxy, mount persistent volumes for PostgreSQL and Redis, and configure log shipping from container stdout.

## Production Checklist

- Set non-default `JWT_SECRET`.
- Configure real provider keys or keep mock providers for demo-only deployments.
- Back up PostgreSQL volumes.
- Enable Prometheus scraping for `/metrics` where available.
- Restrict admin endpoints to trusted users through the Auth Service RBAC roles.
