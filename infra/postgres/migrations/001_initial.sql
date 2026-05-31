CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS schema_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(64) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO schema_versions (version, description) VALUES
    ('001_initial', 'Initial KnowledgeOps tables for auth, ingestion, eval, trace, and cost tracking')
ON CONFLICT (version) DO NOTHING;
