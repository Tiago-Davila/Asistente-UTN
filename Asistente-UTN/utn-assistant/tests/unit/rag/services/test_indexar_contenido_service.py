"""
T036 — Failing unit tests for indexing orchestration (IndexarContenidoService).

FR-015: full rebuild and incremental selected-source update flows.
FR-016: failed update preserves previous index.
FR-017: reports indexed and failed counts.
FR-014: continues when individual source fails.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_source(source_id: str = "src1"):
    from rag.domain.sources import InstitutionalSource
    from rag.domain.enums import AreaInstitucional, TipoFuente
    return InstitutionalSource(
        id=source_id,
        url=f"https://utn.edu.ar/{source_id}",
        area=AreaInstitucional.ACADEMICA,
        source_type=TipoFuente.WEB,
        active=True,
    )


def _make_service(scraper=None, index_loader=None, index_manager=None, repo=None):
    from rag.services.indexar_contenido import IndexarContenidoService
    return IndexarContenidoService(
        scraper=scraper or MagicMock(),
        index_loader=index_loader or MagicMock(),
        index_manager=index_manager or MagicMock(),
        repository=repo or MagicMock(),
    )


class TestIndexarContenidoFullRebuild:
    def test_full_rebuild_creates_completado_run(self):
        from rag.domain.enums import EstadoIndexacion
        scraper = MagicMock()
        scraper.scrape_sources.return_value = ([], [])  # no docs, no failures
        index_loader = MagicMock()
        index_loader.load.return_value = 0
        index_manager = MagicMock()

        svc = _make_service(scraper=scraper, index_loader=index_loader, index_manager=index_manager)
        run = svc.full_rebuild(sources=[_make_source()])

        assert run.status == EstadoIndexacion.COMPLETADO

    def test_full_rebuild_promotes_index(self):
        scraper = MagicMock()
        scraper.scrape_sources.return_value = ([], [])
        index_loader = MagicMock()
        index_loader.load.return_value = 0
        index_manager = MagicMock()

        svc = _make_service(scraper=scraper, index_loader=index_loader, index_manager=index_manager)
        svc.full_rebuild(sources=[_make_source()])

        index_manager.promote.assert_called_once()

    def test_full_rebuild_reports_failure_counts(self):
        from rag.domain.sources import ExtractedDocument
        from rag.domain.enums import EstadoIndexacion
        scraper = MagicMock()
        scraper.scrape_sources.return_value = ([], [("src1", "timeout")])
        index_loader = MagicMock()
        index_loader.load.return_value = 0
        index_manager = MagicMock()

        svc = _make_service(scraper=scraper, index_loader=index_loader, index_manager=index_manager)
        run = svc.full_rebuild(sources=[_make_source()])

        assert run.documents_failed >= 1


class TestIndexarContenidoFailureHandling:
    def test_scraper_exception_produces_fallido_run(self):
        from rag.domain.enums import EstadoIndexacion
        scraper = MagicMock()
        scraper.scrape_sources.side_effect = RuntimeError("network error")
        index_manager = MagicMock()

        svc = _make_service(scraper=scraper, index_manager=index_manager)
        run = svc.full_rebuild(sources=[_make_source()])

        assert run.status == EstadoIndexacion.FALLIDO

    def test_fallido_run_does_not_promote(self):
        scraper = MagicMock()
        scraper.scrape_sources.side_effect = RuntimeError("error")
        index_manager = MagicMock()

        svc = _make_service(scraper=scraper, index_manager=index_manager)
        svc.full_rebuild(sources=[_make_source()])

        index_manager.promote.assert_not_called()

    def test_fallido_run_calls_abort(self):
        scraper = MagicMock()
        scraper.scrape_sources.side_effect = RuntimeError("error")
        index_manager = MagicMock()

        svc = _make_service(scraper=scraper, index_manager=index_manager)
        svc.full_rebuild(sources=[_make_source()])

        index_manager.abort.assert_called_once()


class TestIndexarContenidoIncremental:
    def test_incremental_only_processes_selected_sources(self):
        scraper = MagicMock()
        scraper.scrape_sources.return_value = ([], [])
        index_loader = MagicMock()
        index_loader.load.return_value = 0
        index_manager = MagicMock()

        sources = [_make_source("s1"), _make_source("s2"), _make_source("s3")]
        selected_ids = ["s1"]

        svc = _make_service(scraper=scraper, index_loader=index_loader, index_manager=index_manager)
        from rag.domain.enums import ModoActualizacion
        svc.incremental_update(sources=sources, selected_source_ids=selected_ids)

        call_args = scraper.scrape_sources.call_args
        passed_sources = call_args.args[0] if call_args.args else call_args.kwargs.get("sources", [])
        assert all(s.id in selected_ids for s in passed_sources)
