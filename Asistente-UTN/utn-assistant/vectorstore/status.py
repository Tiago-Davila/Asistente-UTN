"""
vectorstore/status.py — Vectorstore health and IndexStatus mapper.

Builds the IndexStatus domain object from a live ChromaDB collection
without exposing raw ChromaDB internals to application services.

Traceability: T029, FR-018, data-model.md §IndexStatus.
"""
from __future__ import annotations

import logging
from typing import Any

from rag.domain.enums import AreaInstitucional
from rag.domain.indexing import IndexStatus

logger = logging.getLogger(__name__)


def build_index_status(collection: Any) -> IndexStatus:
    """Build an IndexStatus from a live ChromaDB Collection object.

    Parameters
    ----------
    collection:
        A chromadb Collection instance (type-hinted as Any to avoid
        importing chromadb at module level — only vectorstore/ imports it).

    Returns
    -------
    IndexStatus with:
        - fragment_count: total documents in the collection.
        - ready: True when fragment_count > 0.
        - covered_areas: distinct AreaInstitucional values in metadata.
        - document_count: distinct document_id values in metadata.
        - covered_regionales: distinct non-null regional values in metadata.
        - last_successful_update_at: None (managed by IndexManager, not here).
        - recent_failures: [] (managed by IndexUpdateRun, not here).
    """
    try:
        count = collection.count()
    except Exception as exc:
        logger.warning("Could not get collection count: %s", exc)
        return IndexStatus(ready=False)

    if count == 0:
        return IndexStatus(ready=False, fragment_count=0, document_count=0)

    # Fetch all metadata to compute covered areas and document count.
    # For large corpora this is acceptable because status is cached at the
    # service layer and not called per-query.
    try:
        data = collection.get(include=["metadatas"])
        metadatas: list[dict[str, Any]] = data.get("metadatas") or []
    except Exception as exc:
        logger.warning("Could not fetch metadata for status: %s", exc)
        # Return basic status without area breakdown
        return IndexStatus(ready=True, fragment_count=count)

    areas: set[AreaInstitucional] = set()
    doc_ids: set[str] = set()
    regionales: set[str] = set()

    for meta in metadatas:
        # area
        raw_area = meta.get("area")
        if raw_area:
            try:
                areas.add(AreaInstitucional(raw_area))
            except ValueError:
                pass
        # document_id
        doc_id = meta.get("document_id")
        if doc_id:
            doc_ids.add(doc_id)
        # regional
        regional = meta.get("regional")
        if regional:
            regionales.add(regional)

    return IndexStatus(
        ready=True,
        fragment_count=count,
        document_count=len(doc_ids),
        covered_areas=sorted(areas, key=lambda a: a.value),
        covered_regionales=sorted(regionales),
    )
