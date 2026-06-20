"""Tests for FastAPI endpoints."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    with patch("src.api.build_agent"), patch("src.api.count_docs", return_value=42):
        from src.api import app
        with TestClient(app) as c:
            yield c


def _mock_result(content: str) -> MagicMock:
    result = MagicMock()
    result.content.answer = content
    result.content.sources = ["https://example.com"]
    result.reasoning_content = ""
    result.model = "test-model"
    result.tools = []
    result.metrics.total_tokens = 10
    result.metrics.input_tokens = 8
    result.metrics.output_tokens = 2
    result.metrics.reasoning_tokens = 0
    result.metrics.duration = 0.5
    return result


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_query_returns_response(client):
    import src.api as api_module
    api_module._agent = MagicMock()
    api_module._agent.run.return_value = _mock_result("There are 3 open roles.")

    resp = client.post("/query", json={"message": "any open jobs?"})
    assert resp.status_code == 200
    assert resp.json()["response"] == "There are 3 open roles."
