# ADR 0001: Service Boundaries

## Status

Accepted

## Context

KnowledgeOps combines ingestion, retrieval, LLM routing, evaluation, tracing, authentication, and web administration. Keeping these responsibilities in one service would make demos easier to start but would hide the platform architecture concerns the project is intended to demonstrate.

## Decision

Keep separate services for auth, ingestion, retrieval, LLM gateway, eval, trace, API gateway, and web app. Services communicate through HTTP APIs routed by the API gateway and share common model/config helpers through the shared packages.

## Consequences

Each service can be tested and deployed independently, and portfolio reviewers can inspect clear ownership boundaries. Local development uses Docker Compose to reduce operational overhead.
