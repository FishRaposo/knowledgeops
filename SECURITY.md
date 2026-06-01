# KnowledgeOps Security Checklist

## Authentication & Authorization
- [x] JWT tokens with `iss`, `aud`, `jti`, `exp`, `iat` claims
- [x] Strict JWT validation (issuer, audience, required claims)
- [x] Role-based access control (RBAC) with hierarchy
- [x] API key hashing (SHA-256)

## Data Protection
- [x] PostgreSQL with SSL in production
- [x] Redis with AUTH in production
- [x] No secrets committed to repository

## Network Security
- [x] CORS configured on API Gateway
- [x] Service-to-service communication via internal network
- [ ] TLS termination at nginx/ingress
- [ ] Rate limiting on public endpoints

## Infrastructure
- [x] Kubernetes ConfigMap with correct service ports
- [ ] NetworkPolicies for pod isolation
- [ ] Resource quotas and limits
- [ ] PodSecurityPolicies / OPA Gatekeeper

## Observability
- [x] Distributed tracing with trace spans
- [x] Health endpoints on all services
- [x] Budget alerts for LLM spend
- [ ] Audit logging for auth events

## Dependencies
- [ ] Automated vulnerability scanning (Dependabot/Snyk)
- [ ] SBOM generation
- [ ] Regular dependency updates

## Secrets Management
- [ ] Kubernetes External Secrets / Vault integration
- [ ] OpenAI API key rotation policy
- [ ] Database credential rotation
