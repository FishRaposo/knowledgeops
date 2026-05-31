# Security Guide

## Secrets Management

### Microservices Secrets

Each service loads secrets from environment:

```bash
# Auth Service
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Database
DATABASE_PASSWORD=secure-password

# LLM Gateway (in services/llm-gateway/.env)
OPENAI_API_KEY=sk-...
```

### Docker Secrets (Production)

```yaml
# docker-compose.prod.yml
secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
```

### RBAC

Default roles:
- `admin`: Full access
- `user`: Standard access
- `viewer`: Read-only

## Security Checklist

- [ ] Secrets mounted as files, not env vars
- [ ] Database not exposed to internet
- [ ] JWT secrets rotated monthly
- [ ] Network policies between services
