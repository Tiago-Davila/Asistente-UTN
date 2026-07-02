"""
T076 — Index status performance integration test.

Asserts that GET /index/status returns within 1 second (SC-004 target)
in local test conditions using a mocked service.
FR-018, US7.
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest


def _status_client():
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_estado_indice_service
    from rag.domain.indexing import IndexStatus

    mock_svc = MagicMock()
    mock_svc.get_status.return_value = IndexStatus(
        ready=True,
        document_count=100,
        fragment_count=500,
        covered_areas=["ACADEMICA"],
    )
    app.dependency_overrides[get_estado_indice_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False), mock_svc


class TestIndexStatusPerformance:
    def test_status_returns_200(self):
        client, _ = _status_client()
        resp = client.get("/index/status")
        assert resp.status_code == 200

    def test_status_returns_within_one_second(self):
        """SC-004 target: index status must return in under 1 second."""
        client, _ = _status_client()
        start = time.monotonic()
        resp = client.get("/index/status")
        elapsed = time.monotonic() - start
        assert resp.status_code == 200
        assert elapsed < 1.0, f"Index status took {elapsed:.3f}s; must be < 1s"

    def test_status_fields_present(self):
        client, _ = _status_client()
        body = client.get("/index/status").json()
        assert "ready" in body
        assert "document_count" in body
        assert "fragment_count" in body
        assert "covered_areas" in body

    def test_status_values_match_service(self):
        client, _ = _status_client()
        body = client.get("/index/status").json()
        assert body["document_count"] == 100
        assert body["fragment_count"] == 500
        assert body["ready"] is True
