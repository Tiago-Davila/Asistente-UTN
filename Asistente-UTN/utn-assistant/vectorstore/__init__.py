"""
vectorstore — ChromaDB repository abstraction package.

Public API:

  VectorStoreRepository   — abstract interface (repository.py)
  ChromaRepository        — PersistentClient adapter (chroma_repository.py)
  IndexManager            — staging/swap coordinator (index_manager.py)
  build_index_status      — IndexStatus mapper from a live collection (status.py)

Rule: No module outside vectorstore/ may import chromadb directly.
(tasks.md §Notes)
"""
from __future__ import annotations

from vectorstore.repository import VectorStoreRepository
from vectorstore.chroma_repository import ChromaRepository
from vectorstore.index_manager import IndexManager
from vectorstore.status import build_index_status

__all__ = [
    "VectorStoreRepository",
    "ChromaRepository",
    "IndexManager",
    "build_index_status",
]
