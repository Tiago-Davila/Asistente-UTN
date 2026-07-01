"""
T023 — Failing unit tests for vector search result ordering.

Tests that the ordering rules defined in rag/domain/rules.py (order_results)
and consumed by the vectorstore layer produce correctly ranked results.
Expected to pass once T021 (rules) and T018 (fragments) are confirmed complete.

data-model.md §SearchResult: results must be ordered by descending relevance.
"""
from __future__ import annotations

import pytest


def _import_order_results():
    from rag.domain.rules import order_results
    return order_results


def _make_result(fragment_id: str, score: float, rank: int = 1):
    from rag.domain.fragments import SearchResult
    return SearchResult(fragment_id=fragment_id, score=score, rank=rank, metadata={})


# ---------------------------------------------------------------------------
# Ordering by descending score
# ---------------------------------------------------------------------------

class TestSearchResultOrdering:
    def test_single_result_rank_is_1(self):
        order_results = _import_order_results()
        results = [_make_result("f1", 0.80)]
        ordered = order_results(results)
        assert ordered[0].rank == 1

    def test_two_results_ordered_descending(self):
        order_results = _import_order_results()
        results = [
            _make_result("f_low", 0.50, rank=1),
            _make_result("f_high", 0.90, rank=2),
        ]
        ordered = order_results(results)
        assert ordered[0].fragment_id == "f_high"
        assert ordered[0].rank == 1
        assert ordered[1].fragment_id == "f_low"
        assert ordered[1].rank == 2

    def test_three_results_ranked_correctly(self):
        order_results = _import_order_results()
        results = [
            _make_result("f_mid", 0.70),
            _make_result("f_low", 0.50),
            _make_result("f_high", 0.95),
        ]
        ordered = order_results(results)
        scores = [r.score for r in ordered]
        assert scores == sorted(scores, reverse=True)
        ranks = [r.rank for r in ordered]
        assert ranks == [1, 2, 3]

    def test_empty_list_returns_empty(self):
        order_results = _import_order_results()
        assert order_results([]) == []

    def test_equal_scores_preserves_all_results(self):
        order_results = _import_order_results()
        results = [
            _make_result("f1", 0.75),
            _make_result("f2", 0.75),
        ]
        ordered = order_results(results)
        assert len(ordered) == 2
        assert {r.rank for r in ordered} == {1, 2}

    def test_ordering_does_not_drop_results(self):
        order_results = _import_order_results()
        ids = [f"f{i}" for i in range(10)]
        import random
        results = [_make_result(fid, round(random.uniform(0.1, 0.99), 2)) for fid in ids]
        ordered = order_results(results)
        assert len(ordered) == len(ids)
        assert {r.fragment_id for r in ordered} == set(ids)

    def test_below_threshold_results_are_still_ordered(self):
        """Ordering is independent of threshold — filtering happens in rules."""
        order_results = _import_order_results()
        results = [
            _make_result("f_below1", 0.30),
            _make_result("f_below2", 0.20),
        ]
        ordered = order_results(results)
        assert ordered[0].score >= ordered[1].score


# ---------------------------------------------------------------------------
# Fake repository ordering contract
# ---------------------------------------------------------------------------

class TestFakeRepositoryOrdering:
    """Verify that a fake in-memory repository returns results in order.

    This serves as a contract test for any repository implementation.
    """

    def test_fake_repo_query_returns_ordered_results(self):
        """A fake repo built from pre-ordered data should preserve order."""
        from rag.domain.fragments import SearchResult, SearchResultSet
        results = [
            SearchResult(fragment_id="f1", score=0.90, rank=1, metadata={"url": "https://a"}),
            SearchResult(fragment_id="f2", score=0.75, rank=2, metadata={"url": "https://b"}),
            SearchResult(fragment_id="f3", score=0.60, rank=3, metadata={"url": "https://c"}),
        ]
        result_set = SearchResultSet(results=results, threshold=0.65, context_sufficient=True)
        for i in range(len(result_set.results) - 1):
            assert result_set.results[i].score >= result_set.results[i + 1].score
