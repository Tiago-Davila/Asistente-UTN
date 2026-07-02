"""
rag/services/health.py — Dependency health service.

Checks availability of ChromaDB, Ollama, and index readiness (FR-021, US5).
Returns a structured result that the API health router can expose without
leaking internal details.

Traceability: T052.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from rag.services.llm_client import OllamaClient
from vectorstore.repository import VectorStoreRepository

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status for all required local services."""
    chromadb_healthy: bool = False
    ollama_healthy: bool = False
    index_ready: bool = False
    details: dict = field(default_factory=dict)

    @property
    def overall_healthy(self) -> bool:
        return self.chromadb_healthy and self.ollama_healthy and self.index_ready


class HealthService:
    """Checks ChromaDB, Ollama, and index readiness.

    Parameters
    ----------
    repository:
        VectorStoreRepository; is_healthy() and get_status() are called.
    llm_client:
        OllamaClient; is_available() is called.
    """

    def __init__(
        self,
        repository: VectorStoreRepository,
        llm_client: OllamaClient,
    ) -> None:
        self._repository = repository
        self._llm = llm_client

    def check(self) -> HealthStatus:
        """Return a HealthStatus without raising."""
        status = HealthStatus()

        # ChromaDB
        try:
            status.chromadb_healthy = self._repository.is_healthy()
        except Exception as exc:
            logger.warning("ChromaDB health check failed: %s", exc)
            status.chromadb_healthy = False

        # Ollama
        try:
            status.ollama_healthy = self._llm.is_available()
        except Exception as exc:
            logger.warning("Ollama health check failed: %s", exc)
            status.ollama_healthy = False

        # Index readiness
        try:
            index_status = self._repository.get_status()
            status.index_ready = index_status.ready
        except Exception as exc:
            logger.warning("Index status check failed: %s", exc)
            status.index_ready = False

        return status
