"""
rag/services/indexar_contenido.py — Index update orchestration service.

Implements US4 (administrator-triggered indexing).

Supports full rebuild and incremental selected-source updates (FR-015).
Preserves the previous usable index when a run fails (FR-016).
Reports indexed and failed counts at the end of every run (FR-017).
Continues when individual sources fail (FR-014).

Traceability: T050.
"""
from __future__ import annotations

import logging

from rag.domain.enums import EstadoIndexacion, ModoActualizacion
from rag.domain.indexing import IndexUpdateRun
from rag.domain.sources import InstitutionalSource
from processor.index_loader import IndexLoader
from scraper.run import Scraper
from vectorstore.index_manager import IndexManager
from vectorstore.repository import VectorStoreRepository

logger = logging.getLogger(__name__)


class IndexarContenidoService:
    """Orchestrates source scraping → fragment loading → index promotion.

    Parameters
    ----------
    scraper:
        Scraper instance for fetching and extracting pages.
    index_loader:
        IndexLoader for converting documents to fragments and staging them.
    index_manager:
        IndexManager for the staging/swap lifecycle.
    repository:
        VectorStoreRepository (used for pre-run cleanup on full rebuild).
    """

    def __init__(
        self,
        scraper: Scraper,
        index_loader: IndexLoader,
        index_manager: IndexManager,
        repository: VectorStoreRepository,
    ) -> None:
        self._scraper = scraper
        self._index_loader = index_loader
        self._index_manager = index_manager
        self._repository = repository

    def full_rebuild(
        self, sources: list[InstitutionalSource]
    ) -> IndexUpdateRun:
        """Re-index all provided sources from scratch.

        On success, promotes the new index.
        On failure, preserves the previous usable index (FR-016).
        """
        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        run.start()
        self._index_manager.begin_staging(run)

        try:
            documents, failures = self._scraper.scrape_sources(sources)
        except Exception as exc:
            logger.error("Scraper raised an unexpected error: %s", exc)
            run.fail(reason=str(exc))
            self._index_manager.abort(run)
            return run

        # Record source failures (FR-014, FR-017)
        for source_id, reason in failures:
            run.record_failure(source_id=source_id, url=None, reason=reason)

        # Load documents into staging
        try:
            self._index_loader.load(run=run, documents=documents)
        except Exception as exc:
            logger.error("Index loader raised an unexpected error: %s", exc)
            run.fail(reason=str(exc))
            self._index_manager.abort(run)
            return run

        run.complete(
            documents_indexed=run.documents_indexed,
            documents_failed=run.documents_failed,
            fragments_indexed=run.fragments_indexed,
        )
        self._index_manager.promote(run)
        logger.info(
            "Full rebuild complete: %d indexed, %d failed.",
            run.documents_indexed, run.documents_failed,
        )
        return run

    def incremental_update(
        self,
        sources: list[InstitutionalSource],
        selected_source_ids: list[str],
    ) -> IndexUpdateRun:
        """Re-index only the administrator-selected subset of sources (FR-015)."""
        selected = [s for s in sources if s.id in selected_source_ids]
        run = IndexUpdateRun(
            mode=ModoActualizacion.INCREMENTAL_SELECTED_SOURCES,
            selected_source_ids=selected_source_ids,
        )
        run.start()
        self._index_manager.begin_staging(run)

        try:
            documents, failures = self._scraper.scrape_sources(selected)
        except Exception as exc:
            logger.error("Scraper raised an unexpected error: %s", exc)
            run.fail(reason=str(exc))
            self._index_manager.abort(run)
            return run

        for source_id, reason in failures:
            run.record_failure(source_id=source_id, url=None, reason=reason)

        try:
            self._index_loader.load(run=run, documents=documents)
        except Exception as exc:
            logger.error("Index loader raised an unexpected error: %s", exc)
            run.fail(reason=str(exc))
            self._index_manager.abort(run)
            return run

        run.complete(
            documents_indexed=run.documents_indexed,
            documents_failed=run.documents_failed,
            fragments_indexed=run.fragments_indexed,
        )
        self._index_manager.promote(run)
        return run
