"""Tests for ingestion pipeline."""

from unittest.mock import patch

from src.ingestion.pipeline import _truncate, ingest_documents


def test_truncate_short_text():
    text = "This is a short text."
    assert _truncate(text) == text


def test_truncate_long_text():
    long_text = "This is a long text." * 2000
    result = _truncate(long_text)
    assert len(result) < len(long_text)


def test_ingest_documents_calls_upsert():
    docs = [{"title": "T", "url": "https://example.com", "body": "body text", "source": "news"}]
    fake_embedding = [0.1] * 1536

    with patch("src.ingestion.pipeline._embed_batch", return_value=[fake_embedding]), \
         patch("src.ingestion.pipeline.upsert_chunks", return_value=1) as mock_upsert:
        result = ingest_documents(docs)

    assert result == 1
    mock_upsert.assert_called_once()
    chunk = mock_upsert.call_args[0][0][0]
    assert chunk.source == "news"
    assert chunk.source_url == "https://example.com"
