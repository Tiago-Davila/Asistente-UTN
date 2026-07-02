"""
T053 — Failing contract tests for POST /query success response.

Tests the HTTP contract defined in contracts/openapi.yaml for the
successful query path (US1, US3).

Uses FastAPI TestClient with dependency overrides.
Expected to FAIL until T058, T059, T060, T064 are implemented.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

REFUSAL_TEXT = (
    "No tengo informacion suficiente sobre este tema "
    "en las fuentes institucionales disponibles."
)


def _make_cited_source(url: str = "https://utn.edu.ar/a", title: str | None = "Inicio"):
    from rag.domain.queries import CitedSource
    from rag.domain.enums import AreaInstitucional
    return CitedSource(url=url, title=title, area=AreaInstitucional.ACADEMICA)


def _make_app_with_mock_service(answer_text: str = "Las inscripciones son en marzo.", context_sufficient: bool = True):
    """Return a TestClient with ResponderConsultaService mocked."""
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_responder_service

    mock_svc = MagicMock()

    from rag.domain.queries import AssistantAnswer
    cited = [_make_cited_source()] if context_sufficient else []
    if context_sufficient:
        answer_obj = AssistantAnswer(
            answer=answer_text,
            sources=cited,
            context_sufficient=True,
        )
    else:
        answer_obj = AssistantAnswer(
            answer=REFUSAL_TEXT,
            sources=[],
            context_sufficient=False,
        )
    mock_svc.answer.return_value = answer_obj

    app.dependency_overrides[get_responder_service] = lambda: mock_svc
    client = TestClient(app, raise_server_exceptions=False)
    return client, mock_svc


class TestQueryContractSuccess:
    def test_post_query_returns_200(self):
        client, _ = _make_app_with_mock_service()
        resp = client.post("/query", json={"question": "Cuando son las inscripciones?"})
        assert resp.status_code == 200

    def test_response_has_required_fields(self):
        client, _ = _make_app_with_mock_service()
        resp = client.post("/query", json={"question": "Cuando son las inscripciones?"})
        body = resp.json()
        assert "answer" in body
        assert "context_sufficient" in body
        assert "sources" in body

    def test_context_sufficient_is_true_on_success(self):
        client, _ = _make_app_with_mock_service()
        resp = client.post("/query", json={"question": "consulta?"})
        assert resp.json()["context_sufficient"] is True

    def test_sources_list_non_empty_on_success(self):
        client, _ = _make_app_with_mock_service()
        resp = client.post("/query", json={"question": "consulta?"})
        body = resp.json()
        assert isinstance(body["sources"], list)
        assert len(body["sources"]) >= 1

    def test_source_has_url_field(self):
        client, _ = _make_app_with_mock_service()
        resp = client.post("/query", json={"question": "consulta?"})
        source = resp.json()["sources"][0]
        assert "url" in source
        assert source["url"].startswith("http")

    def test_answer_text_returned(self):
        client, _ = _make_app_with_mock_service(answer_text="Respuesta de prueba.")
        resp = client.post("/query", json={"question": "consulta?"})
        assert resp.json()["answer"] == "Respuesta de prueba."

    def test_area_filter_accepted_in_request(self):
        client, mock_svc = _make_app_with_mock_service()
        resp = client.post("/query", json={"question": "consulta?", "area": "ACADEMICA"})
        assert resp.status_code == 200
        # Service was called with a query that has the area filter
        mock_svc.answer.assert_called_once()
        query_arg = mock_svc.answer.call_args.args[0]
        from rag.domain.enums import AreaInstitucional
        assert query_arg.area_filter == AreaInstitucional.ACADEMICA

    def test_content_type_is_json(self):
        client, _ = _make_app_with_mock_service()
        resp = client.post("/query", json={"question": "consulta?"})
        assert "application/json" in resp.headers.get("content-type", "")


class TestQueryContractValidation:
    def test_empty_question_returns_400(self):
        client, _ = _make_app_with_mock_service()
        resp = client.post("/query", json={"question": ""})
        assert resp.status_code == 400

    def test_missing_question_returns_422_or_400(self):
        client, _ = _make_app_with_mock_service()
        resp = client.post("/query", json={})
        assert resp.status_code in (400, 422)

    def test_question_over_2000_chars_returns_400(self):
        client, _ = _make_app_with_mock_service()
        resp = client.post("/query", json={"question": "a" * 2001})
        assert resp.status_code == 400

    def test_invalid_area_returns_400_or_422(self):
        client, _ = _make_app_with_mock_service()
        resp = client.post("/query", json={"question": "consulta?", "area": "INVALID"})
        assert resp.status_code in (400, 422)

    def test_error_response_has_error_field(self):
        client, _ = _make_app_with_mock_service()
        resp = client.post("/query", json={"question": ""})
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
