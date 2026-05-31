# Security Policy

**Last Updated:** March 1, 2024

## Purpose

This document outlines Acme Corporation's security policies and procedures for protecting company and customer data.

## Data Classification

### Public (Level 1)
- Marketing materials, public documentation, press releases
- No special handling required

### Internal (Level 2)
- Internal communications, project documentation, meeting notes
- Access restricted to Acme employees

### Confidential (Level 3)
- Customer data, financial records, employee PII
- Encrypted at rest and in transit, access logged

### Restricted (Level 4)
- Authentication credentials, encryption keys, security audit reports
- Vault-stored, multi-person access required

## Access Control

### Principle of Least Privilege

All system access follows the principle of least privilege. Users are granted only the minimum permissions necessary to perform their job functions.

### Authentication Requirements

- All accounts require multi-factor authentication (MFA)
- Passwords must be at least 16 characters with complexity requirements
- SSO is mandatory for all cloud services
- API keys must be rotated every 90 days

### Access Reviews

Access reviews are conducted quarterly. Managers must certify that all team members have appropriate access levels.

## Incident Response

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| P1 | Active data breach, system compromise | 15 minutes |
| P2 | Potential security vulnerability | 1 hour |
| P3 | Policy violation, suspicious activity | 4 hours |
| P4 | Security question, minor issue | 24 hours |

### Reporting

Report security incidents immediately to:
- **Email:** security@acme.com
- **Phone:** 1-800-ACME-SEC
- **Slack:** #security-incidents

## Encryption Standards

- **At rest:** AES-256
- **In transit:** TLS 1.3
- **Database:** Column-level encryption for PII
- **Backups:** AES-256 with separate key management

## Compliance

Acme maintains compliance with:
- SOC 2 Type II
- GDPR
- HIPAA (for healthcare customers)
- ISO 27001

## Training

All employees must complete security awareness training within 30 days of hire and annually thereafter. Additional role-specific training may be required based on data access levels.
