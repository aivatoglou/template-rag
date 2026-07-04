"""Ingestion pipeline."""

import os
import time
from typing import Generator

import tiktoken
from openai import AzureOpenAI, OpenAI, RateLimitError

from src.db.store import DocChunk, upsert_chunks

# text-embedding-3-large supports up to 8192 tokens per document. However, we truncate
# documents here to optimize processing speed during development. In production,
# documents should be properly chunked with an overlap strategy and embedded separately.
# Additionally, the batch size is capped to prevent hitting provider rate limits.
MAX_TOKENS = 500 # Restricting token length speeds up ingestion, particularly for long articles.
EMBED_BATCH_SIZE = 10 # Processes a maximum of 10 articles per source per run.

_enc = tiktoken.get_encoding("cl100k_base")

if os.environ.get("LLM_PROVIDER", "azure").lower() == "openrouter":
    _embed_deployment = os.environ.get("OPENROUTER_EMBEDDING_MODEL", "openai/text-embedding-3-large")
    _openai_client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
else:
    _embed_deployment = os.environ.get("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
    _openai_client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    )


def _truncate(text: str) -> str:
    tokens = _enc.encode(text)
    return _enc.decode(tokens[:MAX_TOKENS]) if len(tokens) > MAX_TOKENS else text


def _embed_batch(texts: list[str]) -> list[list[float]]:
    # Implement retry logic to handle rate limiting
    while True:
        try:
            response = _openai_client.embeddings.create(model=_embed_deployment, input=texts)
            return [item.embedding for item in response.data]
        except RateLimitError:
            print("[pipeline] rate limited, retrying in 60s...")
            time.sleep(60)

# Batches documents lazily using a generator to optimize memory usage
def _batched(items: list, size: int) -> Generator[list, None, None]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def ingest_documents(documents: list[dict]) -> int:
    docs = [
        DocChunk(
            content=_truncate(doc["body"]),
            embedding=[],
            source=doc["source"],
            source_url=doc["url"],
            title=doc["title"],
        )
        for doc in documents
    ]

    print(f"[pipeline] embedding {len(docs)} documents...")
    for batch in _batched(docs, EMBED_BATCH_SIZE):
        for doc, emb in zip(batch, _embed_batch([d.content for d in batch])):
            doc.embedding = emb

    return upsert_chunks(docs)


def run() -> None:
    from src.ingestion.ars_scraper import scrape_ars
    from src.ingestion.bbc_scraper import scrape_bbc

    for label, docs in [("ars", scrape_ars()), ("bbc", scrape_bbc())]:
        total = ingest_documents(docs)
        print(f"[{label}] ingested {total} documents")

# Invoked as the container entry point via docker-compose
if __name__ == "__main__":
    run()
