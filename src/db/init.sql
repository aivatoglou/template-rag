CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content    TEXT NOT NULL,
    embedding  VECTOR(3072),
    source     TEXT NOT NULL,
    source_url TEXT NOT NULL UNIQUE,
    title      TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
