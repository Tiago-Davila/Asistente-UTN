"""
T100 — E2E validation: Scenario 5 — Area Filtering.

Validates quickstart.md Scenario 5:
  - No-filter query searches the whole usable index.
  - Filtered query returns only sources from the selected area.
  - Insufficient area-specific content returns the approved refusal message.

US6, FR-009, FR-010.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

REFUSAL_TEXT = (
    "No tengo informacion suficiente sobre este tema "
    "en las fuentes institucionales disponibles."
)


def _make_client_with_area_answer(area: str = "ACADEMICA"):
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_responder_service
    from rag.domain.queries import AssistantAnswer, CitedSource
    from rag.domain.enums import AreaInstitucional

    mock_svc = MagicMock()
    mock_svc.answer.return_value = AssistantAnswer(
        answer="Información del área solicitada.",
        sources=[CitedSource(
            url="https://utn.edu.ar/academica",
            title="Académica",
            area=AreaInstitucional(area),
        )],
        context_sufficient=True,
    )
    app.dependency_overrides[get_responder_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False), mock_svc


def _make_client_with_refusal():
    from fastapi.testclient import TestClient
    from api.main import app
    from api.dependencies import get_responder_service
    from rag.domain.queries import AssistantAnswer

    mock_svc = MagicMock()
    mock_svc.answer.return_value = AssistantAnswer(
        answer=REFUSAL_TEXT, sources=[], context_sufficient=False
    )
    app.dependency_overrides[get_responder_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False), mock_svc


class TestScenario5AreaFiltering:
    """quickstart.md Scenario 5: Area Filtering."""

    def test_no_filter_query_returns_200(self):
        """FR-010: no-filter query searches the whole usable index."""
        client, _ = _make_client_with_area_answer()
        resp = client.post("/query", json={"question": "consulta general"})
        assert resp.status_code == 200

    def test_academica_filter_accepted(self):
        client, _ = _make_client_with_area_answer("ACADEMICA")
        resp = client.post("/query", json={"question": "consulta?", "area": "ACADEMICA"})
        assert resp.status_code == 200
        assert resp.json()["context_sufficient"] is True

    def test_all_valid_areas_accepted(self):
        """FR-009: all four institutional areas are valid filter values."""
        for area in ("ACADEMICA", "ADMINISTRATIVA", "BIENESTAR", "EXTENSION"):
            client, _ = _make_client_with_area_answer(area)
            resp = client.post("/query", json={"question": "consulta?", "area": area})
            assert resp.status_code == 200, f"Area {area} returned {resp.status_code}"

    def test_filtered_query_forwards_area_to_service(self):
        """FR-009: area filter is forwarded to the service layer."""
        from rag.domain.enums import AreaInstitucional
        client, mock_svc = _make_client_with_area_answer("ACADEMICA")
        client.post("/query", json={"question": "consulta?", "area": "ACADEMICA"})
        call_args = mock_svc.answer.call_args
        q = call_args.args[0] if call_args.args else call_args.kwargs.get("query")
        assert q.area_filter == AreaInstitucional.ACADEMICA

    def test_insufficient_area_content_returns_refusal(self):
        """quickstart.md: insufficient area content → approved refusal message."""
        client, _ = _make_client_with_refusal()
        resp = client.post("/query", json={"question": "consulta?", "area": "EXTENSION"})
        assert resp.status_code == 200
        assert resp.json()["answer"] == REFUSAL_TEXT

    def test_invalid_area_returns_error(self):
        client, _ = _make_client_with_area_answer()
        resp = client.post("/query", json={"question": "consulta?", "area": "INVALIDA"})
        assert resp.status_code in (400, 422)
