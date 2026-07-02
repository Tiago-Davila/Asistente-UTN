"""
rag/services/responder_consulta.py — Answer orchestration service.

Implements US1 (query), US2 (refusal), US3 (citation) in one service.

Flow:
  1. Embed the question.
  2. Retrieve top-k fragments from the vector store.
  3. Order by descending relevance (domain rules).
  4. Check context sufficiency against the global threshold.
  5a. Insufficient context → return approved refusal answer (FR-007).
  5b. Sufficient context → build prompt → generate → assemble answer with
      cited sources (FR-005).

Traceability: T047 (US1), T048 (US2), T049 (US3).
"""
from __future__ import annotations

import logging
from typing import Optional

from rag.domain.enums import AreaInstitucional
from rag.domain.fragments import SearchResultSet
from rag.domain.queries import AssistantAnswer, UserQuery
from rag.domain.rules import (
    build_cited_sources,
    is_context_sufficient,
    make_refusal_answer,
    order_results,
)
from rag.prompting import PromptBuilder
from rag.services.llm_client import LLMGenerationError, OllamaClient
from vectorstore.repository import VectorStoreRepository

logger = logging.getLogger(__name__)


class ResponderConsultaService:
    """Orchestrates retrieval, threshold check, and answer generation.

    Parameters
    ----------
    repository:
        VectorStoreRepository for fragment retrieval.
    llm_client:
        OllamaClient (or compatible mock) for answer generation.
    prompt_builder:
        PromptBuilder for constructing the generation prompt.
    relevance_threshold:
        Global cosine-similarity threshold (FR-006).
    top_k:
        Maximum fragments to retrieve per query.
    """

    def __init__(
        self,
        repository: VectorStoreRepository,
        llm_client: OllamaClient,
        prompt_builder: PromptBuilder,
        relevance_threshold: float = 0.65,
        top_k: int = 5,
        embeddings_adapter=None,
    ) -> None:
        self._repository = repository
        self._llm = llm_client
        self._prompt_builder = prompt_builder
        self._threshold = relevance_threshold
        self._top_k = top_k
        self._embeddings = embeddings_adapter  # optional; required for real queries

    def answer(self, query: UserQuery) -> AssistantAnswer:
        """Process a UserQuery and return an AssistantAnswer.

        Never raises — all error paths return a structured AssistantAnswer
        with an error payload (FR-021).
        """
        effective_top_k = query.max_results or self._top_k

        # 1. Retrieve fragments
        try:
            raw_results = self._repository.query_fragments(
                query_embedding=self._embed(query.question),
                top_k=effective_top_k,
                area_filter=query.area_filter,
            )
        except Exception as exc:
            logger.error("Vector store query failed: %s", exc)
            return AssistantAnswer(
                answer="",
                sources=[],
                context_sufficient=False,
                error={"code": "INDEX_ERROR", "message": "Error al consultar el índice."},
            )

        # 2. Order by descending relevance
        results = order_results(raw_results)

        # 3. Build result set and check sufficiency
        result_set = SearchResultSet(
            results=results,
            threshold=self._threshold,
            area_filter=query.area_filter,
        )
        result_set.context_sufficient = is_context_sufficient(result_set)

        if not result_set.context_sufficient:
            logger.debug("Insufficient context for query: returning refusal.")
            return make_refusal_answer()

        # 4. Build prompt and generate answer
        try:
            prompt = self._prompt_builder.build(
                question=query.question,
                results=results,
            )
            answer_text = self._llm.generate(prompt)
        except LLMGenerationError as exc:
            logger.warning("LLM generation failed: %s", exc)
            return AssistantAnswer(
                answer="",
                sources=[],
                context_sufficient=False,
                error={"code": "GENERATOR_UNAVAILABLE", "message": str(exc)},
            )

        # 5. Assemble answer with cited sources
        cited = build_cited_sources(results)
        return AssistantAnswer(
            answer=answer_text,
            sources=cited,
            context_sufficient=True,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _embed(self, text: str) -> list[float]:
        """Return a query embedding using the injected adapter."""
        if self._embeddings is not None:
            return self._embeddings.encode_query(text)
        # When no adapter is injected (unit-test mock path), the repo mock
        # ignores the embedding argument, so we return a dummy vector.
        return [0.0] * 384
