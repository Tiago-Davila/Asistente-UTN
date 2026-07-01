"""
T034 — Failing unit tests for prompt context inclusion.

Defines the contract that rag/prompting.py must satisfy.
FR-003: retrieved content must be included in the generation prompt.
FR-005: citation metadata (URL, title) must be available in the prompt.
FR-008: prompt must not invite the LLM to invent content.
"""
from __future__ import annotations

import pytest


def _builder():
    from rag.prompting import PromptBuilder
    return PromptBuilder()


def _make_result(fragment_id: str, text: str, url: str, title: str | None = None, score: float = 0.80):
    from rag.domain.fragments import SearchResult
    return SearchResult(
        fragment_id=fragment_id,
        score=score,
        rank=1,
        metadata={"url": url, "title": title, "area": "ACADEMICA", "text": text},
    )


class TestPromptBuilderContextInclusion:
    def test_retrieved_text_included_in_prompt(self):
        builder = _builder()
        results = [_make_result("f1", "Inscripciones en marzo.", "https://utn.edu.ar/ins")]
        prompt = builder.build(question="Cuando son las inscripciones?", results=results)
        assert "Inscripciones en marzo." in prompt or "inscripciones" in prompt.lower()

    def test_source_url_present_in_prompt(self):
        builder = _builder()
        results = [_make_result("f1", "Texto", "https://utn.edu.ar/page")]
        prompt = builder.build(question="consulta?", results=results)
        assert "https://utn.edu.ar/page" in prompt

    def test_question_present_in_prompt(self):
        builder = _builder()
        results = [_make_result("f1", "Texto", "https://utn.edu.ar/page")]
        prompt = builder.build(question="Cuando es la inscripcion?", results=results)
        assert "Cuando es la inscripcion?" in prompt

    def test_multiple_results_all_included(self):
        builder = _builder()
        results = [
            _make_result("f1", "Fragmento uno", "https://utn.edu.ar/a"),
            _make_result("f2", "Fragmento dos", "https://utn.edu.ar/b"),
        ]
        prompt = builder.build(question="consulta?", results=results)
        assert "Fragmento uno" in prompt
        assert "Fragmento dos" in prompt

    def test_prompt_instructs_argentinian_spanish(self):
        """FR-004: answers must be in natural Argentinian Spanish."""
        builder = _builder()
        results = [_make_result("f1", "Texto", "https://utn.edu.ar/a")]
        prompt = builder.build(question="consulta?", results=results)
        prompt_lower = prompt.lower()
        assert any(kw in prompt_lower for kw in ["español", "castellano", "argentina", "argentino"])

    def test_prompt_instructs_not_to_invent(self):
        """FR-008: the prompt must tell the LLM to stay within provided context."""
        builder = _builder()
        results = [_make_result("f1", "Texto", "https://utn.edu.ar/a")]
        prompt = builder.build(question="consulta?", results=results)
        prompt_lower = prompt.lower()
        assert any(kw in prompt_lower for kw in ["solo", "únicamente", "unicamente", "exclusivamente", "contexto", "fuente"])

    def test_empty_results_raises_or_returns_refusal_prompt(self):
        """No results should not produce a generation prompt that invites hallucination."""
        builder = _builder()
        with pytest.raises(Exception):
            builder.build(question="consulta?", results=[])
