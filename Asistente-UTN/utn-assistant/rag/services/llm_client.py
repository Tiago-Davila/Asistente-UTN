"""
rag/services/llm_client.py — Ollama-compatible OpenAI client adapter.

Wraps the httpx-based chat completion call to the local Ollama endpoint.
Configuration (URL, model, timeout) comes from settings (FR-022).

research.md §Timeout Strategy: 30-second hard generation timeout with
a controlled error on breach (no internal details exposed to users).
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class LLMGenerationError(Exception):
    """Raised when the LLM cannot produce a response within constraints."""


class OllamaClient:
    """HTTP client for the Ollama-compatible /v1/chat/completions endpoint.

    Parameters
    ----------
    base_url:
        Base URL of the Ollama server, e.g. ``http://localhost:11434/v1``.
    model:
        Model name to use for generation, e.g. ``llama3``.
    timeout_seconds:
        Hard timeout for the generation request.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "llama3",
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds

    def generate(self, prompt: str) -> str:
        """Send a generation request and return the assistant's reply text.

        Raises
        ------
        LLMGenerationError
            On timeout, connection failure, or unexpected response format.
            The original exception detail is logged but not surfaced to callers
            (FR-021: clear error without exposing internals).
        """
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            logger.warning("LLM generation timed out after %ss: %s", self._timeout, exc)
            raise LLMGenerationError("El generador de respuestas superó el tiempo máximo.") from exc
        except httpx.RequestError as exc:
            logger.warning("LLM generation request failed: %s", exc)
            raise LLMGenerationError("El generador de respuestas no está disponible.") from exc

        if response.status_code != 200:
            logger.warning("LLM returned HTTP %d", response.status_code)
            raise LLMGenerationError("El generador de respuestas devolvió un error inesperado.")

        try:
            data = response.json()
            text: str = data["choices"][0]["message"]["content"]
            return text.strip()
        except (KeyError, IndexError, ValueError) as exc:
            logger.warning("Could not parse LLM response: %s — raw: %s", exc, response.text[:200])
            raise LLMGenerationError("Respuesta del generador en formato inesperado.") from exc

    def is_available(self) -> bool:
        """Return True when the Ollama server responds to a health ping."""
        try:
            with httpx.Client(timeout=3.0) as client:
                r = client.get(f"{self._base_url.replace('/v1', '')}/api/tags")
            return r.status_code == 200
        except Exception:
            return False
