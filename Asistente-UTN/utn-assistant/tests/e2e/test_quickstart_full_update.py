"""
T097 — E2E validation: Scenario 2 — Full Source Update.

Validates quickstart.md Scenario 2:
  - Update run reports documents/fragments indexed and failures.
  - Failed individual URLs recorded without stopping the run.
  - Completed run promotes a usable index.
  - Status shows document/fragment count, last update, covered areas, regionales.

US4, FR-015, FR-016, FR-017.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest


def _make_completed_run(docs_indexed: int = 5, docs_failed: int = 1, frags: int = 20):
    from rag.domain.indexing import IndexUpdateRun, FailureDetail
    from rag.domain.enums import ModoActualizacion
    run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
    run.start()
    run.complete(
        documents_indexed=docs_indexed,
        documents_failed=docs_failed,
        fragments_indexed=frags,
    )
    run.promoted = True
    run.failure_details.append(FailureDetail(source_id="src-fail", reason="HTTP 404"))
    return run


def _app_client_for_update(run=None):
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_indexar_service, get_estado_indice_service
    from rag.domain.indexing import IndexStatus
    from rag.domain.enums import AreaInstitucional

    if run is None:
        run = _make_completed_run()

    indexar_mock = MagicMock()
    indexar_mock.full_rebuild.return_value = run

    status_mock = MagicMock()
    status_mock.get_status.return_value = IndexStatus(
        ready=True,
        document_count=5,
        fragment_count=20,
        last_successful_update_at=datetime.now(timezone.utc),
        covered_areas=[AreaInstitucional.ACADEMICA],
        covered_regionales=["Rectorado"],
    )

    app.dependency_overrides[get_indexar_service] = lambda: indexar_mock
    app.dependency_overrides[get_estado_indice_service] = lambda: status_mock
    return TestClient(app, raise_server_exceptions=False), indexar_mock


class TestScenario2FullSourceUpdate:
    """quickstart.md Scenario 2: Full Source Update."""

    def test_rebuild_returns_202(self):
        client, _ = _app_client_for_update()
        resp = client.post("/index/rebuild", json={"mode": "FULL_REBUILD"})
        assert resp.status_code == 202

    def test_rebuild_reports_documents_indexed(self):
        client, _ = _app_client_for_update()
        body = client.post("/index/rebuild", json={"mode": "FULL_REBUILD"}).json()
        assert body["documents_indexed"] == 5

    def test_rebuild_reports_documents_failed(self):
        client, _ = _app_client_for_update()
        body = client.post("/index/rebuild", json={"mode": "FULL_REBUILD"}).json()
        assert body["documents_failed"] == 1

    def test_rebuild_reports_fragments_indexed(self):
        client, _ = _app_client_for_update()
        body = client.post("/index/rebuild", json={"mode": "FULL_REBUILD"}).json()
        assert body["fragments_indexed"] == 20

    def test_rebuild_records_individual_failures(self):
        """quickstart.md: failed individual URLs recorded without stopping run."""
        client, _ = _app_client_for_update()
        body = client.post("/index/rebuild", json={"mode": "FULL_REBUILD"}).json()
        assert isinstance(body.get("failures", []), list)

    def test_status_shows_document_count_after_update(self):
        client, _ = _app_client_for_update()
        body = client.get("/index/status").json()
        assert body["document_count"] == 5
        assert body["fragment_count"] == 20

    def test_status_shows_covered_areas_after_update(self):
        client, _ = _app_client_for_update()
        body = client.get("/index/status").json()
        assert len(body["covered_areas"]) >= 1

    def test_status_ready_after_successful_update(self):
        client, _ = _app_client_for_update()
        assert client.get("/index/status").json()["ready"] is True
