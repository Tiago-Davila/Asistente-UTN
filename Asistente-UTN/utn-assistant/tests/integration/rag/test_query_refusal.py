"""
T071 — RAG refusal integration tests.
T110 — Refusal case for relevant context without a citable source
        (FR-005, rev. 2026-07-10).

Tests the refusal path with a real ChromaDB (threshold above scores),
empty retrieval scenarios, and threshold-sufficient context that carries
no citable source URL among the retrieved fragments.
FR-005 (rev.), FR-006, FR-007, US2.
"""
from __future__ import annotations

from unittest.mock import MagicMock

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


def _make_no_url_result(fragment_id: str, score: float = 0.90):
    """A threshold-sufficient result whose metadata carries no source URL."""
    from rag.domain.fragments import SearchResult
    return SearchResult(
        fragment_id=fragment_id,
        score=score,
        rank=1,
        metadata={"title": "Pagina sin URL registrada"},
    )


@pytest.fixture()
def no_citable_url_service(mock_llm_client):
    """Service whose repository returns threshold-sufficient context with no
    citable source URL among the retrieved fragments (FR-005 rev.)."""
    from rag.services.responder_consulta import ResponderConsultaService
    from rag.prompting import PromptBuilder
    repo = MagicMock()
    repo.query_fragments.return_value = [_make_no_url_result("f1", score=0.90)]
    return ResponderConsultaService(
        repository=repo,
        llm_client=mock_llm_client,
        prompt_builder=PromptBuilder(),
        relevance_threshold=0.65,
        top_k=5,
        embeddings_adapter=None,
    )


class TestQueryRefusalNoCitableSource:
    """FR-005 (rev. 2026-07-10): relevant context without a citable URL among
    retrieved fragments must fall back to the refusal, never an uncited
    answer."""

    def test_refusal_when_context_relevant_but_no_url(self, no_citable_url_service):
        from rag.domain.queries import UserQuery
        answer = no_citable_url_service.answer(
            UserQuery(question="consulta con contexto relevante sin fuente")
        )
        assert answer.context_sufficient is False
        assert answer.answer == REFUSAL

    def test_sources_empty_when_no_citable_url(self, no_citable_url_service):
        from rag.domain.queries import UserQuery
        answer = no_citable_url_service.answer(UserQuery(question="consulta"))
        assert answer.sources == []

    def test_llm_not_called_when_no_citable_url(
        self, no_citable_url_service, mock_llm_client
    ):
        from rag.domain.queries import UserQuery
        no_citable_url_service.answer(UserQuery(question="consulta"))
        mock_llm_client.generate.assert_not_called()
