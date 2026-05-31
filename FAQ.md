# KnowledgeOps FAQ

## Q: How much RAM do I need?
**A:** Minimum 4GB for local Docker Compose. 8GB recommended for all services running simultaneously.

## Q: Can I deploy to Kubernetes?
**A:** Kubernetes manifests are on the roadmap (Phase 3). Currently use Docker Compose or Docker Swarm.

## Q: How do I update a single service?
**A:** `docker compose up -d --build <service_name>` rebuilds and restarts only that service.
