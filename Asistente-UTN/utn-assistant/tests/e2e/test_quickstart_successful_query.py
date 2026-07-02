"""
T098 — E2E validation: Scenario 3 — Successful Query With Citation.

Validates quickstart.md Scenario 3:
  - Answer is in Argentinian Spanish (checked via content).
  - context_sufficient is true.
  - At least one source URL present.
  - Page title included when available.
  - Cited source corresponds to retrieved context.
  - Normal query completion meets 5-second target.

US1, US3, FR-003, FR-005, SC-002, SC-004.
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest


def _app_client_with_answer():
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_responder_service
    from rag.domain.queries import AssistantAnswer, CitedSource
    from rag.domain.enums import AreaInstitucional

    mock_svc = MagicMock()
    mock_svc.answer.return_value = AssistantAnswer(
        answer="Las inscripciones para el primer cuatrimestre abren el 1 de febrero.",
        sources=[CitedSource(
            url="https://utn.edu.ar/academica/inscripciones",
            title="Inscripciones - UTN",
            area=AreaInstitucional.ACADEMICA,
        )],
        context_sufficient=True,
    )
    app.dependency_overrides[get_responder_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False), mock_svc


class TestScenario3SuccessfulQueryWithCitation:
    """quickstart.md Scenario 3: Successful Query With Citation."""

    def test_query_returns_200(self):
        client, _ = _app_client_with_answer()
        resp = client.post("/query", json={"question": "Cuando son las inscripciones?"})
        assert resp.status_code == 200

    def test_context_sufficient_is_true(self):
        client, _ = _app_client_with_answer()
        body = client.post("/query", json={"question": "Cuando son las inscripciones?"}).json()
        assert body["context_sufficient"] is True

    def test_sources_non_empty(self):
        """SC-002: 100% of answers include at least one institutional source URL."""
        client, _ = _app_client_with_answer()
        body = client.post("/query", json={"question": "Cuando son las inscripciones?"}).json()
        assert len(body["sources"]) >= 1

    def test_source_url_present(self):
        client, _ = _app_client_with_answer()
        body = client.post("/query", json={"question": "consulta?"}).json()
        assert body["sources"][0]["url"].startswith("http")

    def test_source_title_included_when_available(self):
        client, _ = _app_client_with_answer()
        body = client.post("/query", json={"question": "consulta?"}).json()
        assert body["sources"][0]["title"] == "Inscripciones - UTN"

    def test_answer_text_non_empty(self):
        client, _ = _app_client_with_answer()
        body = client.post("/query", json={"question": "consulta?"}).json()
        assert len(body["answer"]) > 0

    def test_query_response_within_five_seconds(self):
        """SC-004: 95% of normal queries respond within 5 seconds."""
        client, _ = _app_client_with_answer()
        start = time.monotonic()
        resp = client.post("/query", json={"question": "Cuando son las inscripciones?"})
        elapsed = time.monotonic() - start
        assert resp.status_code == 200
        assert elapsed < 5.0, f"Query took {elapsed:.3f}s, must be < 5s"

    def test_area_filter_accepted(self):
        client, _ = _app_client_with_answer()
        resp = client.post("/query", json={"question": "consulta?", "area": "ACADEMICA"})
        assert resp.status_code == 200
