"""
T055 — Failing contract tests for query validation and dependency errors.

Tests the HTTP error contract for US5 (Disponibilidad y errores claros).
Covers: empty question, too-long question, invalid area, index-not-ready,
        generator-unavailable paths.
Expected to FAIL until T061 + T064 are confirmed wired (both already done).
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from rag.services.llm_client import LLMGenerationError


REFUSAL = (
    "No tengo informacion suficiente sobre este tema "
    "en las fuentes institucionales disponibles."
)


def _client_with_service(service_mock=None):
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_responder_service

    if service_mock is None:
        service_mock = MagicMock()
        from rag.domain.queries import AssistantAnswer
        # Use valid refusal answer (context_sufficient=False requires exact text)
        service_mock.answer.return_value = AssistantAnswer(
            answer=REFUSAL,
            sources=[],
            context_sufficient=False,
        )

    app.dependency_overrides[get_responder_service] = lambda: service_mock
    return TestClient(app, raise_server_exceptions=False), service_mock


class TestInputValidationErrors:
    def test_empty_question_returns_400(self):
        client, _ = _client_with_service()
        resp = client.post("/query", json={"question": ""})
        assert resp.status_code == 400

    def test_blank_question_returns_400(self):
        client, _ = _client_with_service()
        resp = client.post("/query", json={"question": "   "})
        assert resp.status_code == 400

    def test_question_over_2000_chars_returns_400(self):
        client, _ = _client_with_service()
        resp = client.post("/query", json={"question": "x" * 2001})
        assert resp.status_code == 400

    def test_missing_question_field_returns_400(self):
        client, _ = _client_with_service()
        resp = client.post("/query", json={"area": "ACADEMICA"})
        assert resp.status_code in (400, 422)

    def test_invalid_area_value_returns_400(self):
        client, _ = _client_with_service()
        resp = client.post("/query", json={"question": "consulta?", "area": "NO_ES_UN_AREA"})
        assert resp.status_code in (400, 422)

    def test_max_results_over_10_returns_400(self):
        client, _ = _client_with_service()
        resp = client.post("/query", json={"question": "consulta?", "max_results": 11})
        assert resp.status_code in (400, 422)

    def test_max_results_zero_returns_400(self):
        client, _ = _client_with_service()
        resp = client.post("/query", json={"question": "consulta?", "max_results": 0})
        assert resp.status_code in (400, 422)


class TestErrorResponseEnvelope:
    def test_error_response_has_error_key(self):
        client, _ = _client_with_service()
        resp = client.post("/query", json={"question": ""})
        body = resp.json()
        assert "error" in body

    def test_error_detail_has_code_and_message(self):
        client, _ = _client_with_service()
        resp = client.post("/query", json={"question": ""})
        error = resp.json()["error"]
        assert "code" in error
        assert "message" in error
        assert len(error["code"]) > 0
        assert len(error["message"]) > 0

    def test_invalid_question_code_is_correct(self):
        client, _ = _client_with_service()
        resp = client.post("/query", json={"question": ""})
        assert resp.json()["error"]["code"] == "INVALID_QUESTION"


class TestDependencyErrors:
    def test_service_error_payload_returns_503(self):
        """When the service returns an error payload, the router maps it to 503."""
        from fastapi.testclient import TestClient
        from api.main import app
        from api.dependencies import get_responder_service
        from rag.domain.queries import AssistantAnswer

        mock_svc = MagicMock()
        mock_svc.answer.return_value = AssistantAnswer(
            answer="",
            sources=[],
            context_sufficient=False,
            error={"code": "GENERATOR_UNAVAILABLE", "message": "Ollama no disponible."},
        )
        app.dependency_overrides[get_responder_service] = lambda: mock_svc
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.post("/query", json={"question": "consulta?"})
        assert resp.status_code == 503

    def test_503_response_has_error_envelope(self):
        from fastapi.testclient import TestClient
        from api.main import app
        from api.dependencies import get_responder_service
        from rag.domain.queries import AssistantAnswer

        mock_svc = MagicMock()
        mock_svc.answer.return_value = AssistantAnswer(
            answer="",
            sources=[],
            context_sufficient=False,
            error={"code": "INDEX_NOT_READY", "message": "Indice no disponible."},
        )
        app.dependency_overrides[get_responder_service] = lambda: mock_svc
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.post("/query", json={"question": "consulta?"})
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "INDEX_NOT_READY"
