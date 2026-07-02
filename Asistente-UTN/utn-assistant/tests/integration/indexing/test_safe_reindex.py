"""
T073 — Safe re-indexing integration tests.

Failed update must not replace the previous usable index (FR-016).
Uses real IndexManager + ChromaDB temp dir.
"""
from __future__ import annotations

import pytest


def _make_full_run(index_manager, chroma_repo, documents):
    """Run a complete full-rebuild and return (run, fragments_in_repo_after)."""
    from rag.domain.indexing import IndexUpdateRun
    from rag.domain.enums import ModoActualizacion

    run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
    run.start()
    index_manager.begin_staging(run)

    # Stage documents via loader or directly
    for doc in documents:
        from rag.domain.fragments import ContentFragment, FragmentMetadata
        from rag.domain.enums import AreaInstitucional, TipoFuente

        for i, chunk in enumerate(doc.clean_text.split(".")):
            chunk = chunk.strip()
            if not chunk:
                continue
            frag = ContentFragment(
                id=f"{doc.id}-{i}",
                document_id=doc.id,
                text=chunk,
                chunk_index=i,
                embedding_model="test",
                metadata=FragmentMetadata(
                    url=doc.url,
                    title=doc.title,
                    area=doc.area,
                    source_type=doc.source_type,
                ),
            )
            index_manager.stage_fragment(run, frag, [0.5] * 384)

    run.complete(
        documents_indexed=len(documents),
        documents_failed=0,
        fragments_indexed=index_manager.staged_count(run),
    )
    index_manager.promote(run)
    return run


class TestSafeReindexing:
    def test_successful_run_populates_index(self, index_manager, chroma_repo, fake_extracted_doc):
        _make_full_run(index_manager, chroma_repo, [fake_extracted_doc])
        assert chroma_repo.get_status().fragment_count >= 1

    def test_failed_run_does_not_wipe_previous_index(self, index_manager, chroma_repo, fake_extracted_doc):
        # Build initial index
        _make_full_run(index_manager, chroma_repo, [fake_extracted_doc])
        initial_count = chroma_repo.get_status().fragment_count
        assert initial_count >= 1

        # Attempt a new run that fails mid-way
        from rag.domain.indexing import IndexUpdateRun
        from rag.domain.enums import ModoActualizacion

        failed_run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        failed_run.start()
        index_manager.begin_staging(failed_run)
        # Stage a fragment but then fail before promoting
        from rag.domain.fragments import ContentFragment, FragmentMetadata
        from rag.domain.enums import AreaInstitucional, TipoFuente
        frag = ContentFragment(
            id="new-frag", document_id="new-doc", text="Nuevo contenido",
            chunk_index=0, embedding_model="test",
            metadata=FragmentMetadata(url="https://utn.edu.ar/new", area=AreaInstitucional.ACADEMICA, source_type=TipoFuente.WEB),
        )
        index_manager.stage_fragment(failed_run, frag, [0.6] * 384)
        failed_run.fail(reason="simulated error")
        index_manager.abort(failed_run)

        # Previous index must still be intact
        after_count = chroma_repo.get_status().fragment_count
        assert after_count == initial_count

    def test_failed_run_is_not_promoted(self, index_manager, chroma_repo, fake_extracted_doc):
        from rag.domain.indexing import IndexUpdateRun
        from rag.domain.enums import ModoActualizacion

        run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        run.start()
        index_manager.begin_staging(run)
        run.fail(reason="error")
        index_manager.abort(run)
        assert run.promoted is False

    def test_queries_use_previous_index_after_failed_update(self, index_manager, chroma_repo, fake_extracted_doc, mock_llm_client):
        from rag.services.responder_consulta import ResponderConsultaService
        from rag.prompting import PromptBuilder
        from rag.domain.queries import UserQuery
        from rag.domain.indexing import IndexUpdateRun
        from rag.domain.enums import ModoActualizacion

        # Build initial good index
        _make_full_run(index_manager, chroma_repo, [fake_extracted_doc])

        # Fail a second run
        failed_run = IndexUpdateRun(mode=ModoActualizacion.FULL_REBUILD)
        failed_run.start()
        index_manager.begin_staging(failed_run)
        failed_run.fail(reason="network error")
        index_manager.abort(failed_run)

        # Service should still answer from the previous index
        mock_llm_client.generate.return_value = "Respuesta desde el indice anterior."
        svc = ResponderConsultaService(
            repository=chroma_repo,
            llm_client=mock_llm_client,
            prompt_builder=PromptBuilder(),
            relevance_threshold=0.0,
            top_k=5,
        )
        answer = svc.answer(UserQuery(question="inscripciones?"))
        assert answer.context_sufficient is True
