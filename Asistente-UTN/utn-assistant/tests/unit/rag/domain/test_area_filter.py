"""
T015 — Failing unit tests for area filter validation.

These tests define the behaviour that rag/domain/enums.py and
rag/domain/queries.py must satisfy.
They are expected to FAIL until T016 + T019 are implemented.

FR-009: area filter is optional; when given must be a valid AreaInstitucional.
FR-010: no filter → search all indexed content.
data-model.md §AreaInstitucional: ACADEMICA, ADMINISTRATIVA, BIENESTAR, EXTENSION.
"""
from __future__ import annotations

import pytest


def _import_area():
    from rag.domain.enums import AreaInstitucional
    return AreaInstitucional


def _import_user_query():
    from rag.domain.queries import UserQuery
    return UserQuery


# ---------------------------------------------------------------------------
# AreaInstitucional enum completeness
# ---------------------------------------------------------------------------

class TestAreaInstitucionalEnum:
    def test_all_four_areas_exist(self):
        AreaInstitucional = _import_area()
        names = {a.name for a in AreaInstitucional}
        assert names == {"ACADEMICA", "ADMINISTRATIVA", "BIENESTAR", "EXTENSION"}

    def test_area_has_string_value(self):
        AreaInstitucional = _import_area()
        for area in AreaInstitucional:
            assert isinstance(area.value, str)
            assert len(area.value) > 0

    def test_area_values_are_uppercase(self):
        AreaInstitucional = _import_area()
        for area in AreaInstitucional:
            assert area.value == area.value.upper()


# ---------------------------------------------------------------------------
# UserQuery area filter validation
# ---------------------------------------------------------------------------

class TestUserQueryAreaFilterValidation:
    def test_no_area_means_search_all(self):
        """FR-010: no filter → search across full index."""
        UserQuery = _import_user_query()
        q = UserQuery(question="consulta sin area")
        assert q.area_filter is None

    def test_academica_filter_accepted(self):
        UserQuery = _import_user_query()
        AreaInstitucional = _import_area()
        q = UserQuery(question="consulta", area_filter=AreaInstitucional.ACADEMICA)
        assert q.area_filter == AreaInstitucional.ACADEMICA

    def test_administrativa_filter_accepted(self):
        UserQuery = _import_user_query()
        AreaInstitucional = _import_area()
        q = UserQuery(question="consulta", area_filter=AreaInstitucional.ADMINISTRATIVA)
        assert q.area_filter == AreaInstitucional.ADMINISTRATIVA

    def test_bienestar_filter_accepted(self):
        UserQuery = _import_user_query()
        AreaInstitucional = _import_area()
        q = UserQuery(question="consulta", area_filter=AreaInstitucional.BIENESTAR)
        assert q.area_filter == AreaInstitucional.BIENESTAR

    def test_extension_filter_accepted(self):
        UserQuery = _import_user_query()
        AreaInstitucional = _import_area()
        q = UserQuery(question="consulta", area_filter=AreaInstitucional.EXTENSION)
        assert q.area_filter == AreaInstitucional.EXTENSION

    def test_invalid_string_area_is_rejected(self):
        UserQuery = _import_user_query()
        with pytest.raises(Exception):
            UserQuery(question="consulta", area_filter="INVALID_AREA")  # type: ignore
