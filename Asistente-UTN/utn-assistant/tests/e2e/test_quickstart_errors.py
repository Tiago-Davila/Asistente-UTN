"""
T102 — E2E validation: Scenario 7 — Input and Dependency Errors.

Validates quickstart.md Scenario 7:
  - Invalid questions return structured validation errors.
  - Generator unavailable returns clear controlled error.
  - Index unavailable/not-ready returns clear structured errors.
  - No internal stack traces exposed.

US5, FR-002, FR-021, SC-003.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _app_client_generator_down():
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_responder_service
    from rag.domain.queries import AssistantAnswer

    mock_svc = MagicMock()
    mock_svc.answer.return_value = AssistantAnswer(
        answer="",
        sources=[],
        context_sufficient=False,
        error={"code": "GENERATOR_UNAVAILABLE", "message": "El generador no está disponible."},
    )
    app.dependency_overrides[get_responder_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def _basic_client():
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_responder_service
    from rag.domain.queries import AssistantAnswer

    mock_svc = MagicMock()
    mock_svc.answer.return_value = AssistantAnswer(
        answer="No tengo informacion suficiente sobre este tema en las fuentes institucionales disponibles.",
        sources=[],
        context_sufficient=False,
    )
    app.dependency_overrides[get_responder_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


class TestScenario7InputAndDependencyErrors:
    """quickstart.md Scenario 7: Input and Dependency Errors."""

    def test_empty_question_returns_400(self):
        """quickstart.md: invalid questions return structured validation errors."""
        client = _basic_client()
        resp = client.post("/query", json={"question": ""})
        assert resp.status_code == 400

    def test_empty_question_has_structured_error(self):
        client = _basic_client()
        body = client.post("/query", json={"question": ""}).json()
        assert "error" in body
        assert body["error"]["code"] == "INVALID_QUESTION"

    def test_question_over_2000_chars_returns_400(self):
        client = _basic_client()
        resp = client.post("/query", json={"question": "x" * 2001})
        assert resp.status_code == 400

    def test_generator_unavailable_returns_503(self):
        """quickstart.md: generator unavailable → clear controlled error."""
        client = _app_client_generator_down()
        resp = client.post("/query", json={"question": "consulta válida"})
        assert resp.status_code == 503

    def test_generator_error_has_error_code(self):
        client = _app_client_generator_down()
        body = client.post("/query", json={"question": "consulta válida"}).json()
        assert body["error"]["code"] == "GENERATOR_UNAVAILABLE"

    def test_no_stack_trace_in_validation_error(self):
        """quickstart.md: no internal stack traces or implementation details exposed."""
        client = _basic_client()
        body = client.post("/query", json={"question": ""}).json()
        msg = body.get("error", {}).get("message", "")
        assert "Traceback" not in msg
        assert "Exception" not in msg

    def test_no_stack_trace_in_dependency_error(self):
        client = _app_client_generator_down()
        body = client.post("/query", json={"question": "consulta"}).json()
        msg = body.get("error", {}).get("message", "")
        assert "Traceback" not in msg
        assert "Exception" not in msg

    def test_index_not_ready_error_structured(self):
        from fastapi.testclient import TestClient
        from api.main import app
        from api.dependencies import get_responder_service
        from rag.domain.queries import AssistantAnswer

        mock_svc = MagicMock()
        mock_svc.answer.return_value = AssistantAnswer(
            answer="", sources=[], context_sufficient=False,
            error={"code": "INDEX_NOT_READY", "message": "Índice no disponible."},
        )
        app.dependency_overrides[get_responder_service] = lambda: mock_svc
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.post("/query", json={"question": "consulta"})
        assert resp.status_code == 503
        assert resp.json()["error"]["code"] == "INDEX_NOT_READY"
