"""
T035 — Failing unit tests for answer orchestration (ResponderConsultaService).

Uses mocked vectorstore repository and mocked Ollama client.
FR-001: accept natural-language question.
FR-003: retrieve relevant fragments before generating.
FR-006: refuse when no fragment meets threshold.
FR-007: use the exact refusal text.
FR-005: include source URL and title in answer.
"""
from __future__ import annotations

from unittest.mock import MagicMock, AsyncMock

import pytest


REFUSAL_TEXT = (
    "No tengo informacion suficiente sobre este tema "
    "en las fuentes institucionales disponibles."
)


def _make_result(fragment_id: str, url: str, score: float = 0.80, title: str | None = None):
    from rag.domain.fragments import SearchResult
    return SearchResult(
        fragment_id=fragment_id,
        score=score,
        rank=1,
        metadata={"url": url, "title": title, "area": "ACADEMICA"},
    )


def _make_service(repo=None, llm=None, threshold: float = 0.65, top_k: int = 5):
    from rag.services.responder_consulta import ResponderConsultaService
    from rag.prompting import PromptBuilder
    return ResponderConsultaService(
        repository=repo or MagicMock(),
        llm_client=llm or MagicMock(),
        prompt_builder=PromptBuilder(),
        relevance_threshold=threshold,
        top_k=top_k,
    )


class TestResponderConsultaServiceSuccess:
    def test_answer_returned_when_context_sufficient(self):
        repo = MagicMock()
        repo.query_fragments.return_value = [_make_result("f1", "https://utn.edu.ar/a", score=0.80)]
        llm = MagicMock()
        llm.generate.return_value = "Las inscripciones son en marzo."

        svc = _make_service(repo=repo, llm=llm)
        from rag.domain.queries import UserQuery
        q = UserQuery(question="Cuando son las inscripciones?")
        answer = svc.answer(q)

        assert answer.context_sufficient is True
        assert answer.answer == "Las inscripciones son en marzo."
        assert len(answer.sources) >= 1

    def test_sources_include_url(self):
        repo = MagicMock()
        repo.query_fragments.return_value = [
            _make_result("f1", "https://utn.edu.ar/a", score=0.80, title="Inicio"),
        ]
        llm = MagicMock()
        llm.generate.return_value = "Respuesta."

        svc = _make_service(repo=repo, llm=llm)
        from rag.domain.queries import UserQuery
        answer = svc.answer(UserQuery(question="consulta?"))

        assert answer.sources[0].url == "https://utn.edu.ar/a"

    def test_source_title_included_when_available(self):
        repo = MagicMock()
        repo.query_fragments.return_value = [
            _make_result("f1", "https://utn.edu.ar/a", score=0.80, title="Pagina Principal"),
        ]
        llm = MagicMock()
        llm.generate.return_value = "Respuesta."

        svc = _make_service(repo=repo, llm=llm)
        from rag.domain.queries import UserQuery
        answer = svc.answer(UserQuery(question="consulta?"))
        assert answer.sources[0].title == "Pagina Principal"


class TestResponderConsultaServiceRefusal:
    def test_refusal_when_no_results(self):
        repo = MagicMock()
        repo.query_fragments.return_value = []

        svc = _make_service(repo=repo)
        from rag.domain.queries import UserQuery
        answer = svc.answer(UserQuery(question="consulta sin resultados"))

        assert answer.context_sufficient is False
        assert answer.answer == REFUSAL_TEXT
        assert answer.sources == []

    def test_refusal_when_all_below_threshold(self):
        repo = MagicMock()
        repo.query_fragments.return_value = [
            _make_result("f1", "https://utn.edu.ar/a", score=0.40),
            _make_result("f2", "https://utn.edu.ar/b", score=0.30),
        ]
        svc = _make_service(repo=repo, threshold=0.65)
        from rag.domain.queries import UserQuery
        answer = svc.answer(UserQuery(question="consulta irrelevante"))

        assert answer.context_sufficient is False
        assert answer.answer == REFUSAL_TEXT

    def test_llm_not_called_on_refusal(self):
        repo = MagicMock()
        repo.query_fragments.return_value = []
        llm = MagicMock()

        svc = _make_service(repo=repo, llm=llm)
        from rag.domain.queries import UserQuery
        svc.answer(UserQuery(question="consulta"))

        llm.generate.assert_not_called()


class TestResponderConsultaServiceAreaFilter:
    def test_area_filter_passed_to_repository(self):
        from rag.domain.enums import AreaInstitucional
        repo = MagicMock()
        repo.query_fragments.return_value = [
            _make_result("f1", "https://utn.edu.ar/a", score=0.80),
        ]
        llm = MagicMock()
        llm.generate.return_value = "Respuesta."

        svc = _make_service(repo=repo, llm=llm)
        from rag.domain.queries import UserQuery
        q = UserQuery(question="consulta?", area_filter=AreaInstitucional.ACADEMICA)
        svc.answer(q)

        call_kwargs = repo.query_fragments.call_args
        assert call_kwargs.kwargs.get("area_filter") == AreaInstitucional.ACADEMICA or \
               (call_kwargs.args and AreaInstitucional.ACADEMICA in call_kwargs.args)
