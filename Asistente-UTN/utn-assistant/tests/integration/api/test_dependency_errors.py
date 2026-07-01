"""
T075 — API dependency error integration tests.

Validates that the API layer maps service error payloads to the correct
HTTP status codes and structured error responses.
FR-021, US5.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

REFUSAL = (
    "No tengo informacion suficiente sobre este tema "
    "en las fuentes institucionales disponibles."
)


def _client_with_error_payloads(error_code: str, status_hint: int = 503):
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_responder_service, get_health_service
    from rag.domain.queries import AssistantAnswer

    mock_svc = MagicMock()
    mock_svc.answer.return_value = AssistantAnswer(
        answer="",
        sources=[],
        context_sufficient=False,
        error={"code": error_code, "message": f"Simulated: {error_code}"},
    )
    app.dependency_overrides[get_responder_service] = lambda: mock_svc

    # Also wire a basic health mock so /health doesn't crash
    health_mock = MagicMock()
    from rag.services.health import HealthStatus
    health_mock.check.return_value = HealthStatus()
    app.dependency_overrides[get_health_service] = lambda: health_mock

    return TestClient(app, raise_server_exceptions=False), mock_svc


class TestDependencyErrorIntegration:
    def test_generator_unavailable_returns_503(self):
        client, _ = _client_with_error_payloads("GENERATOR_UNAVAILABLE")
        resp = client.post("/query", json={"question": "consulta?"})
        assert resp.status_code == 503

    def test_index_not_ready_returns_503(self):
        client, _ = _client_with_error_payloads("INDEX_NOT_READY")
        resp = client.post("/query", json={"question": "consulta?"})
        assert resp.status_code == 503

    def test_error_code_preserved_in_body(self):
        client, _ = _client_with_error_payloads("GENERATOR_UNAVAILABLE")
        resp = client.post("/query", json={"question": "consulta?"})
        body = resp.json()
        assert body["error"]["code"] == "GENERATOR_UNAVAILABLE"

    def test_no_internal_details_in_error_message(self):
        """Error message must not expose stack traces or class names."""
        client, _ = _client_with_error_payloads("INDEX_NOT_READY")
        resp = client.post("/query", json={"question": "consulta?"})
        msg = resp.json()["error"]["message"]
        assert "Traceback" not in msg
        assert "Exception" not in msg
        assert "chromadb" not in msg.lower()


class TestHealthEndpointErrors:
    def test_health_degraded_when_ollama_down(self):
        from fastapi.testclient import TestClient
        from api.main import app
        from api.dependencies import get_health_service
        from rag.services.health import HealthStatus

        mock_health = MagicMock()
        mock_health.check.return_value = HealthStatus(
            chromadb_healthy=True, ollama_healthy=False, index_ready=False
        )
        app.dependency_overrides[get_health_service] = lambda: mock_health
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] in ("degraded", "unavailable")
        assert body["ollama"] == "unavailable"

    def test_health_ok_when_all_up(self):
        from fastapi.testclient import TestClient
        from api.main import app
        from api.dependencies import get_health_service
        from rag.services.health import HealthStatus

        mock_health = MagicMock()
        mock_health.check.return_value = HealthStatus(
            chromadb_healthy=True, ollama_healthy=True, index_ready=True
        )
        app.dependency_overrides[get_health_service] = lambda: mock_health
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.get("/health")
        assert resp.json()["status"] == "ok"
