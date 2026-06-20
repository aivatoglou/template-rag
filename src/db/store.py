"""pgvector store: upsert documents and hybrid search."""

import os
from typing import Generator
from contextlib import contextmanager

import psycopg
from pgvector.psycopg import register_vector

from .models import DocChunk, SearchResult

RRF_K = 60


@contextmanager
def _db() -> Generator[psycopg.Connection, None, None]:
    _db_url = "postgresql://{user}:{password}@{host}/{db}".format(
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        db=os.environ["POSTGRES_DB"],
    )
    with psycopg.connect(_db_url) as conn:
        register_vector(conn)
        yield conn

# Deduplicate on source_url by updating existing records with the new content, embeddings, and titles.
# While a production environment might require more complex versioning, this handles basic upserts.
def upsert_chunks(chunks: list[DocChunk]) -> int:
    sql = """
        INSERT INTO documents (content, embedding, source, source_url, title)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (source_url) DO UPDATE
            SET content   = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                title     = EXCLUDED.title
    """
    with _db() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, [(c.content, c.embedding, c.source, c.source_url, c.title) for c in chunks])
    return len(chunks)


def _vector_search(cur: psycopg.Cursor, embedding: list[float], source: str, k: int) -> list[SearchResult]:
    cur.execute("""
        SELECT content, source, source_url, title,
               1 - (embedding <=> %s::vector) AS score
        FROM documents
        WHERE source = %s AND embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (embedding, source, embedding, k))
    return [SearchResult(content=r[0], source=r[1], source_url=r[2], title=r[3], score=r[4]) for r in cur.fetchall()]


def _keyword_search(cur: psycopg.Cursor, query: str, source: str, k: int) -> list[SearchResult]:
    # Hardcoded to english, which causes sub-optimal stemming for documents in otehr languages.
    # Optimization: Detect document language during ingestion, store it in the database, 
    # and dynamically pass the matching language configuration.
    cur.execute("""
        SELECT content, source, source_url, title,
               ts_rank(to_tsvector('english', content), plainto_tsquery('english', %s)) AS score
        FROM documents
        WHERE source = %s
          AND to_tsvector('english', content) @@ plainto_tsquery('english', %s)
        ORDER BY score DESC
        LIMIT %s
    """, (query, source, query, k))
    return [SearchResult(content=r[0], source=r[1], source_url=r[2], title=r[3], score=r[4]) for r in cur.fetchall()]


def hybrid_search(embedding: list[float], query: str, source: str, k: int = 5) -> list[SearchResult]:
    with _db() as conn:
        with conn.cursor() as cur:
            vector_results = _vector_search(cur, embedding, source, k * 2)
            keyword_results = _keyword_search(cur, query, source, k * 2)

    scores: dict[str, float] = {}
    meta: dict[str, SearchResult] = {}

    # Combine semantic and keyword results using Reciprocal Rank Fusion (RRF).
    # RRF merges distinct ranked lists based purely on position, without the need 
    # to normalize the data coming from different scoring metrics.
    for rank, r in enumerate(vector_results):
        scores[r.source_url] = scores.get(r.source_url, 0) + 1 / (RRF_K + rank + 1)
        meta[r.source_url] = r

    for rank, r in enumerate(keyword_results):
        scores[r.source_url] = scores.get(r.source_url, 0) + 1 / (RRF_K + rank + 1)
        meta[r.source_url] = r

    # Sort the final list in descending order, favoring documents that appeared in both search results.
    ranked = sorted(scores, key=scores.__getitem__, reverse=True)[:k]
    return [meta[url] for url in ranked]


def count_docs() -> int:
    with _db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM documents")
            return cur.fetchone()[0]
