# tests/conftest.py
"""
T078 — Root pytest configuration with shared fixtures.

Provides:
  - tmp_chroma_dir / chroma_repo  — real ChromaDB in a temp dir
  - fake_sources                  — sample InstitutionalSource fixtures
  - fake_extracted_doc            — sample ExtractedDocument fixture
  - mock_llm_client               — mocked OllamaClient
  - test_settings                 — settings with temp paths and fast defaults
  - responder_service             — ResponderConsultaService wired with temp ChromaDB

Traceability: T078, plan.md §Testing.
"""
import sys
from pathlib import Path

# Ensure the project root is importable
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Settings override
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_settings(tmp_path):
    """Settings pointing to a temporary directory for ChromaDB."""
    from config.settings import Settings
    return Settings(
        chromadb_path=tmp_path / "chromadb",
        sources_config_path=tmp_path / "sources.yaml",
        ollama_base_url="http://localhost:11434/v1",
        llm_model="test-llm",
        embedding_model="test-embedding",
        relevance_threshold=0.65,
        top_k=5,
        chunk_size=200,
        chunk_overlap=20,
        request_delay_seconds=0.0,
        source_fetch_timeout_seconds=5.0,
        generation_timeout_seconds=5.0,
    )


# ---------------------------------------------------------------------------
# ChromaDB fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_chroma_dir(tmp_path):
    """Temporary directory for ChromaDB persistence."""
    return tmp_path / "chromadb"


@pytest.fixture()
def chroma_repo(tmp_chroma_dir):
    """Real ChromaDB repository backed by a temporary directory."""
    from vectorstore.chroma_repository import ChromaRepository
    return ChromaRepository(persist_directory=str(tmp_chroma_dir))


@pytest.fixture()
def index_manager(chroma_repo):
    """IndexManager backed by the temporary ChromaDB repo."""
    from vectorstore.index_manager import IndexManager
    return IndexManager(repository=chroma_repo)


# ---------------------------------------------------------------------------
# Domain fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_sources():
    """Two active InstitutionalSource fixtures across two areas."""
    from rag.domain.sources import InstitutionalSource
    from rag.domain.enums import AreaInstitucional, TipoFuente
    return [
        InstitutionalSource(
            id="src-academica",
            url="https://utn.edu.ar/academica",
            area=AreaInstitucional.ACADEMICA,
            source_type=TipoFuente.WEB,
            active=True,
        ),
        InstitutionalSource(
            id="src-bienestar",
            url="https://utn.edu.ar/bienestar",
            area=AreaInstitucional.BIENESTAR,
            source_type=TipoFuente.WEB,
            active=True,
        ),
    ]


@pytest.fixture()
def fake_extracted_doc():
    """One ExtractedDocument fixture with useful clean text."""
    from rag.domain.sources import ExtractedDocument
    from rag.domain.enums import AreaInstitucional, TipoFuente, EstadoIndexacion
    return ExtractedDocument(
        id="doc-001",
        source_id="src-academica",
        url="https://utn.edu.ar/academica/inscripciones",
        title="Inscripciones - UTN",
        raw_text="Las inscripciones para el primer cuatrimestre abren el 1 de febrero.",
        clean_text="Las inscripciones para el primer cuatrimestre abren el 1 de febrero.",
        area=AreaInstitucional.ACADEMICA,
        source_type=TipoFuente.WEB,
        status=EstadoIndexacion.COMPLETADO,
        extracted_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Mocked LLM client
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_llm_client():
    """OllamaClient mock that returns a canned answer."""
    client = MagicMock()
    client.generate.return_value = "Las inscripciones son en febrero."
    client.is_available.return_value = True
    return client


# ---------------------------------------------------------------------------
# Pre-seeded ChromaDB with one fragment (for query tests)
# ---------------------------------------------------------------------------

@pytest.fixture()
def seeded_chroma_repo(chroma_repo):
    """ChromaDB repo pre-populated with one ACADEMICA fragment."""
    from rag.domain.fragments import ContentFragment, FragmentMetadata
    from rag.domain.enums import AreaInstitucional, TipoFuente
    frag = ContentFragment(
        id="frag-001",
        document_id="doc-001",
        text="Las inscripciones para el primer cuatrimestre abren el 1 de febrero.",
        chunk_index=0,
        embedding_model="test-embedding",
        metadata=FragmentMetadata(
            url="https://utn.edu.ar/academica/inscripciones",
            title="Inscripciones - UTN",
            area=AreaInstitucional.ACADEMICA,
            source_type=TipoFuente.WEB,
        ),
    )
    # Use a deterministic embedding vector
    embedding = [0.5] * 384
    chroma_repo.upsert_fragments([(frag, embedding)])
    return chroma_repo


# ---------------------------------------------------------------------------
# Wired ResponderConsultaService (real ChromaDB + mocked LLM)
# ---------------------------------------------------------------------------

@pytest.fixture()
def responder_service(seeded_chroma_repo, mock_llm_client):
    """ResponderConsultaService with real ChromaDB and mocked LLM."""
    from rag.services.responder_consulta import ResponderConsultaService
    from rag.prompting import PromptBuilder

    return ResponderConsultaService(
        repository=seeded_chroma_repo,
        llm_client=mock_llm_client,
        prompt_builder=PromptBuilder(),
        relevance_threshold=0.0,   # accept any score in tests
        top_k=5,
        embeddings_adapter=None,   # will use dummy embedding [0]*384
    )
