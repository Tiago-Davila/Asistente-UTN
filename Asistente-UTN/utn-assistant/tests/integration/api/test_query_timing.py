"""
T077 — Query response timing integration test.

Tests the POST /query path end-to-end with a mocked service and asserts
that the response time target is met in controlled local conditions.
SC-004: 95% of normal queries return within 5 seconds.
US1.
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

REFUSAL = (
    "No tengo informacion suficiente sobre este tema "
    "en las fuentes institucionales disponibles."
)


def _query_client(answer_text: str = "Respuesta en menos de 5 segundos."):
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_responder_service
    from rag.domain.queries import AssistantAnswer, CitedSource
    from rag.domain.enums import AreaInstitucional

    mock_svc = MagicMock()
    mock_svc.answer.return_value = AssistantAnswer(
        answer=answer_text,
        sources=[CitedSource(url="https://utn.edu.ar/page", area=AreaInstitucional.ACADEMICA)],
        context_sufficient=True,
    )
    app.dependency_overrides[get_responder_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False), mock_svc


class TestQueryResponseTiming:
    def test_query_returns_200(self):
        client, _ = _query_client()
        resp = client.post("/query", json={"question": "Cuando son las inscripciones?"})
        assert resp.status_code == 200

    def test_query_completes_within_five_seconds(self):
        """SC-004: normal queries must respond in under 5 seconds."""
        client, _ = _query_client()
        start = time.monotonic()
        resp = client.post("/query", json={"question": "Cuando son las inscripciones?"})
        elapsed = time.monotonic() - start
        assert resp.status_code == 200
        assert elapsed < 5.0, f"Query took {elapsed:.3f}s; must be < 5s"

    def test_query_answer_in_response(self):
        client, _ = _query_client("Las inscripciones son en febrero.")
        resp = client.post("/query", json={"question": "consulta?"})
        assert resp.json()["answer"] == "Las inscripciones son en febrero."

    def test_refusal_also_fast(self):
        """Refusal path should be even faster than generation."""
        from fastapi.testclient import TestClient
        from api.main import app
        from api.dependencies import get_responder_service
        from rag.domain.queries import AssistantAnswer

        mock_svc = MagicMock()
        mock_svc.answer.return_value = AssistantAnswer(
            answer=REFUSAL, sources=[], context_sufficient=False
        )
        app.dependency_overrides[get_responder_service] = lambda: mock_svc
        client = TestClient(app, raise_server_exceptions=False)

        start = time.monotonic()
        resp = client.post("/query", json={"question": "consulta fuera del corpus"})
        elapsed = time.monotonic() - start
        assert resp.status_code == 200
        assert elapsed < 5.0
