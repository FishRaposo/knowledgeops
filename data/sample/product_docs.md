# Acme Corp Product Documentation

## Product Lineup

### AcmeFlow - Workflow Automation

AcmeFlow is our flagship workflow automation platform designed for enterprise customers. It enables teams to design, deploy, and monitor automated workflows without writing code.

**Key Features:**
- Visual workflow builder with drag-and-drop interface
- 200+ pre-built connectors for popular SaaS applications
- Real-time monitoring and alerting
- Role-based access control
- Audit trail and compliance reporting

**Pricing Tiers:**
| Tier | Price | Workflows | Users |
|------|-------|-----------|-------|
| Starter | $49/mo | 10 | 5 |
| Professional | $149/mo | 50 | 25 |
| Enterprise | Custom | Unlimited | Unlimited |

### AcmeInsight - Analytics Dashboard

AcmeInsight provides real-time business intelligence with customizable dashboards and automated reporting.

**Key Features:**
- 50+ chart types and visualization options
- Scheduled report generation (daily, weekly, monthly)
- Data connectors for SQL, APIs, and flat files
- Anomaly detection with ML-powered alerts
- Embedded analytics via iframe or SDK

**API Rate Limits:**
- Starter: 100 requests/minute
- Professional: 1,000 requests/minute
- Enterprise: 10,000 requests/minute

### AcmeVault - Document Management

AcmeVault is a secure document management system with version control, collaboration, and compliance features.

**Key Features:**
- Document versioning with full history
- Granular permission controls
- OCR scanning for searchable PDFs
- eSignature integration
- Retention policies and legal hold

## Integration Guide

### Authentication

All Acme APIs use OAuth 2.0 with bearer tokens. Obtain your client ID and secret from the developer portal.

```bash
curl -X POST https://api.acme.com/oauth/token \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

### Base URL

All API requests should be made to: `https://api.acme.com/v2/`

### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource does not exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Support

- **Documentation:** docs.acme.com
- **Status Page:** status.acme.com
- **Support Email:** support@acme.com
- **SLA:** 99.9% uptime guarantee for Enterprise tier
