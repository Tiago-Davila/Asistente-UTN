"""
config/settings.py — Centralised typed settings for the UTN assistant.

All operational values are loaded from environment variables (or a .env file).
No business logic lives here; this module only defines and validates
configuration shapes.

FR-022: Source URLs, area definitions, relevance threshold, question length
limit, source update delay, chunk sizing, and model choices are configurable.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Source configuration
    # ------------------------------------------------------------------
    sources_config_path: Path = Field(
        default=Path("./config/sources.yaml"),
        description="Path to the YAML file listing configured UTN institutional sources.",
    )

    # ------------------------------------------------------------------
    # ChromaDB persistence
    # ------------------------------------------------------------------
    chromadb_path: Path = Field(
        default=Path("./data/chromadb"),
        description="Directory where ChromaDB stores its persistent data.",
    )

    # ------------------------------------------------------------------
    # Ollama / LLM
    # ------------------------------------------------------------------
    ollama_base_url: str = Field(
        default="http://localhost:11434/v1",
        description="Base URL for the Ollama-compatible OpenAI endpoint.",
    )
    llm_model: str = Field(
        default="llama3",
        description="Chat/generation model name used for answer synthesis.",
    )
    embedding_model: str = Field(
        default="intfloat/multilingual-e5-base",
        description="Sentence-transformers model name for embedding generation.",
    )

    # ------------------------------------------------------------------
    # RAG retrieval — FR-006, FR-010, research.md §Relevance Threshold
    # ------------------------------------------------------------------
    relevance_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description=(
            "Global cosine-similarity threshold (0–1). Queries where no retrieved "
            "fragment meets this threshold trigger the refusal response."
        ),
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of fragments retrieved per query.",
    )

    # ------------------------------------------------------------------
    # Chunking — research.md §Chunk Size and Overlap
    # ------------------------------------------------------------------
    chunk_size: int = Field(
        default=800,
        ge=100,
        description="Target chunk size in text units (tokens / characters).",
    )
    chunk_overlap: int = Field(
        default=120,
        ge=0,
        description="Overlap between consecutive chunks in text units.",
    )

    @field_validator("chunk_overlap")
    @classmethod
    def overlap_less_than_size(cls, v: int, info) -> int:
        chunk_size = info.data.get("chunk_size", 800)
        if v >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v

    # ------------------------------------------------------------------
    # Scraper — FR-023, research.md §robots.txt and Request Delay
    # ------------------------------------------------------------------
    request_delay_seconds: float = Field(
        default=1.0,
        ge=0.0,
        description="Delay between HTTP requests to the same domain (seconds).",
    )
    source_fetch_timeout_seconds: float = Field(
        default=10.0,
        ge=1.0,
        description="HTTP timeout for fetching a single source page (seconds).",
    )

    # ------------------------------------------------------------------
    # Query validation — FR-002
    # ------------------------------------------------------------------
    max_question_length: int = Field(
        default=2000,
        ge=1,
        description="Maximum allowed question length in characters.",
    )

    # ------------------------------------------------------------------
    # Generation timeout — research.md §Timeout Strategy, Edge Cases
    # ------------------------------------------------------------------
    generation_timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        description=(
            "Hard generation timeout in seconds. Queries that exceed this "
            "return a controlled error without exposing internal details."
        ),
    )

    # ------------------------------------------------------------------
    # API server
    # ------------------------------------------------------------------
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
