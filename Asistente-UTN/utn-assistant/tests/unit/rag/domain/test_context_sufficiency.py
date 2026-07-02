"""
T012 — Failing unit tests for context sufficiency and refusal rules.

These tests define the behaviour that rag/domain/rules.py must satisfy.
They are expected to FAIL until T016 + T021 are implemented.

FR-006: refuse when no result meets the global relevance threshold.
FR-007: refusal text is exactly "No tengo informacion suficiente sobre este
        tema en las fuentes institucionales disponibles."
FR-008: no claims outside retrieved context.
data-model.md §SearchResultSet: context_sufficient driven by threshold.
"""
from __future__ import annotations

import pytest

REFUSAL_TEXT = (
    "No tengo informacion suficiente sobre este tema "
    "en las fuentes institucionales disponibles."
)


def _import_rules():
    from rag.domain import rules
    return rules


def _import_search_result_set():
    from rag.domain.fragments import SearchResultSet
    return SearchResultSet


def _import_search_result():
    from rag.domain.fragments import SearchResult
    return SearchResult


# ---------------------------------------------------------------------------
# context_sufficient computation
# ---------------------------------------------------------------------------

class TestContextSufficiency:
    def test_empty_results_are_insufficient(self):
        rules = _import_rules()
        SearchResultSet = _import_search_result_set()
        result_set = SearchResultSet(results=[], threshold=0.65)
        assert rules.is_context_sufficient(result_set) is False

    def test_all_below_threshold_are_insufficient(self):
        rules = _import_rules()
        SearchResultSet = _import_search_result_set()
        SearchResult = _import_search_result()
        results = [
            SearchResult(fragment_id="f1", score=0.40, rank=1, metadata={}),
            SearchResult(fragment_id="f2", score=0.50, rank=2, metadata={}),
        ]
        result_set = SearchResultSet(results=results, threshold=0.65)
        assert rules.is_context_sufficient(result_set) is False

    def test_one_at_threshold_is_sufficient(self):
        rules = _import_rules()
        SearchResultSet = _import_search_result_set()
        SearchResult = _import_search_result()
        results = [
            SearchResult(fragment_id="f1", score=0.65, rank=1, metadata={}),
        ]
        result_set = SearchResultSet(results=results, threshold=0.65)
        assert rules.is_context_sufficient(result_set) is True

    def test_one_above_threshold_is_sufficient(self):
        rules = _import_rules()
        SearchResultSet = _import_search_result_set()
        SearchResult = _import_search_result()
        results = [
            SearchResult(fragment_id="f1", score=0.90, rank=1, metadata={}),
        ]
        result_set = SearchResultSet(results=results, threshold=0.65)
        assert rules.is_context_sufficient(result_set) is True


# ---------------------------------------------------------------------------
# Refusal text (FR-007)
# ---------------------------------------------------------------------------

class TestRefusalText:
    def test_refusal_constant_is_exact(self):
        rules = _import_rules()
        assert rules.REFUSAL_TEXT == REFUSAL_TEXT

    def test_refusal_text_not_empty(self):
        rules = _import_rules()
        assert len(rules.REFUSAL_TEXT.strip()) > 0

    def test_refusal_answer_uses_exact_text(self):
        rules = _import_rules()
        answer = rules.make_refusal_answer()
        assert answer.answer == REFUSAL_TEXT
        assert answer.context_sufficient is False
        assert answer.sources == []
