"""
api/dependencies.py — FastAPI dependency wiring.

Provides injectable instances of settings, vectorstore repository,
application services, and the admin operation guard.

All constructor dependencies are assembled once via lru_cache singletons.
Application code never constructs these directly — they arrive via
FastAPI's DI system.

Traceability: T059, tasks.md §Notes (keep routers thin).
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from config.settings import Settings, get_settings
from processor.chunker import Chunker
from processor.embeddings import EmbeddingsAdapter
from processor.index_loader import IndexLoader
from rag.prompting import PromptBuilder
from rag.services.health import HealthService
from rag.services.llm_client import OllamaClient
from rag.services.responder_consulta import ResponderConsultaService
from rag.services.consultar_estado_indice import ConsultarEstadoIndiceService
from rag.services.indexar_contenido import IndexarContenidoService
from scraper.client import ScraperClient
from scraper.extractor import HtmlExtractor
from scraper.robots import RobotsChecker
from scraper.run import Scraper
from processor.text_cleaner import TextCleaner
from vectorstore.chroma_repository import ChromaRepository
from vectorstore.index_manager import IndexManager
from vectorstore.repository import VectorStoreRepository

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Infrastructure singletons
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_repository(settings: Settings) -> ChromaRepository:
    return ChromaRepository(persist_directory=str(settings.chromadb_path))


@lru_cache(maxsize=1)
def _get_llm_client(settings: Settings) -> OllamaClient:
    return OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.llm_model,
        timeout_seconds=settings.generation_timeout_seconds,
        max_tokens=settings.max_tokens_generation,
    )


@lru_cache(maxsize=1)
def _get_embeddings(settings: Settings) -> EmbeddingsAdapter:
    return EmbeddingsAdapter(model_name=settings.embedding_model)


@lru_cache(maxsize=1)
def _get_index_manager(settings: Settings) -> IndexManager:
    repo = _get_repository(settings)
    return IndexManager(repository=repo)


@lru_cache(maxsize=1)
def _get_scraper(settings: Settings) -> Scraper:
    robots = RobotsChecker()
    scraper_client = ScraperClient(
        delay_seconds=settings.request_delay_seconds,
        timeout_seconds=settings.source_fetch_timeout_seconds,
    )
    extractor = HtmlExtractor(client=scraper_client, text_cleaner=TextCleaner())
    return Scraper(extractor=extractor)


@lru_cache(maxsize=1)
def _get_index_loader(settings: Settings) -> IndexLoader:
    chunker = Chunker(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
    embeddings = _get_embeddings(settings)
    manager = _get_index_manager(settings)
    return IndexLoader(chunker=chunker, embeddings=embeddings, index_manager=manager)


# ---------------------------------------------------------------------------
# FastAPI dependency functions (overridable in tests)
# ---------------------------------------------------------------------------

def get_settings_dep() -> Settings:
    return get_settings()


def get_repository(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> VectorStoreRepository:
    return _get_repository(settings)


def get_responder_service(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> ResponderConsultaService:
    repo = _get_repository(settings)
    llm = _get_llm_client(settings)
    embeddings = _get_embeddings(settings)
    return ResponderConsultaService(
        repository=repo,
        llm_client=llm,
        prompt_builder=PromptBuilder(),
        relevance_threshold=settings.relevance_threshold,
        top_k=settings.top_k,
        embeddings_adapter=embeddings,
    )


def get_indexar_service(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> IndexarContenidoService:
    return IndexarContenidoService(
        scraper=_get_scraper(settings),
        index_loader=_get_index_loader(settings),
        index_manager=_get_index_manager(settings),
        repository=_get_repository(settings),
    )


def get_estado_indice_service(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> ConsultarEstadoIndiceService:
    return ConsultarEstadoIndiceService(repository=_get_repository(settings))


def get_health_service(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> HealthService:
    return HealthService(
        repository=_get_repository(settings),
        llm_client=_get_llm_client(settings),
    )
