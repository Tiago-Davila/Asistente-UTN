"""
T014 — Failing unit tests for IndexUpdateRun state transitions.

These tests define the behaviour that rag/domain/indexing.py and
rag/domain/rules.py must satisfy.
They are expected to FAIL until T016 + T020 + T021 are implemented.

data-model.md §EstadoIndexacion: PENDIENTE → EN_PROCESO → COMPLETADO | FALLIDO.
data-model.md §IndexUpdateRun: only COMPLETADO runs can promote.
FR-016: FALLIDO runs preserve the previous usable index.
FR-017: completed runs expose indexed and failed counts.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone


def _import_run():
    from rag.domain.indexing import IndexUpdateRun
    return IndexUpdateRun


def _import_estado():
    from rag.domain.enums import EstadoIndexacion
    return EstadoIndexacion


def _import_mode():
    from rag.domain.enums import ModoActualizacion
    return ModoActualizacion


def _import_rules():
    from rag.domain import rules
    return rules


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

class TestIndexUpdateRunStateTransitions:
    def test_new_run_starts_as_pendiente(self):
        IndexUpdateRun = _import_run()
        EstadoIndexacion = _import_estado()
        ModoActualizacion = _import_mode()
        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        assert run.status == EstadoIndexacion.PENDIENTE

    def test_run_can_transition_to_en_proceso(self):
        IndexUpdateRun = _import_run()
        EstadoIndexacion = _import_estado()
        ModoActualizacion = _import_mode()
        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        run.start()
        assert run.status == EstadoIndexacion.EN_PROCESO

    def test_run_can_transition_to_completado(self):
        IndexUpdateRun = _import_run()
        EstadoIndexacion = _import_estado()
        ModoActualizacion = _import_mode()
        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        run.start()
        run.complete(documents_indexed=10, documents_failed=0, fragments_indexed=50)
        assert run.status == EstadoIndexacion.COMPLETADO

    def test_run_can_transition_to_fallido(self):
        IndexUpdateRun = _import_run()
        EstadoIndexacion = _import_estado()
        ModoActualizacion = _import_mode()
        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        run.start()
        run.fail(reason="scraper error")
        assert run.status == EstadoIndexacion.FALLIDO

    def test_pendiente_cannot_complete_directly(self):
        IndexUpdateRun = _import_run()
        ModoActualizacion = _import_mode()
        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        with pytest.raises(Exception):
            run.complete(documents_indexed=5, documents_failed=0, fragments_indexed=20)

    def test_pendiente_cannot_fail_directly(self):
        IndexUpdateRun = _import_run()
        ModoActualizacion = _import_mode()
        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        with pytest.raises(Exception):
            run.fail(reason="too early")


# ---------------------------------------------------------------------------
# Promotion eligibility (only COMPLETADO may promote)
# ---------------------------------------------------------------------------

class TestPromotionEligibility:
    def test_completado_run_can_promote(self):
        rules = _import_rules()
        IndexUpdateRun = _import_run()
        ModoActualizacion = _import_mode()
        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        run.start()
        run.complete(documents_indexed=5, documents_failed=0, fragments_indexed=20)
        assert rules.can_promote(run) is True

    def test_fallido_run_cannot_promote(self):
        rules = _import_rules()
        IndexUpdateRun = _import_run()
        ModoActualizacion = _import_mode()
        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        run.start()
        run.fail(reason="error")
        assert rules.can_promote(run) is False

    def test_en_proceso_run_cannot_promote(self):
        rules = _import_rules()
        IndexUpdateRun = _import_run()
        ModoActualizacion = _import_mode()
        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        run.start()
        assert rules.can_promote(run) is False

    def test_pendiente_run_cannot_promote(self):
        rules = _import_rules()
        IndexUpdateRun = _import_run()
        ModoActualizacion = _import_mode()
        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        assert rules.can_promote(run) is False


# ---------------------------------------------------------------------------
# Counts (FR-017)
# ---------------------------------------------------------------------------

class TestIndexUpdateRunCounts:
    def test_completed_run_exposes_counts(self):
        IndexUpdateRun = _import_run()
        ModoActualizacion = _import_mode()
        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        run.start()
        run.complete(documents_indexed=8, documents_failed=2, fragments_indexed=40)
        assert run.documents_indexed == 8
        assert run.documents_failed == 2
        assert run.fragments_indexed == 40

    def test_incremental_requires_selected_sources(self):
        IndexUpdateRun = _import_run()
        ModoActualizacion = _import_mode()
        with pytest.raises(Exception):
            IndexUpdateRun(
                mode=ModoActualizacion.INCREMENTAL_SELECTED_SOURCES,
                selected_source_ids=[],
            )
