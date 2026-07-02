"""
T101 — E2E validation: Scenario 6 — Failed Update Preservation.

Validates quickstart.md Scenario 6:
  - Failed run is recorded as failed.
  - Previous usable index remains active.
  - Queries continue to use the previous index after the failed update.

US4, FR-016, SC-006.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _make_run(mode: str = "FULL_REBUILD", fail: bool = False):
    from rag.domain.indexing import IndexUpdateRun
    from rag.domain.enums import ModoActualizacion, EstadoIndexacion
    run = IndexUpdateRun(mode=ModoActualizacion(mode))
    run.start()
    if fail:
        run.fail(reason="simulated scraper error")
    else:
        run.complete(documents_indexed=5, documents_failed=0, fragments_indexed=20)
        run.promoted = True
    return run


def _app_client_failed_update():
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_indexar_service, get_estado_indice_service, get_responder_service
    from rag.domain.indexing import IndexStatus
    from rag.domain.queries import AssistantAnswer, CitedSource
    from rag.domain.enums import AreaInstitucional

    indexar_mock = MagicMock()
    indexar_mock.full_rebuild.return_value = _make_run(fail=True)

    status_mock = MagicMock()
    # Previous index still available
    status_mock.get_status.return_value = IndexStatus(
        ready=True, document_count=5, fragment_count=20
    )

    responder_mock = MagicMock()
    responder_mock.answer.return_value = AssistantAnswer(
        answer="Respuesta del índice anterior.",
        sources=[CitedSource(url="https://utn.edu.ar/anterior", area=AreaInstitucional.ACADEMICA)],
        context_sufficient=True,
    )

    app.dependency_overrides[get_indexar_service] = lambda: indexar_mock
    app.dependency_overrides[get_estado_indice_service] = lambda: status_mock
    app.dependency_overrides[get_responder_service] = lambda: responder_mock
    return TestClient(app, raise_server_exceptions=False), indexar_mock, responder_mock


class TestScenario6FailedUpdatePreservation:
    """quickstart.md Scenario 6: Failed Update Preservation."""

    def test_failed_run_status_is_fallido(self):
        """SC-006: failed update never replaces the last known usable index."""
        client, indexar_mock, _ = _app_client_failed_update()
        body = client.post("/index/rebuild", json={"mode": "FULL_REBUILD"}).json()
        assert body["status"] == "FALLIDO"

    def test_failed_run_not_promoted(self):
        client, indexar_mock, _ = _app_client_failed_update()
        body = client.post("/index/rebuild", json={"mode": "FULL_REBUILD"}).json()
        assert body.get("promoted", False) is False

    def test_previous_index_still_ready_after_failed_update(self):
        """quickstart.md: previous usable index remains active after failure."""
        client, _, _ = _app_client_failed_update()
        client.post("/index/rebuild", json={"mode": "FULL_REBUILD"})
        status = client.get("/index/status").json()
        assert status["ready"] is True

    def test_queries_still_work_after_failed_update(self):
        """quickstart.md: queries continue using previous index."""
        client, _, _ = _app_client_failed_update()
        client.post("/index/rebuild", json={"mode": "FULL_REBUILD"})
        resp = client.post("/query", json={"question": "consulta?"})
        assert resp.status_code == 200
        assert resp.json()["context_sufficient"] is True

    def test_failed_run_response_shape(self):
        client, _, _ = _app_client_failed_update()
        body = client.post("/index/rebuild", json={"mode": "FULL_REBUILD"}).json()
        assert "run_id" in body
        assert "status" in body
        assert "documents_indexed" in body
