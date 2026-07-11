"""
T013 — Failing unit tests for citation integrity rules.
T109 — Unit tests for citable-source presence (FR-005, rev. 2026-07-10).

These tests define the behaviour that rag/domain/rules.py must satisfy.
They are expected to FAIL until T016 + T018 + T019 + T021 are implemented.

FR-005: every answer based on retrieved content must include at least one URL.
FR-005 (rev. 2026-07-10): context that clears the relevance threshold but
carries no citable URL among retrieved fragments must fall back to the
insufficient-context refusal instead of an uncited answer.
FR-008: cited sources must correspond to retrieved fragments only.
data-model.md §CitedSource: url required; title when available.
data-model.md §AssistantAnswer: sources must originate from retrieved context.
"""
from __future__ import annotations

import pytest


def _import_rules():
    from rag.domain import rules
    return rules


def _import_search_result():
    from rag.domain.fragments import SearchResult
    return SearchResult


def _import_search_result_set():
    from rag.domain.fragments import SearchResultSet
    return SearchResultSet


def _import_cited_source():
    from rag.domain.queries import CitedSource
    return CitedSource


def _make_search_result(fragment_id: str, url: str, title: str | None = None):
    SearchResult = _import_search_result()
    return SearchResult(
        fragment_id=fragment_id,
        score=0.80,
        rank=1,
        metadata={"url": url, "title": title},
    )


# ---------------------------------------------------------------------------
# Citation originates from retrieved fragments
# ---------------------------------------------------------------------------

class TestCitationIntegrity:
    def test_cited_url_in_retrieved_fragments_passes(self):
        rules = _import_rules()
        results = [_make_search_result("f1", "https://utn.edu.ar/page")]
        CitedSource = _import_cited_source()
        cited = [CitedSource(url="https://utn.edu.ar/page")]
        assert rules.validate_citation_integrity(cited, results) is True

    def test_cited_url_not_in_retrieved_fragments_fails(self):
        rules = _import_rules()
        results = [_make_search_result("f1", "https://utn.edu.ar/page")]
        CitedSource = _import_cited_source()
        cited = [CitedSource(url="https://example.com/unrelated")]
        assert rules.validate_citation_integrity(cited, results) is False

    def test_empty_citations_with_results_fails(self):
        rules = _import_rules()
        results = [_make_search_result("f1", "https://utn.edu.ar/page")]
        assert rules.validate_citation_integrity([], results) is False

    def test_empty_citations_with_empty_results_passes(self):
        """No results → refusal, no citation required."""
        rules = _import_rules()
        assert rules.validate_citation_integrity([], []) is True

    def test_multiple_cited_sources_all_in_results(self):
        rules = _import_rules()
        results = [
            _make_search_result("f1", "https://utn.edu.ar/a"),
            _make_search_result("f2", "https://utn.edu.ar/b"),
        ]
        CitedSource = _import_cited_source()
        cited = [
            CitedSource(url="https://utn.edu.ar/a"),
            CitedSource(url="https://utn.edu.ar/b"),
        ]
        assert rules.validate_citation_integrity(cited, results) is True

    def test_one_citation_outside_results_fails(self):
        rules = _import_rules()
        results = [_make_search_result("f1", "https://utn.edu.ar/a")]
        CitedSource = _import_cited_source()
        cited = [
            CitedSource(url="https://utn.edu.ar/a"),
            CitedSource(url="https://utn.edu.ar/not-retrieved"),
        ]
        assert rules.validate_citation_integrity(cited, results) is False


# ---------------------------------------------------------------------------
# Title included when available (FR-005)
# ---------------------------------------------------------------------------

class TestCitedSourceTitle:
    def test_title_is_preserved_when_available(self):
        rules = _import_rules()
        results = [_make_search_result("f1", "https://utn.edu.ar/a", title="Inicio")]
        cited = rules.build_cited_sources(results)
        assert any(s.title == "Inicio" for s in cited)

    def test_title_is_none_when_unavailable(self):
        rules = _import_rules()
        results = [_make_search_result("f1", "https://utn.edu.ar/a", title=None)]
        cited = rules.build_cited_sources(results)
        assert any(s.url == "https://utn.edu.ar/a" for s in cited)
        source = next(s for s in cited if s.url == "https://utn.edu.ar/a")
        assert source.title is None


# ---------------------------------------------------------------------------
# Citable source presence (FR-005, revised 2026-07-10)
# ---------------------------------------------------------------------------

class TestCitableSourcePresence:
    def test_no_url_among_fragments_is_not_citable(self):
        rules = _import_rules()
        SearchResult = _import_search_result()
        SearchResultSet = _import_search_result_set()
        results = [
            SearchResult(fragment_id="f1", score=0.90, rank=1, metadata={}),
        ]
        result_set = SearchResultSet(results=results, threshold=0.65)
        assert rules.has_citable_source(result_set) is False

    def test_at_least_one_url_is_citable(self):
        rules = _import_rules()
        SearchResult = _import_search_result()
        SearchResultSet = _import_search_result_set()
        results = [
            SearchResult(fragment_id="f1", score=0.90, rank=1, metadata={}),
            SearchResult(
                fragment_id="f2",
                score=0.70,
                rank=2,
                metadata={"url": "https://utn.edu.ar/a"},
            ),
        ]
        result_set = SearchResultSet(results=results, threshold=0.65)
        assert rules.has_citable_source(result_set) is True

    def test_empty_results_are_not_citable(self):
        rules = _import_rules()
        SearchResultSet = _import_search_result_set()
        result_set = SearchResultSet(results=[], threshold=0.65)
        assert rules.has_citable_source(result_set) is False

    def test_threshold_sufficient_without_url_yields_refusal(self):
        """Context above threshold but with no citable URL → treated as
        insufficient context (FR-005 rev.), not an uncited answer."""
        rules = _import_rules()
        SearchResult = _import_search_result()
        SearchResultSet = _import_search_result_set()
        results = [
            SearchResult(fragment_id="f1", score=0.90, rank=1, metadata={}),
        ]
        result_set = SearchResultSet(results=results, threshold=0.65)
        assert rules.is_context_sufficient(result_set) is True
        assert rules.has_citable_source(result_set) is False
        combined = rules.is_context_sufficient(result_set) and rules.has_citable_source(
            result_set
        )
        assert combined is False

    def test_threshold_sufficient_with_url_yields_answer(self):
        """Context above threshold with at least one citable URL → the
        combined check passes and an answer with a source is produced."""
        rules = _import_rules()
        SearchResult = _import_search_result()
        SearchResultSet = _import_search_result_set()
        results = [
            SearchResult(
                fragment_id="f1",
                score=0.90,
                rank=1,
                metadata={"url": "https://utn.edu.ar/a"},
            ),
        ]
        result_set = SearchResultSet(results=results, threshold=0.65)
        combined = rules.is_context_sufficient(result_set) and rules.has_citable_source(
            result_set
        )
        assert combined is True
