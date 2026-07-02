"""
T013 — Failing unit tests for citation integrity rules.

These tests define the behaviour that rag/domain/rules.py must satisfy.
They are expected to FAIL until T016 + T018 + T019 + T021 are implemented.

FR-005: every answer based on retrieved content must include at least one URL.
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
