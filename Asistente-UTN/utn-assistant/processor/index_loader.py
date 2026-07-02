"""
processor/index_loader.py — Converts ExtractedDocument records into
ContentFragment records and passes them to the IndexManager staging buffer.

Traceability: T040, FR-013, FR-015, FR-017.
"""
from __future__ import annotations

import hashlib
import logging

from rag.domain.fragments import ContentFragment, FragmentMetadata
from rag.domain.indexing import IndexUpdateRun
from rag.domain.sources import ExtractedDocument
from processor.chunker import Chunker
from processor.embeddings import EmbeddingsAdapter
from vectorstore.index_manager import IndexManager

logger = logging.getLogger(__name__)


class IndexLoader:
    """Converts extracted documents into indexed fragments via staging.

    Parameters
    ----------
    chunker:
        Configured Chunker instance.
    embeddings:
        Configured EmbeddingsAdapter instance.
    index_manager:
        IndexManager coordinating the staging/swap lifecycle.
    """

    def __init__(
        self,
        chunker: Chunker,
        embeddings: EmbeddingsAdapter,
        index_manager: IndexManager,
    ) -> None:
        self._chunker = chunker
        self._embeddings = embeddings
        self._index_manager = index_manager

    def load(
        self,
        run: IndexUpdateRun,
        documents: list[ExtractedDocument],
    ) -> int:
        """Convert documents to fragments, embed them, and stage for promotion.

        Returns the total number of fragments staged.
        """
        total_staged = 0

        for doc in documents:
            if not doc.is_usable():
                logger.debug("Skipping unusable document %s", doc.id)
                continue

            chunks = self._chunker.split(doc.clean_text)
            if not chunks:
                logger.debug("No chunks produced for document %s", doc.id)
                continue

            texts = chunks
            try:
                vectors = self._embeddings.encode(texts)
            except Exception as exc:
                logger.warning("Embedding failed for document %s: %s", doc.id, exc)
                run.record_failure(source_id=doc.source_id, url=doc.url, reason=str(exc))
                continue

            fragments_with_embeddings = []
            for (chunk_index, chunk_text), embedding in zip(
                enumerate(texts), vectors
            ):
                fragment_id = _stable_fragment_id(doc.url, chunk_index)
                meta = FragmentMetadata(
                    url=doc.url,
                    title=doc.title,
                    area=doc.area,
                    regional=doc.regional,
                    department=doc.department,
                    source_type=doc.source_type,
                    extraction_date=doc.extracted_at,
                )
                fragment = ContentFragment(
                    id=fragment_id,
                    document_id=doc.id,
                    text=chunk_text,
                    chunk_index=chunk_index,
                    embedding_model=self._embeddings._model_name,
                    metadata=meta,
                )
                fragments_with_embeddings.append((fragment, embedding))

            self._index_manager.stage_batch(run, fragments_with_embeddings)
            total_staged += len(fragments_with_embeddings)
            run.fragments_indexed += len(fragments_with_embeddings)
            run.documents_indexed += 1

        logger.info("IndexLoader staged %d fragments from %d documents.", total_staged, len(documents))
        return total_staged


def _stable_fragment_id(url: str, chunk_index: int) -> str:
    """Derive a stable, deterministic fragment ID from URL + chunk index."""
    raw = f"{url}::{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
