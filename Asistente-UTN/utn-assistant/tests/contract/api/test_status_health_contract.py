"""
T057 — Failing contract tests for GET /index/status and GET /health.

Tests the HTTP contract for index status (US7) and health (US5).
Expected to FAIL until T062 (index router) and T063 (health router) are implemented.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _client_with_status_and_health():
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_estado_indice_service, get_health_service
    from rag.domain.indexing import IndexStatus
    from rag.services.health import HealthStatus

    status_mock = MagicMock()
    status_mock.get_status.return_value = IndexStatus(
        ready=True,
        document_count=42,
        fragment_count=210,
        covered_areas=["ACADEMICA"],
    )

    health_mock = MagicMock()
    health_status = HealthStatus(
        chromadb_healthy=True,
        ollama_healthy=True,
        index_ready=True,
    )
    health_mock.check.return_value = health_status

    app.dependency_overrides[get_estado_indice_service] = lambda: status_mock
    app.dependency_overrides[get_health_service] = lambda: health_mock

    return TestClient(app, raise_server_exceptions=False), status_mock, health_mock


class TestIndexStatusContract:
    def test_get_index_status_returns_200(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/index/status")
        assert resp.status_code == 200

    def test_index_status_has_ready_field(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/index/status")
        assert "ready" in resp.json()

    def test_index_status_has_document_count(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/index/status")
        assert "document_count" in resp.json()

    def test_index_status_has_fragment_count(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/index/status")
        assert "fragment_count" in resp.json()

    def test_index_status_has_covered_areas(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/index/status")
        assert "covered_areas" in resp.json()
        assert isinstance(resp.json()["covered_areas"], list)

    def test_index_status_values_match_service(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/index/status")
        body = resp.json()
        assert body["ready"] is True
        assert body["document_count"] == 42
        assert body["fragment_count"] == 210

    def test_index_status_response_is_json(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/index/status")
        assert "application/json" in resp.headers.get("content-type", "")


class TestHealthContract:
    def test_get_health_returns_200(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status_field(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/health")
        assert "status" in resp.json()

    def test_health_has_chromadb_field(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/health")
        assert "chromadb" in resp.json()

    def test_health_has_ollama_field(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/health")
        assert "ollama" in resp.json()

    def test_health_has_index_ready_field(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/health")
        assert "index_ready" in resp.json()

    def test_health_status_ok_when_all_healthy(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/health")
        assert resp.json()["status"] == "ok"

    def test_health_chromadb_ok_value(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/health")
        assert resp.json()["chromadb"] == "ok"

    def test_health_ollama_ok_value(self):
        client, _, _ = _client_with_status_and_health()
        resp = client.get("/health")
        assert resp.json()["ollama"] == "ok"

    def test_health_degraded_when_ollama_down(self):
        from fastapi.testclient import TestClient
        from api.main import app
        from api.dependencies import get_health_service
        from rag.services.health import HealthStatus

        health_mock = MagicMock()
        health_mock.check.return_value = HealthStatus(
            chromadb_healthy=True,
            ollama_healthy=False,
            index_ready=True,
        )
        app.dependency_overrides[get_health_service] = lambda: health_mock
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.get("/health")
        assert resp.json()["status"] in ("degraded", "unavailable")
        assert resp.json()["ollama"] == "unavailable"
