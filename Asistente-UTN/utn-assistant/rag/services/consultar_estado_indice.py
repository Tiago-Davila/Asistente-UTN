"""
rag/services/consultar_estado_indice.py — Index status service.

Provides the current state of the searchable corpus to the API layer
without exposing raw vectorstore internals (FR-018, US7).

Traceability: T051.
"""
from __future__ import annotations

import logging

from rag.domain.indexing import IndexStatus
from vectorstore.repository import VectorStoreRepository

logger = logging.getLogger(__name__)


class ConsultarEstadoIndiceService:
    """Returns current index status from the vector store.

    Parameters
    ----------
    repository:
        VectorStoreRepository; get_status() must return in under 1 second
        (SC-004 index status target).
    """

    def __init__(self, repository: VectorStoreRepository) -> None:
        self._repository = repository

    def get_status(self) -> IndexStatus:
        """Return the current IndexStatus snapshot.

        Never raises — returns a not-ready status on any error so the API
        can still respond (FR-021).
        """
        try:
            return self._repository.get_status()
        except Exception as exc:
            logger.error("Failed to retrieve index status: %s", exc)
            return IndexStatus(
                ready=False,
                error_detail=str(exc),  # type: ignore[call-arg]
            )
