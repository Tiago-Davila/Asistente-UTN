"""
T024 — Integration tests for ChromaDB insert/search/metadata filtering.

These tests use a real ChromaDB PersistentClient in a temporary directory.
They require chromadb to be installed.  They are expected to FAIL until
T026 + T027 are implemented.

plan.md §Testing: ChromaDB PersistentClient test fixture in a temporary directory.
research.md §ChromaDB Collection Strategy: one collection, metadata filters.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_chroma_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for ChromaDB persistence."""
    return tmp_path / "chromadb"


@pytest.fixture()
def repo(tmp_chroma_dir: Path):
    """Provide a ChromaRepository backed by a temporary ChromaDB instance."""
    from vectorstore.chroma_repository import ChromaRepository
    return ChromaRepository(persist_directory=str(tmp_chroma_dir))


def _make_fragment(
    fragment_id: str,
    text: str,
    url: str,
    area: str = "ACADEMICA",
    regional: str | None = None,
) -> "ContentFragment":
    from rag.domain.fragments import ContentFragment, FragmentMetadata
    from rag.domain.enums import AreaInstitucional, TipoFuente
    return ContentFragment(
        id=fragment_id,
        document_id="doc1",
        text=text,
        chunk_index=0,
        embedding_model="test-model",
        metadata=FragmentMetadata(
            url=url,
            area=AreaInstitucional(area),
            source_type=TipoFuente.WEB,
            regional=regional,
        ),
    )


# ---------------------------------------------------------------------------
# Insert and retrieve
# ---------------------------------------------------------------------------

class TestChromaRepositoryInsertSearch:
    def test_upsert_and_query_returns_result(self, repo):
        frag = _make_fragment("f1", "Inscripciones UTN", "https://utn.edu.ar/inscripciones")
        embedding = [0.1] * 384
        repo.upsert_fragments([(frag, embedding)])

        results = repo.query_fragments(
            query_embedding=[0.1] * 384,
            top_k=1,
            area_filter=None,
        )
        assert len(results) >= 1
        assert results[0].fragment_id == "f1"

    def test_upsert_multiple_fragments(self, repo):
        frags = [
            (_make_fragment(f"f{i}", f"Texto {i}", f"https://utn.edu.ar/{i}"), [float(i) / 10] * 384)
            for i in range(5)
        ]
        repo.upsert_fragments(frags)
        results = repo.query_fragments(query_embedding=[0.0] * 384, top_k=10)
        assert len(results) == 5

    def test_upsert_is_idempotent(self, repo):
        frag = _make_fragment("f1", "Texto duplicado", "https://utn.edu.ar/dup")
        embedding = [0.5] * 384
        repo.upsert_fragments([(frag, embedding)])
        repo.upsert_fragments([(frag, embedding)])  # same id
        results = repo.query_fragments(query_embedding=[0.5] * 384, top_k=10)
        ids = [r.fragment_id for r in results]
        assert ids.count("f1") == 1


# ---------------------------------------------------------------------------
# Metadata filtering (research.md: area, regional, department, source_type)
# ---------------------------------------------------------------------------

class TestChromaRepositoryMetadataFiltering:
    def test_area_filter_returns_only_matching_fragments(self, repo):
        from rag.domain.enums import AreaInstitucional
        frags = [
            (_make_fragment("fa", "Academica", "https://utn.edu.ar/a", area="ACADEMICA"), [0.1] * 384),
            (_make_fragment("fb", "Bienestar", "https://utn.edu.ar/b", area="BIENESTAR"), [0.2] * 384),
        ]
        repo.upsert_fragments(frags)

        results = repo.query_fragments(
            query_embedding=[0.1] * 384,
            top_k=10,
            area_filter=AreaInstitucional.ACADEMICA,
        )
        assert all(r.metadata.get("area") == "ACADEMICA" for r in results)
        assert all(r.fragment_id != "fb" for r in results)

    def test_no_area_filter_returns_all_areas(self, repo):
        frags = [
            (_make_fragment("fa", "Academica", "https://utn.edu.ar/a", area="ACADEMICA"), [0.1] * 384),
            (_make_fragment("fb", "Bienestar", "https://utn.edu.ar/b", area="BIENESTAR"), [0.2] * 384),
        ]
        repo.upsert_fragments(frags)
        results = repo.query_fragments(query_embedding=[0.15] * 384, top_k=10)
        assert {r.metadata.get("area") for r in results} == {"ACADEMICA", "BIENESTAR"}


# ---------------------------------------------------------------------------
# Delete collection
# ---------------------------------------------------------------------------

class TestChromaRepositoryDelete:
    def test_delete_collection_removes_all_fragments(self, repo):
        frag = _make_fragment("f1", "Texto", "https://utn.edu.ar/x")
        repo.upsert_fragments([(frag, [0.1] * 384)])
        repo.delete_collection()
        results = repo.query_fragments(query_embedding=[0.1] * 384, top_k=10)
        assert results == []


# ---------------------------------------------------------------------------
# Status and health
# ---------------------------------------------------------------------------

class TestChromaRepositoryStatus:
    def test_empty_repo_fragment_count_is_zero(self, repo):
        status = repo.get_status()
        assert status.fragment_count == 0

    def test_fragment_count_increases_after_upsert(self, repo):
        frag = _make_fragment("f1", "Texto", "https://utn.edu.ar/y")
        repo.upsert_fragments([(frag, [0.1] * 384)])
        status = repo.get_status()
        assert status.fragment_count >= 1

    def test_health_check_returns_true_when_available(self, repo):
        assert repo.is_healthy() is True
