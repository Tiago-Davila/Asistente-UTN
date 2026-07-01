"""
vectorstore/index_manager.py — Staging and promotion coordinator.

Implements the staging-and-swap update strategy described in
research.md §Index Update Safety:

  1. begin_staging(run)    — open a staging buffer for this run.
  2. stage_fragment(...)   — accumulate fragments in memory; do NOT write to
                             the active collection yet.
  3. promote(run)          — called after run.complete(); flushes staged
                             fragments to the repository and marks run.promoted.
  4. abort(run)            — called after run.fail(); discards staged fragments;
                             the active collection is untouched (FR-016).

The manager holds staged fragments in memory during the run.  For very large
corpora the caller (IndexarContenidoService, T050) should flush in batches via
the batch-upsert path, but the coordinator always validates promotion eligibility
before writing.

Traceability: T028, FR-015, FR-016, data-model.md §EstadoIndexacion.
"""
from __future__ import annotations

import logging
from typing import Optional

from rag.domain.enums import EstadoIndexacion
from rag.domain.fragments import ContentFragment
from rag.domain.indexing import IndexUpdateRun
from rag.domain.rules import can_promote
from vectorstore.repository import VectorStoreRepository

logger = logging.getLogger(__name__)


class IndexManager:
    """Coordinates the staging-and-swap lifecycle for index update runs.

    Parameters
    ----------
    repository:
        The VectorStoreRepository instance used for all persistence operations.
    """

    def __init__(self, repository: VectorStoreRepository) -> None:
        self._repository = repository
        # run_id → list of (fragment, embedding) staged for that run
        self._staging: dict[str, list[tuple[ContentFragment, list[float]]]] = {}

    # ------------------------------------------------------------------
    # Lifecycle methods
    # ------------------------------------------------------------------

    def begin_staging(self, run: IndexUpdateRun) -> None:
        """Open a staging buffer for the given run.

        Must be called after run.start() while run.status is EN_PROCESO.
        """
        if run.status != EstadoIndexacion.EN_PROCESO:
            raise ValueError(
                f"Cannot begin staging for a run in state {run.status}; "
                "expected EN_PROCESO"
            )
        self._staging[run.id] = []
        logger.debug("Staging opened for run %s.", run.id)

    def stage_fragment(
        self,
        run: IndexUpdateRun,
        fragment: ContentFragment,
        embedding: list[float],
    ) -> None:
        """Accumulate a fragment in the staging buffer.

        The active collection is NOT modified until promote() is called.
        """
        if run.id not in self._staging:
            raise KeyError(
                f"No staging buffer for run {run.id}. Call begin_staging() first."
            )
        self._staging[run.id].append((fragment, embedding))

    def promote(self, run: IndexUpdateRun) -> None:
        """Flush staged fragments to the repository and mark the run promoted.

        Raises ValueError if the run is not eligible for promotion (FR-016).
        """
        if not can_promote(run):
            raise ValueError(
                f"Run {run.id} cannot be promoted (status={run.status}). "
                "Only COMPLETADO runs may promote their index."
            )

        staged = self._staging.pop(run.id, [])
        if staged:
            self._repository.upsert_fragments(staged)
            logger.info(
                "Promoted %d fragments from run %s to active index.",
                len(staged),
                run.id,
            )
        else:
            logger.info("Run %s promoted with 0 staged fragments.", run.id)

        run.promoted = True

    def abort(self, run: IndexUpdateRun) -> None:
        """Discard staged fragments; the active collection remains untouched.

        Called when run.status is FALLIDO.  Preserves the previous usable
        index (FR-016).
        """
        discarded = self._staging.pop(run.id, [])
        logger.info(
            "Aborted run %s; discarded %d staged fragments. "
            "Active index is preserved.",
            run.id,
            len(discarded),
        )

    # ------------------------------------------------------------------
    # Convenience: batch staging for large documents
    # ------------------------------------------------------------------

    def stage_batch(
        self,
        run: IndexUpdateRun,
        fragments_with_embeddings: list[tuple[ContentFragment, list[float]]],
    ) -> None:
        """Stage multiple fragments in one call."""
        for fragment, embedding in fragments_with_embeddings:
            self.stage_fragment(run, fragment, embedding)

    def staged_count(self, run: IndexUpdateRun) -> int:
        """Return the number of fragments currently staged for the run."""
        return len(self._staging.get(run.id, []))
