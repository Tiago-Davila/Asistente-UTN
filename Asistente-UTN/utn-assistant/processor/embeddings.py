"""
processor/embeddings.py — Sentence-transformers embeddings adapter.

Wraps the sentence-transformers library so the rest of the application never
imports it directly.  Model name is loaded from settings (FR-022).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer  # noqa: F401 (for patching in tests)
except ImportError:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


class EmbeddingsAdapter:
    """Lazy-loading sentence-transformers adapter.

    Parameters
    ----------
    model_name:
        HuggingFace model ID, e.g. ``intfloat/multilingual-e5-base``.
    """

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None  # loaded on first use

    def _load(self):
        if self._model is None:
            logger.info("Loading embedding model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Encode a batch of texts and return a list of float vectors."""
        if not texts:
            return []
        model = self._load()
        import numpy as np
        vectors = model.encode(texts)
        # Handle both numpy arrays and lists gracefully.
        if hasattr(vectors, "tolist"):
            result = vectors.tolist()
        else:
            result = [list(v) for v in vectors]
        # Ensure each element is a list[float]
        return [[float(x) for x in row] for row in result]

    def encode_query(self, text: str) -> list[float]:
        """Encode a single query string and return a flat float vector."""
        vectors = self.encode([text])
        return vectors[0] if vectors else []
