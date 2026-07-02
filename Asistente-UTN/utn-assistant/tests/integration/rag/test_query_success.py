"""
T070 — RAG service integration tests: successful query with citation.

Uses real ChromaDB (seeded_chroma_repo), mocked LLM.
FR-003, FR-005: retrieved content used; citation returned.
US1, US3.
"""
from __future__ import annotations

import pytest


class TestQuerySuccess:
    def test_answer_returned_for_seeded_content(self, responder_service):
        from rag.domain.queries import UserQuery
        q = UserQuery(question="Cuando son las inscripciones?")
        answer = responder_service.answer(q)
        assert answer.context_sufficient is True
        assert len(answer.answer) > 0

    def test_answer_is_llm_generated_text(self, responder_service, mock_llm_client):
        from rag.domain.queries import UserQuery
        mock_llm_client.generate.return_value = "Texto de respuesta generado."
        q = UserQuery(question="consulta?")
        answer = responder_service.answer(q)
        assert answer.answer == "Texto de respuesta generado."

    def test_sources_non_empty_on_success(self, responder_service):
        from rag.domain.queries import UserQuery
        answer = responder_service.answer(UserQuery(question="inscripciones?"))
        assert len(answer.sources) >= 1

    def test_source_url_present(self, responder_service):
        from rag.domain.queries import UserQuery
        answer = responder_service.answer(UserQuery(question="inscripciones?"))
        assert all(s.url.startswith("http") for s in answer.sources)

    def test_source_title_present_when_available(self, responder_service):
        from rag.domain.queries import UserQuery
        answer = responder_service.answer(UserQuery(question="inscripciones?"))
        # The seeded fixture has a title
        assert any(s.title is not None for s in answer.sources)

    def test_llm_called_once_per_query(self, responder_service, mock_llm_client):
        from rag.domain.queries import UserQuery
        mock_llm_client.generate.return_value = "Respuesta."
        responder_service.answer(UserQuery(question="consulta?"))
        mock_llm_client.generate.assert_called_once()
