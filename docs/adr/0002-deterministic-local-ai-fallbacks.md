# ADR 0002: Deterministic Local AI Fallbacks

## Status

Accepted

## Context

The platform integrates external AI services, but portfolio tests and demos must run without requiring paid provider credentials.

## Decision

Every AI-facing subsystem keeps a deterministic local mode: mock LLM gateway responses, local reranking heuristics, deterministic eval judges, and refusal behavior based on retrieval confidence.

## Consequences

The stack can be tested in CI and during interviews without secrets. Production deployments can still point the same interfaces at real providers through environment configuration.
