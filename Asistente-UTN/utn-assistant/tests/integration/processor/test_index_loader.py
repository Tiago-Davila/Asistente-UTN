"""
T069 — Processor integration tests: ExtractedDocument → fragments → staged vectorstore.

Uses real Chunker, mocked EmbeddingsAdapter, and real IndexManager/ChromaRepo
backed by a temporary directory.
FR-013: fragment metadata flows from document.
FR-015: staging/swap lifecycle.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
import numpy as np


@pytest.fixture()
def mock_embeddings():
    adapter = MagicMock()
    adapter._model_name = "test-embed"
    adapter.encode.side_effect = lambda texts: [[0.1] * 384 for _ in texts]
    return adapter


@pytest.fixture()
def index_loader(index_manager, mock_embeddings):
    from processor.chunker import Chunker
    from processor.index_loader import IndexLoader
    chunker = Chunker(chunk_size=100, chunk_overlap=20)
    return IndexLoader(chunker=chunker, embeddings=mock_embeddings, index_manager=index_manager)


def _make_run():
    from rag.domain.indexing import IndexUpdateRun
    from rag.domain.enums import ModoActualizacion
    run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
    run.start()
    return run


class TestIndexLoaderIntegration:
    def test_document_produces_at_least_one_fragment(self, index_loader, index_manager, fake_extracted_doc, chroma_repo):
        run = _make_run()
        index_manager.begin_staging(run)
        count = index_loader.load(run=run, documents=[fake_extracted_doc])
        assert count >= 1

    def test_fragment_staged_not_yet_in_active_repo(self, index_loader, index_manager, fake_extracted_doc, chroma_repo):
        run = _make_run()
        index_manager.begin_staging(run)
        index_loader.load(run=run, documents=[fake_extracted_doc])
        # Not promoted yet — active repo should be empty
        status = chroma_repo.get_status()
        assert status.fragment_count == 0

    def test_promote_after_complete_writes_to_repo(self, index_loader, index_manager, fake_extracted_doc, chroma_repo):
        run = _make_run()
        index_manager.begin_staging(run)
        index_loader.load(run=run, documents=[fake_extracted_doc])
        run.complete(
            documents_indexed=run.documents_indexed,
            documents_failed=run.documents_failed,
            fragments_indexed=run.fragments_indexed,
        )
        index_manager.promote(run)
        status = chroma_repo.get_status()
        assert status.fragment_count >= 1

    def test_fragment_metadata_preserves_url(self, index_loader, index_manager, fake_extracted_doc, chroma_repo):
        run = _make_run()
        index_manager.begin_staging(run)
        index_loader.load(run=run, documents=[fake_extracted_doc])
        run.complete(documents_indexed=1, documents_failed=0, fragments_indexed=run.fragments_indexed)
        index_manager.promote(run)
        results = chroma_repo.query_fragments(query_embedding=[0.1] * 384, top_k=5)
        assert any(r.metadata.get("url") == fake_extracted_doc.url for r in results)

    def test_unusable_document_skipped(self, index_loader, index_manager, chroma_repo):
        from rag.domain.sources import ExtractedDocument
        from rag.domain.enums import AreaInstitucional, TipoFuente, EstadoIndexacion
        bad_doc = ExtractedDocument(
            id="bad-doc",
            source_id="src",
            url="https://utn.edu.ar/bad",
            clean_text="",   # empty → unusable
            area=AreaInstitucional.ACADEMICA,
            source_type=TipoFuente.WEB,
        )
        run = _make_run()
        index_manager.begin_staging(run)
        count = index_loader.load(run=run, documents=[bad_doc])
        assert count == 0

    def test_documents_indexed_count_updated(self, index_loader, index_manager, fake_extracted_doc):
        run = _make_run()
        index_manager.begin_staging(run)
        index_loader.load(run=run, documents=[fake_extracted_doc])
        assert run.documents_indexed >= 1
