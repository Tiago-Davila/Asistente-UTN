"""
T071 — RAG refusal integration tests.

Tests the refusal path with a real ChromaDB (threshold above scores) and
empty retrieval scenarios.
FR-006, FR-007, US2.
"""
from __future__ import annotations

import pytest

REFUSAL = (
    "No tengo informacion suficiente sobre este tema "
    "en las fuentes institucionales disponibles."
)


@pytest.fixture()
def high_threshold_service(seeded_chroma_repo, mock_llm_client):
    """Service with threshold set above any possible score (forces refusal)."""
    from rag.services.responder_consulta import ResponderConsultaService
    from rag.prompting import PromptBuilder
    return ResponderConsultaService(
        repository=seeded_chroma_repo,
        llm_client=mock_llm_client,
        prompt_builder=PromptBuilder(),
        relevance_threshold=0.9999,  # nothing will pass
        top_k=5,
        embeddings_adapter=None,
    )


@pytest.fixture()
def empty_repo_service(chroma_repo, mock_llm_client):
    """Service with an empty ChromaDB (forces refusal)."""
    from rag.services.responder_consulta import ResponderConsultaService
    from rag.prompting import PromptBuilder
    return ResponderConsultaService(
        repository=chroma_repo,
        llm_client=mock_llm_client,
        prompt_builder=PromptBuilder(),
        relevance_threshold=0.65,
        top_k=5,
        embeddings_adapter=None,
    )


class TestQueryRefusalBelowThreshold:
    def test_refusal_when_all_below_threshold(self, high_threshold_service):
        from rag.domain.queries import UserQuery
        answer = high_threshold_service.answer(UserQuery(question="consulta irrelevante"))
        assert answer.context_sufficient is False
        assert answer.answer == REFUSAL

    def test_refusal_sources_empty(self, high_threshold_service):
        from rag.domain.queries import UserQuery
        answer = high_threshold_service.answer(UserQuery(question="consulta"))
        assert answer.sources == []

    def test_llm_not_called_on_threshold_refusal(self, high_threshold_service, mock_llm_client):
        from rag.domain.queries import UserQuery
        high_threshold_service.answer(UserQuery(question="consulta"))
        mock_llm_client.generate.assert_not_called()


class TestQueryRefusalEmptyIndex:
    def test_refusal_when_index_empty(self, empty_repo_service):
        from rag.domain.queries import UserQuery
        answer = empty_repo_service.answer(UserQuery(question="consulta sin indice"))
        assert answer.context_sufficient is False
        assert answer.answer == REFUSAL

    def test_exact_refusal_text(self, empty_repo_service):
        from rag.domain.queries import UserQuery
        answer = empty_repo_service.answer(UserQuery(question="consulta"))
        assert answer.answer == REFUSAL
