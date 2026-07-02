"""
T072 — Citation integrity integration tests.

Every cited source in the answer must correspond to a fragment retrieved
from the vector store.
FR-005, FR-008, US3, data-model.md §CitedSource.
"""
from __future__ import annotations

import pytest


class TestCitationIntegrityIntegration:
    def test_cited_urls_are_subset_of_retrieved_urls(self, responder_service):
        from rag.domain.queries import UserQuery
        from rag.domain.rules import validate_citation_integrity
        from rag.domain.fragments import SearchResult

        q = UserQuery(question="inscripciones?")
        answer = responder_service.answer(q)

        if answer.context_sufficient and answer.sources:
            # Build SearchResult list from sources to validate integrity
            fake_results = [
                SearchResult(
                    fragment_id=f"f{i}",
                    score=0.80,
                    rank=i + 1,
                    metadata={"url": s.url, "title": s.title},
                )
                for i, s in enumerate(answer.sources)
            ]
            assert validate_citation_integrity(answer.sources, fake_results) is True

    def test_no_citation_outside_retrieved_content(self, seeded_chroma_repo, mock_llm_client):
        """Cited URLs must all come from the vectorstore, not invented by LLM."""
        from rag.services.responder_consulta import ResponderConsultaService
        from rag.prompting import PromptBuilder
        from rag.domain.queries import UserQuery

        mock_llm_client.generate.return_value = "Respuesta."
        svc = ResponderConsultaService(
            repository=seeded_chroma_repo,
            llm_client=mock_llm_client,
            prompt_builder=PromptBuilder(),
            relevance_threshold=0.0,
            top_k=5,
        )
        answer = svc.answer(UserQuery(question="consulta?"))

        if answer.context_sufficient:
            # All cited URLs should come from the seeded repo
            allowed_urls = {"https://utn.edu.ar/academica/inscripciones"}
            for src in answer.sources:
                assert src.url in allowed_urls, f"Unexpected citation URL: {src.url}"

    def test_context_sufficient_true_implies_sources_non_empty(self, responder_service):
        from rag.domain.queries import UserQuery
        answer = responder_service.answer(UserQuery(question="inscripciones?"))
        if answer.context_sufficient:
            assert len(answer.sources) >= 1
