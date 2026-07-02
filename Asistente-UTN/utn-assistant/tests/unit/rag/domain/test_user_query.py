"""
T011 — Failing unit tests for UserQuery validation.

These tests define the behaviour that rag/domain/queries.py must satisfy.
They are expected to FAIL until T019 is implemented.

FR-002: question must be non-empty and ≤ MAX_QUESTION_LENGTH (2000 chars).
FR-009: area_filter is optional; when given, must be a valid AreaInstitucional.
data-model.md §UserQuery: max_results ≤ 10.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helpers — imported lazily so tests fail with ImportError until implemented
# ---------------------------------------------------------------------------

def _import_user_query():
    from rag.domain.queries import UserQuery
    return UserQuery


def _import_area():
    from rag.domain.enums import AreaInstitucional
    return AreaInstitucional


# ---------------------------------------------------------------------------
# Empty question
# ---------------------------------------------------------------------------

class TestUserQueryEmptyQuestion:
    def test_empty_string_is_rejected(self):
        UserQuery = _import_user_query()
        with pytest.raises(Exception):
            UserQuery(question="")

    def test_whitespace_only_is_rejected(self):
        UserQuery = _import_user_query()
        with pytest.raises(Exception):
            UserQuery(question="   ")

    def test_tab_only_is_rejected(self):
        UserQuery = _import_user_query()
        with pytest.raises(Exception):
            UserQuery(question="\t\n")


# ---------------------------------------------------------------------------
# Maximum question length (FR-002, data-model.md §UserQuery)
# ---------------------------------------------------------------------------

class TestUserQueryMaxLength:
    def test_exactly_2000_chars_is_accepted(self):
        UserQuery = _import_user_query()
        q = UserQuery(question="a" * 2000)
        assert len(q.question) == 2000

    def test_2001_chars_is_rejected(self):
        UserQuery = _import_user_query()
        with pytest.raises(Exception):
            UserQuery(question="a" * 2001)

    def test_one_char_is_accepted(self):
        UserQuery = _import_user_query()
        q = UserQuery(question="?")
        assert q.question == "?"


# ---------------------------------------------------------------------------
# Optional area filter (FR-009)
# ---------------------------------------------------------------------------

class TestUserQueryAreaFilter:
    def test_no_area_filter_is_accepted(self):
        UserQuery = _import_user_query()
        q = UserQuery(question="Cuando es la inscripcion?")
        assert q.area_filter is None

    def test_valid_area_filter_is_accepted(self):
        UserQuery = _import_user_query()
        AreaInstitucional = _import_area()
        q = UserQuery(
            question="Cuando es la inscripcion?",
            area_filter=AreaInstitucional.ACADEMICA,
        )
        assert q.area_filter == AreaInstitucional.ACADEMICA

    def test_all_valid_areas_accepted(self):
        UserQuery = _import_user_query()
        AreaInstitucional = _import_area()
        for area in AreaInstitucional:
            q = UserQuery(question="consulta?", area_filter=area)
            assert q.area_filter == area


# ---------------------------------------------------------------------------
# max_results bound (data-model.md §UserQuery: ≤ 10)
# ---------------------------------------------------------------------------

class TestUserQueryMaxResults:
    def test_default_max_results_is_none_or_valid(self):
        UserQuery = _import_user_query()
        q = UserQuery(question="consulta?")
        assert q.max_results is None or (1 <= q.max_results <= 10)

    def test_max_results_of_1_is_accepted(self):
        UserQuery = _import_user_query()
        q = UserQuery(question="consulta?", max_results=1)
        assert q.max_results == 1

    def test_max_results_of_10_is_accepted(self):
        UserQuery = _import_user_query()
        q = UserQuery(question="consulta?", max_results=10)
        assert q.max_results == 10

    def test_max_results_of_11_is_rejected(self):
        UserQuery = _import_user_query()
        with pytest.raises(Exception):
            UserQuery(question="consulta?", max_results=11)

    def test_max_results_of_0_is_rejected(self):
        UserQuery = _import_user_query()
        with pytest.raises(Exception):
            UserQuery(question="consulta?", max_results=0)
