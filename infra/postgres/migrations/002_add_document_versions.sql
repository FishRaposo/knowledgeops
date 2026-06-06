-- Migration 002: Add document_versions audit table
CREATE TABLE IF NOT EXISTS document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, version_number)
);

INSERT INTO schema_versions (version, description) VALUES
    ('002_add_document_versions', 'Add document_versions audit table')
ON CONFLICT (version) DO NOTHING;
