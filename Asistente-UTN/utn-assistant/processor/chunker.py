"""
processor/chunker.py — Configurable text chunker.

Splits cleaned text into overlapping chunks suitable for embedding and
retrieval.  Chunk size and overlap come from settings (FR-022).

research.md §Chunk Size and Overlap: default 800 units, 120 overlap.
"""
from __future__ import annotations

import re


class Chunker:
    """Character-based overlapping text chunker.

    Parameters
    ----------
    chunk_size:
        Target maximum chunk length in characters.
    chunk_overlap:
        Number of characters shared between adjacent chunks.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def split(self, text: str) -> list[str]:
        """Return a list of chunk strings; empty list when text has no content."""
        text = text.strip()
        if not text:
            return []

        chunks: list[str] = []
        step = self._chunk_size - self._chunk_overlap
        start = 0

        while start < len(text):
            end = start + self._chunk_size
            chunk = text[start:end]

            # Try to break at a word boundary if we're not at the end.
            if end < len(text):
                boundary = chunk.rfind(" ")
                if boundary > self._chunk_size // 2:
                    chunk = chunk[:boundary]

            chunk = chunk.strip()
            if chunk:
                chunks.append(chunk)

            advance = len(chunk) - self._chunk_overlap
            if advance <= 0:
                advance = max(1, step)
            start += advance

        return chunks

    def split_with_index(self, text: str) -> list[tuple[int, str]]:
        """Return ``(chunk_index, chunk_text)`` pairs.

        Chunk indices are sequential starting at 0.
        """
        return list(enumerate(self.split(text)))
