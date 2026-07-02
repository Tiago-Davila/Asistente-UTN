"""
vectorstore/chroma_repository.py — ChromaDB PersistentClient adapter.

Implements VectorStoreRepository using one persistent ChromaDB collection
with metadata filters for area, regional, department, and source_type.

Design decisions:
  - One collection per installation (research.md §ChromaDB Collection Strategy).
  - Metadata filter applied at query time, not via separate collections.
  - Fragment IDs from the domain model are used as ChromaDB document IDs
    to ensure idempotent upserts.
  - ChromaDB's cosine distance is converted to a similarity score (1 - distance).

Traceability: T027, FR-003, FR-009, FR-013, FR-018, FR-019.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from rag.domain.enums import AreaInstitucional
from rag.domain.fragments import ContentFragment, SearchResult
from rag.domain.indexing import IndexStatus
from vectorstore.repository import VectorStoreRepository

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "utn_institutional"


class ChromaRepository(VectorStoreRepository):
    """ChromaDB PersistentClient-backed vector store.

    Parameters
    ----------
    persist_directory:
        Filesystem path where ChromaDB persists data.  Passed directly to
        chromadb.PersistentClient.
    collection_name:
        ChromaDB collection name (default ``utn_institutional``).
    """

    def __init__(
        self,
        persist_directory: str,
        collection_name: str = _COLLECTION_NAME,
    ) -> None:
        import chromadb  # local import — keeps ChromaDB inside vectorstore/

        self._persist_directory = persist_directory
        self._collection_name = collection_name
        self._client = chromadb.PersistentClient(path=persist_directory)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.debug(
            "ChromaRepository initialised: path=%s collection=%s",
            persist_directory,
            collection_name,
        )

    # ------------------------------------------------------------------
    # VectorStoreRepository implementation
    # ------------------------------------------------------------------

    def upsert_fragments(
        self,
        fragments_with_embeddings: list[tuple[ContentFragment, list[float]]],
    ) -> None:
        """Batch-upsert fragments into the ChromaDB collection."""
        if not fragments_with_embeddings:
            return

        ids: list[str] = []
        embeddings: list[list[float]] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for fragment, embedding in fragments_with_embeddings:
            ids.append(fragment.id)
            embeddings.append(embedding)
            documents.append(fragment.text)
            metadatas.append(self._fragment_to_metadata(fragment))

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.debug("Upserted %d fragments.", len(ids))

    def query_fragments(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        area_filter: Optional[AreaInstitucional] = None,
    ) -> list[SearchResult]:
        """Query the collection and return ordered SearchResult objects."""
        where: Optional[dict[str, Any]] = None
        if area_filter is not None:
            where = {"area": area_filter.value}

        try:
            response = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, max(self._collection.count(), 1)),
                where=where,
                include=["distances", "metadatas", "documents"],
            )
        except Exception as exc:
            logger.warning("ChromaDB query failed: %s", exc)
            return []

        results: list[SearchResult] = []
        ids = response.get("ids", [[]])[0]
        distances = response.get("distances", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]

        for rank, (fid, dist, meta) in enumerate(
            zip(ids, distances, metadatas), start=1
        ):
            score = min(1.0, max(0.0, 1.0 - dist))  # cosine distance → similarity (clamped)
            results.append(
                SearchResult(
                    fragment_id=fid,
                    score=round(score, 6),
                    rank=rank,
                    metadata=meta or {},
                )
            )

        return results

    def delete_collection(self) -> None:
        """Delete and recreate the collection, removing all fragments."""
        self._client.delete_collection(self._collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Collection '%s' deleted and recreated.", self._collection_name)

    def get_status(self) -> IndexStatus:
        """Return a lightweight status snapshot."""
        from vectorstore.status import build_index_status
        return build_index_status(self._collection)

    def is_healthy(self) -> bool:
        """Return True when the ChromaDB client can be reached."""
        try:
            self._client.heartbeat()
            return True
        except Exception as exc:
            logger.warning("ChromaDB health check failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fragment_to_metadata(fragment: ContentFragment) -> dict[str, Any]:
        """Flatten fragment metadata into a ChromaDB-compatible dict.

        ChromaDB metadata values must be str, int, float, or bool.
        datetime objects are serialised to ISO 8601 strings.
        None values are omitted because ChromaDB does not support null metadata.
        """
        m = fragment.metadata
        raw: dict[str, Any] = {
            "url": m.url,
            "area": m.area.value,
            "source_type": m.source_type.value,
        }
        if m.title is not None:
            raw["title"] = m.title
        if m.regional is not None:
            raw["regional"] = m.regional
        if m.department is not None:
            raw["department"] = m.department
        if m.extraction_date is not None:
            raw["extraction_date"] = m.extraction_date.isoformat()
        raw["indexed_at"] = m.indexed_at.isoformat()
        raw["document_id"] = fragment.document_id
        raw["chunk_index"] = fragment.chunk_index
        raw["embedding_model"] = fragment.embedding_model
        return raw
