"""
T074 — Area filter integration tests.

Filtered queries must return only fragments from the selected area.
No filter searches all indexed content (FR-009, FR-010, US6).
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def two_area_repo(chroma_repo):
    """ChromaDB seeded with fragments in two areas."""
    from rag.domain.fragments import ContentFragment, FragmentMetadata
    from rag.domain.enums import AreaInstitucional, TipoFuente

    frags = [
        ContentFragment(
            id="frag-academica",
            document_id="doc-a",
            text="Información sobre inscripciones académicas.",
            chunk_index=0,
            embedding_model="test",
            metadata=FragmentMetadata(
                url="https://utn.edu.ar/academica",
                title="Académica",
                area=AreaInstitucional.ACADEMICA,
                source_type=TipoFuente.WEB,
            ),
        ),
        ContentFragment(
            id="frag-bienestar",
            document_id="doc-b",
            text="Información sobre servicios de bienestar estudiantil.",
            chunk_index=0,
            embedding_model="test",
            metadata=FragmentMetadata(
                url="https://utn.edu.ar/bienestar",
                title="Bienestar",
                area=AreaInstitucional.BIENESTAR,
                source_type=TipoFuente.WEB,
            ),
        ),
    ]
    chroma_repo.upsert_fragments([(f, [0.5] * 384) for f in frags])
    return chroma_repo


@pytest.fixture()
def area_service(two_area_repo, mock_llm_client):
    from rag.services.responder_consulta import ResponderConsultaService
    from rag.prompting import PromptBuilder
    mock_llm_client.generate.return_value = "Respuesta."
    return ResponderConsultaService(
        repository=two_area_repo,
        llm_client=mock_llm_client,
        prompt_builder=PromptBuilder(),
        relevance_threshold=0.0,
        top_k=10,
    )


class TestAreaFilterIntegration:
    def test_no_filter_returns_both_areas(self, two_area_repo):
        results = two_area_repo.query_fragments(
            query_embedding=[0.5] * 384, top_k=10, area_filter=None
        )
        areas = {r.metadata.get("area") for r in results}
        assert "ACADEMICA" in areas
        assert "BIENESTAR" in areas

    def test_academica_filter_returns_only_academica(self, two_area_repo):
        from rag.domain.enums import AreaInstitucional
        results = two_area_repo.query_fragments(
            query_embedding=[0.5] * 384, top_k=10, area_filter=AreaInstitucional.ACADEMICA
        )
        assert len(results) >= 1
        assert all(r.metadata.get("area") == "ACADEMICA" for r in results)
        assert all(r.metadata.get("area") != "BIENESTAR" for r in results)

    def test_bienestar_filter_returns_only_bienestar(self, two_area_repo):
        from rag.domain.enums import AreaInstitucional
        results = two_area_repo.query_fragments(
            query_embedding=[0.5] * 384, top_k=10, area_filter=AreaInstitucional.BIENESTAR
        )
        assert len(results) >= 1
        assert all(r.metadata.get("area") == "BIENESTAR" for r in results)

    def test_area_filter_in_service_answer(self, area_service):
        from rag.domain.queries import UserQuery
        from rag.domain.enums import AreaInstitucional
        answer = area_service.answer(
            UserQuery(question="consulta?", area_filter=AreaInstitucional.ACADEMICA)
        )
        if answer.context_sufficient:
            for src in answer.sources:
                assert src.area == AreaInstitucional.ACADEMICA

    def test_insufficient_area_content_returns_refusal(self, area_service):
        from rag.domain.queries import UserQuery
        from rag.domain.enums import AreaInstitucional
        # EXTENSION area has no fragments — should return refusal
        answer = area_service.answer(
            UserQuery(question="consulta?", area_filter=AreaInstitucional.EXTENSION)
        )
        assert answer.context_sufficient is False
