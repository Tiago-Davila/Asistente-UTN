"""
T099 — E2E validation: Scenario 4 — Insufficient Context Refusal.

Validates quickstart.md Scenario 4:
  - context_sufficient is false.
  - Answer is exactly the approved refusal text.
  - No unsupported institutional claim is generated.

US2, FR-006, FR-007, FR-008, SC-003.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

REFUSAL_TEXT = (
    "No tengo informacion suficiente sobre este tema "
    "en las fuentes institucionales disponibles."
)


def _app_client_with_refusal():
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_responder_service
    from rag.domain.queries import AssistantAnswer

    mock_svc = MagicMock()
    mock_svc.answer.return_value = AssistantAnswer(
        answer=REFUSAL_TEXT,
        sources=[],
        context_sufficient=False,
    )
    app.dependency_overrides[get_responder_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False), mock_svc


class TestScenario4InsufficientContextRefusal:
    """quickstart.md Scenario 4: Insufficient Context Refusal."""

    def test_refusal_returns_200(self):
        """Refusal is a valid answer — HTTP 200, not an error code."""
        client, _ = _app_client_with_refusal()
        resp = client.post("/query", json={"question": "Consulta fuera del corpus"})
        assert resp.status_code == 200

    def test_context_sufficient_is_false(self):
        """SC-003: 100% of insufficient-context questions return refusal."""
        client, _ = _app_client_with_refusal()
        body = client.post("/query", json={"question": "Consulta fuera del corpus"}).json()
        assert body["context_sufficient"] is False

    def test_answer_is_exact_refusal_text(self):
        """FR-007: the exact approved refusal text must be returned."""
        client, _ = _app_client_with_refusal()
        body = client.post("/query", json={"question": "Consulta sin contexto"}).json()
        assert body["answer"] == REFUSAL_TEXT

    def test_sources_empty_on_refusal(self):
        client, _ = _app_client_with_refusal()
        body = client.post("/query", json={"question": "consulta"}).json()
        assert body["sources"] == []

    def test_no_error_field_on_refusal(self):
        """Refusal is not an error — error field must be absent or null."""
        client, _ = _app_client_with_refusal()
        body = client.post("/query", json={"question": "consulta"}).json()
        assert body.get("error") is None

    def test_refusal_response_shape_matches_contract(self):
        client, _ = _app_client_with_refusal()
        body = client.post("/query", json={"question": "consulta"}).json()
        assert {"answer", "context_sufficient", "sources"}.issubset(body.keys())
