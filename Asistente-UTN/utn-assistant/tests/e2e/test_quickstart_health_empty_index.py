"""
T096 — E2E validation: Scenario 1 — Health and Empty Index.

Validates quickstart.md Scenario 1:
  - Health reports local dependency state for ChromaDB and Ollama.
  - Index status reports ready=false or zero counts when empty.
  - Query on empty index returns a controlled error, not an unsupported answer.

US5, FR-018, FR-021.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _app_client(chromadb_ok: bool = True, ollama_ok: bool = True, index_ready: bool = False):
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_health_service, get_estado_indice_service, get_responder_service
    from rag.services.health import HealthStatus
    from rag.domain.indexing import IndexStatus
    from rag.domain.queries import AssistantAnswer

    health_mock = MagicMock()
    health_mock.check.return_value = HealthStatus(
        chromadb_healthy=chromadb_ok,
        ollama_healthy=ollama_ok,
        index_ready=index_ready,
    )
    status_mock = MagicMock()
    status_mock.get_status.return_value = IndexStatus(
        ready=index_ready,
        document_count=0,
        fragment_count=0,
    )
    responder_mock = MagicMock()
    responder_mock.answer.return_value = AssistantAnswer(
        answer="",
        sources=[],
        context_sufficient=False,
        error={"code": "INDEX_NOT_READY", "message": "El índice no está disponible."},
    )

    app.dependency_overrides[get_health_service] = lambda: health_mock
    app.dependency_overrides[get_estado_indice_service] = lambda: status_mock
    app.dependency_overrides[get_responder_service] = lambda: responder_mock
    return TestClient(app, raise_server_exceptions=False)


class TestScenario1HealthAndEmptyIndex:
    """quickstart.md Scenario 1: Health and Empty Index."""

    def test_health_endpoint_reports_dependency_state(self):
        client = _app_client(chromadb_ok=True, ollama_ok=True)
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert "chromadb" in body
        assert "ollama" in body
        assert "status" in body

    def test_health_chromadb_ok_when_available(self):
        client = _app_client(chromadb_ok=True, ollama_ok=True)
        assert client.get("/health").json()["chromadb"] == "ok"

    def test_health_ollama_ok_when_available(self):
        client = _app_client(chromadb_ok=True, ollama_ok=True)
        assert client.get("/health").json()["ollama"] == "ok"

    def test_health_degraded_when_ollama_unavailable(self):
        client = _app_client(chromadb_ok=True, ollama_ok=False)
        status = client.get("/health").json()["status"]
        assert status in ("degraded", "unavailable")

    def test_index_status_not_ready_when_empty(self):
        client = _app_client(index_ready=False)
        resp = client.get("/index/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ready"] is False

    def test_index_fragment_count_zero_when_empty(self):
        client = _app_client(index_ready=False)
        body = client.get("/index/status").json()
        assert body["fragment_count"] == 0

    def test_query_before_index_ready_returns_503(self):
        """quickstart.md: query returns controlled not-ready error, not unsupported answer."""
        client = _app_client(index_ready=False)
        resp = client.post("/query", json={"question": "Consulta antes del índice"})
        assert resp.status_code == 503

    def test_query_error_does_not_expose_internals(self):
        client = _app_client(index_ready=False)
        resp = client.post("/query", json={"question": "consulta?"})
        if resp.status_code == 503:
            msg = resp.json().get("error", {}).get("message", "")
            assert "Traceback" not in msg
            assert "Exception" not in msg
