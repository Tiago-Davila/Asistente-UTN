"""
T056 — Failing contract tests for POST /index/rebuild and DELETE /index.

Tests the HTTP contract for admin index operations (US4).
Expected to FAIL until T062 is implemented.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _make_run_response():
    from rag.domain.indexing import IndexUpdateRun
    from rag.domain.enums import ModoActualizacion
    run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
    run.start()
    run.complete(documents_indexed=5, documents_failed=0, fragments_indexed=20)
    return run


def _client_with_index_service(service_mock=None, status_service_mock=None):
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_estado_indice_service, get_indexar_service, get_repository

    if service_mock is None:
        service_mock = MagicMock()
        service_mock.full_rebuild.return_value = _make_run_response()
        service_mock.incremental_update.return_value = _make_run_response()

    if status_service_mock is None:
        from rag.domain.indexing import IndexStatus
        status_service_mock = MagicMock()
        status_service_mock.get_status.return_value = IndexStatus(
            ready=True, fragment_count=100, document_count=10
        )

    # Mock repository so DELETE /index doesn't touch real ChromaDB
    repo_mock = MagicMock()
    repo_mock.delete_collection.return_value = None

    app.dependency_overrides[get_indexar_service] = lambda: service_mock
    app.dependency_overrides[get_estado_indice_service] = lambda: status_service_mock
    app.dependency_overrides[get_repository] = lambda: repo_mock

    return TestClient(app, raise_server_exceptions=False), service_mock


class TestIndexRebuildContract:
    def test_post_index_rebuild_returns_202(self):
        client, _ = _client_with_index_service()
        resp = client.post("/index/rebuild", json={"mode": "FULL_REBUILD"})
        assert resp.status_code == 202

    def test_rebuild_response_has_run_id(self):
        client, _ = _client_with_index_service()
        resp = client.post("/index/rebuild", json={"mode": "FULL_REBUILD"})
        body = resp.json()
        assert "run_id" in body
        assert len(body["run_id"]) > 0

    def test_rebuild_response_has_status_field(self):
        client, _ = _client_with_index_service()
        resp = client.post("/index/rebuild", json={"mode": "FULL_REBUILD"})
        assert "status" in resp.json()

    def test_rebuild_response_has_counts(self):
        client, _ = _client_with_index_service()
        resp = client.post("/index/rebuild", json={"mode": "FULL_REBUILD"})
        body = resp.json()
        assert "documents_indexed" in body
        assert "documents_failed" in body
        assert "fragments_indexed" in body

    def test_incremental_rebuild_requires_source_ids(self):
        client, _ = _client_with_index_service()
        resp = client.post(
            "/index/rebuild",
            json={"mode": "INCREMENTAL_SELECTED_SOURCES", "selected_source_ids": []},
        )
        assert resp.status_code in (400, 422)

    def test_invalid_mode_returns_400(self):
        client, _ = _client_with_index_service()
        resp = client.post("/index/rebuild", json={"mode": "INVALID_MODE"})
        assert resp.status_code in (400, 422)

    def test_missing_mode_returns_400(self):
        client, _ = _client_with_index_service()
        resp = client.post("/index/rebuild", json={})
        assert resp.status_code in (400, 422)


class TestIndexDeleteContract:
    def test_delete_index_returns_202(self):
        client, _ = _client_with_index_service()
        resp = client.delete("/index")
        assert resp.status_code == 202

    def test_delete_response_has_accepted_field(self):
        client, _ = _client_with_index_service()
        resp = client.delete("/index")
        body = resp.json()
        assert "accepted" in body
        assert body["accepted"] is True

    def test_delete_response_has_message_field(self):
        client, _ = _client_with_index_service()
        resp = client.delete("/index")
        assert "message" in resp.json()
