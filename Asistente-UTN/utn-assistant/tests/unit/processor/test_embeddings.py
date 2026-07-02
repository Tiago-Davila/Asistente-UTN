"""
T033 — Failing unit tests for embeddings adapter with mocked sentence-transformers.

Defines the contract that processor/embeddings.py must satisfy.
FR-022: embedding model name is configurable from settings.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _adapter(model_name: str = "test-model"):
    from processor.embeddings import EmbeddingsAdapter
    return EmbeddingsAdapter(model_name=model_name)


class TestEmbeddingsAdapterBehaviour:
    def test_encode_returns_list_of_floats(self):
        with patch("processor.embeddings.SentenceTransformer") as MockST:
            import numpy as np
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 384])
            MockST.return_value = mock_model

            adapter = _adapter()
            result = adapter.encode(["Texto de prueba"])
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], list)
            assert all(isinstance(v, float) for v in result[0])

    def test_encode_single_text_returns_single_embedding(self):
        with patch("processor.embeddings.SentenceTransformer") as MockST:
            import numpy as np
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.5] * 384])
            MockST.return_value = mock_model

            adapter = _adapter()
            result = adapter.encode(["Una consulta"])
            assert len(result) == 1

    def test_encode_multiple_texts_returns_matching_count(self):
        with patch("processor.embeddings.SentenceTransformer") as MockST:
            import numpy as np
            n = 5
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 384] * n)
            MockST.return_value = mock_model

            adapter = _adapter()
            result = adapter.encode([f"texto {i}" for i in range(n)])
            assert len(result) == n

    def test_encode_empty_list_returns_empty(self):
        with patch("processor.embeddings.SentenceTransformer") as MockST:
            import numpy as np
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([]).reshape(0, 384)
            MockST.return_value = mock_model

            adapter = _adapter()
            result = adapter.encode([])
            assert result == []

    def test_model_loaded_with_configured_name(self):
        with patch("processor.embeddings.SentenceTransformer") as MockST:
            import numpy as np
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.array([[0.1] * 384])
            MockST.return_value = mock_instance

            adapter = _adapter(model_name="intfloat/multilingual-e5-base")
            adapter.encode(["trigger load"])  # lazy-load happens on first encode
            MockST.assert_called_once_with("intfloat/multilingual-e5-base")

    def test_encode_query_returns_single_embedding(self):
        with patch("processor.embeddings.SentenceTransformer") as MockST:
            import numpy as np
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.3] * 384])
            MockST.return_value = mock_model

            adapter = _adapter()
            result = adapter.encode_query("Cuando es la inscripcion?")
            assert isinstance(result, list)
            assert all(isinstance(v, float) for v in result)
