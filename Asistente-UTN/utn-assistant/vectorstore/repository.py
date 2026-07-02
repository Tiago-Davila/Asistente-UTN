"""
vectorstore/repository.py — Abstract ChromaDB repository interface.

Defines the contract that ChromaRepository (T027) must satisfy.
No ChromaDB imports here — this is a pure abstract interface so that
application services and tests can depend on the abstraction, not the
concrete adapter.

Traceability:
  upsert_fragments  → FR-013, FR-015 (index loading)
  query_fragments   → FR-003, FR-006, FR-009 (retrieval with optional area filter)
  delete_collection → FR-019 (full rebuild support)
  get_status        → FR-018, data-model.md §IndexStatus
  is_healthy        → FR-021, US5

tasks.md: "Keep ChromaDB access inside vectorstore/; no other module imports
           ChromaDB directly."
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from rag.domain.enums import AreaInstitucional
from rag.domain.fragments import ContentFragment, SearchResult
from rag.domain.indexing import IndexStatus


class VectorStoreRepository(ABC):
    """Abstract interface for the vector persistence layer.

    Concrete implementations (ChromaRepository) live in chroma_repository.py.
    Tests may use this interface to build fakes without importing ChromaDB.
    """

    @abstractmethod
    def upsert_fragments(
        self,
        fragments_with_embeddings: list[tuple[ContentFragment, list[float]]],
    ) -> None:
        """Insert or update a batch of fragments with their pre-computed embeddings.

        Callers provide the embedding vector alongside each fragment so that this
        layer remains decoupled from the embedding model (T039 owns that).
        """

    @abstractmethod
    def query_fragments(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        area_filter: Optional[AreaInstitucional] = None,
    ) -> list[SearchResult]:
        """Return the top-k most similar fragments to the query embedding.

        When area_filter is given, only fragments whose metadata.area matches
        are considered (research.md §ChromaDB Collection Strategy).

        Results are returned ordered by descending similarity score.
        """

    @abstractmethod
    def delete_collection(self) -> None:
        """Delete all fragments from the collection.

        Used by the full-rebuild flow before staging new fragments (FR-019).
        The caller is responsible for ensuring the previous index is preserved
        via the IndexManager staging/swap strategy before calling this.
        """

    @abstractmethod
    def get_status(self) -> IndexStatus:
        """Return a lightweight status snapshot without exposing raw storage.

        Must be fast enough to meet the ≤1-second index status target (SC-004).
        """

    @abstractmethod
    def is_healthy(self) -> bool:
        """Return True if the vector store is reachable and operational (FR-021)."""
