"""
T025 — Failing unit tests for safe staging/swap index update behaviour.

Tests that the IndexManager (T028) implements the staging-and-swap strategy:
  - New fragments are written to a staging collection.
  - Only on COMPLETADO does the manager promote staging → active.
  - On FALLIDO the previous active index is preserved untouched.

research.md §Index Update Safety.
FR-016: failed update must not replace the previous usable index.
data-model.md §EstadoIndexacion / §IndexUpdateRun promotion rules.
"""
from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest


def _make_run(mode: str = "FULL_REBUILD", source_ids: list | None = None):
    from rag.domain.indexing import IndexUpdateRun
    from rag.domain.enums import ModoActualizacion
    kwargs: dict = {"mode": ModoActualizacion(mode)}
    if source_ids is not None:
        kwargs["selected_source_ids"] = source_ids
    return IndexUpdateRun(**kwargs)


def _import_index_manager():
    from vectorstore.index_manager import IndexManager
    return IndexManager


def _make_fake_repo():
    """Return a mock repository with the interface expected by IndexManager."""
    repo = MagicMock()
    repo.get_status.return_value = MagicMock(fragment_count=0)
    repo.is_healthy.return_value = True
    repo.query_fragments.return_value = []
    return repo


# ---------------------------------------------------------------------------
# Staging: fragments written during the run don't replace active index yet
# ---------------------------------------------------------------------------

class TestIndexManagerStaging:
    def test_staging_does_not_promote_until_completed(self):
        IndexManager = _import_index_manager()
        repo = _make_fake_repo()
        manager = IndexManager(repository=repo)
        run = _make_run()
        run.start()

        # Simulate writing staged fragments — active should not be changed yet
        manager.begin_staging(run)
        assert not run.promoted

    def test_staging_collects_fragments_without_modifying_active(self):
        IndexManager = _import_index_manager()
        repo = _make_fake_repo()
        manager = IndexManager(repository=repo)
        run = _make_run()
        run.start()
        manager.begin_staging(run)

        from rag.domain.fragments import ContentFragment, FragmentMetadata
        from rag.domain.enums import AreaInstitucional, TipoFuente
        frag = ContentFragment(
            id="f1",
            document_id="doc1",
            text="Texto de prueba",
            chunk_index=0,
            embedding_model="test",
            metadata=FragmentMetadata(
                url="https://utn.edu.ar",
                area=AreaInstitucional.ACADEMICA,
                source_type=TipoFuente.WEB,
            ),
        )
        manager.stage_fragment(run, frag, [0.1] * 384)
        # Active collection should not have been written directly
        repo.upsert_fragments.assert_not_called()


# ---------------------------------------------------------------------------
# Promotion: COMPLETADO run triggers swap
# ---------------------------------------------------------------------------

class TestIndexManagerPromotion:
    def test_promote_completado_run_calls_upsert(self):
        IndexManager = _import_index_manager()
        repo = _make_fake_repo()
        manager = IndexManager(repository=repo)
        run = _make_run()
        run.start()
        manager.begin_staging(run)

        from rag.domain.fragments import ContentFragment, FragmentMetadata
        from rag.domain.enums import AreaInstitucional, TipoFuente
        frag = ContentFragment(
            id="f1",
            document_id="doc1",
            text="Texto",
            chunk_index=0,
            embedding_model="test",
            metadata=FragmentMetadata(
                url="https://utn.edu.ar",
                area=AreaInstitucional.ACADEMICA,
                source_type=TipoFuente.WEB,
            ),
        )
        manager.stage_fragment(run, frag, [0.1] * 384)
        run.complete(documents_indexed=1, documents_failed=0, fragments_indexed=1)
        manager.promote(run)

        assert run.promoted is True
        repo.upsert_fragments.assert_called_once()

    def test_promote_marks_run_as_promoted(self):
        IndexManager = _import_index_manager()
        repo = _make_fake_repo()
        manager = IndexManager(repository=repo)
        run = _make_run()
        run.start()
        manager.begin_staging(run)
        run.complete(documents_indexed=0, documents_failed=0, fragments_indexed=0)
        manager.promote(run)
        assert run.promoted is True


# ---------------------------------------------------------------------------
# Failure: FALLIDO run preserves active index (FR-016)
# ---------------------------------------------------------------------------

class TestIndexManagerFailurePreservation:
    def test_abort_fallido_run_does_not_call_upsert(self):
        IndexManager = _import_index_manager()
        repo = _make_fake_repo()
        manager = IndexManager(repository=repo)
        run = _make_run()
        run.start()
        manager.begin_staging(run)

        from rag.domain.fragments import ContentFragment, FragmentMetadata
        from rag.domain.enums import AreaInstitucional, TipoFuente
        frag = ContentFragment(
            id="f1",
            document_id="doc1",
            text="Texto",
            chunk_index=0,
            embedding_model="test",
            metadata=FragmentMetadata(
                url="https://utn.edu.ar",
                area=AreaInstitucional.ACADEMICA,
                source_type=TipoFuente.WEB,
            ),
        )
        manager.stage_fragment(run, frag, [0.1] * 384)
        run.fail(reason="simulated scraper error")
        manager.abort(run)

        # Active collection must not have been modified
        repo.upsert_fragments.assert_not_called()
        assert run.promoted is False

    def test_cannot_promote_fallido_run(self):
        IndexManager = _import_index_manager()
        repo = _make_fake_repo()
        manager = IndexManager(repository=repo)
        run = _make_run()
        run.start()
        manager.begin_staging(run)
        run.fail(reason="error")
        with pytest.raises(Exception):
            manager.promote(run)
