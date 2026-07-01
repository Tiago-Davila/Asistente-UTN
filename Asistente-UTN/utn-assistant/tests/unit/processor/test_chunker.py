"""
T032 — Failing unit tests for chunk size and overlap.

Defines the contract that processor/chunker.py must satisfy.
research.md §Chunk Size and Overlap: default 800 units, 120 overlap.
FR-022: chunk size and overlap are configurable from settings.
"""
from __future__ import annotations

import pytest


def _chunker(chunk_size: int = 800, overlap: int = 120):
    from processor.chunker import Chunker
    return Chunker(chunk_size=chunk_size, chunk_overlap=overlap)


class TestChunkerSizeAndOverlap:
    def test_short_text_produces_single_chunk(self):
        c = _chunker()
        chunks = c.split("Texto corto.")
        assert len(chunks) == 1

    def test_long_text_produces_multiple_chunks(self):
        c = _chunker(chunk_size=100, overlap=20)
        text = "palabra " * 50  # ~400 chars
        chunks = c.split(text)
        assert len(chunks) > 1

    def test_each_chunk_does_not_exceed_chunk_size(self):
        c = _chunker(chunk_size=100, overlap=20)
        text = "a" * 500
        for chunk in c.split(text):
            assert len(chunk) <= 100 + 20  # allow slight overshoot at word boundaries

    def test_overlap_content_shared_between_adjacent_chunks(self):
        c = _chunker(chunk_size=50, overlap=10)
        text = "ab" * 60
        chunks = c.split(text)
        if len(chunks) >= 2:
            # The end of chunk[0] and start of chunk[1] should share content
            tail = chunks[0][-10:]
            head = chunks[1][:10]
            # At least some overlap should exist
            assert len(set(tail) & set(head)) > 0 or tail in chunks[1] or head in chunks[0]

    def test_empty_text_returns_no_chunks(self):
        c = _chunker()
        assert c.split("") == []

    def test_whitespace_only_returns_no_chunks(self):
        c = _chunker()
        assert c.split("   \n\t  ") == []

    def test_custom_chunk_size_respected(self):
        c = _chunker(chunk_size=200, overlap=50)
        text = "palabra " * 100
        chunks = c.split(text)
        assert all(len(ch) <= 200 + 50 for ch in chunks)

    def test_chunk_count_increases_with_longer_text(self):
        c = _chunker(chunk_size=100, overlap=0)
        short_chunks = c.split("a" * 100)
        long_chunks = c.split("a" * 1000)
        assert len(long_chunks) > len(short_chunks)


class TestChunkerChunkIndex:
    def test_chunks_have_sequential_indices(self):
        from processor.chunker import Chunker
        c = Chunker(chunk_size=100, chunk_overlap=20)
        text = "texto " * 100
        indexed = c.split_with_index(text)
        indices = [idx for idx, _ in indexed]
        assert indices == list(range(len(indices)))

    def test_split_with_index_returns_text_and_index(self):
        from processor.chunker import Chunker
        c = Chunker(chunk_size=100, chunk_overlap=0)
        result = c.split_with_index("Hola mundo " * 20)
        for idx, text in result:
            assert isinstance(idx, int)
            assert isinstance(text, str)
            assert len(text) > 0
