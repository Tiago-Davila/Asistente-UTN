"""
T054 — Failing contract tests for POST /query insufficient-context refusal.

Tests the HTTP contract for the refusal path (US2).
Expected to FAIL until T058, T059, T060, T064 are implemented.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

REFUSAL_TEXT = (
    "No tengo informacion suficiente sobre este tema "
    "en las fuentes institucionales disponibles."
)


def _make_refusal_client():
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


class TestQueryRefusalContract:
    def test_refusal_returns_200_not_404(self):
        """Refusal is a valid answer — still HTTP 200."""
        client, _ = _make_refusal_client()
        resp = client.post("/query", json={"question": "Consulta sin contexto"})
        assert resp.status_code == 200

    def test_refusal_answer_is_exact_text(self):
        client, _ = _make_refusal_client()
        resp = client.post("/query", json={"question": "Consulta sin contexto"})
        assert resp.json()["answer"] == REFUSAL_TEXT

    def test_refusal_context_sufficient_is_false(self):
        client, _ = _make_refusal_client()
        resp = client.post("/query", json={"question": "Consulta sin contexto"})
        assert resp.json()["context_sufficient"] is False

    def test_refusal_sources_is_empty_list(self):
        client, _ = _make_refusal_client()
        resp = client.post("/query", json={"question": "Consulta sin contexto"})
        assert resp.json()["sources"] == []

    def test_refusal_has_no_error_field_or_null(self):
        """Refusal is not an error — error field should be absent or null."""
        client, _ = _make_refusal_client()
        resp = client.post("/query", json={"question": "Consulta sin contexto"})
        body = resp.json()
        assert body.get("error") is None

    def test_refusal_response_shape_matches_contract(self):
        """QueryResponse schema: answer + context_sufficient + sources all present."""
        client, _ = _make_refusal_client()
        resp = client.post("/query", json={"question": "consulta"})
        body = resp.json()
        assert set(["answer", "context_sufficient", "sources"]).issubset(body.keys())
