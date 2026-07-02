"""
config/source_loader.py — Load InstitutionalSource records from YAML config.

Reads the sources YAML file (sources.yaml / sources.example.yaml) and
returns a list of InstitutionalSource domain objects.

FR-011: administrators configure sources without changing application code.
FR-022: source URLs and area definitions are operational configuration values.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from rag.domain.enums import AreaInstitucional, TipoFuente
from rag.domain.sources import InstitutionalSource

logger = logging.getLogger(__name__)


def load_sources(config_path: Path | str) -> list[InstitutionalSource]:
    """Parse sources YAML and return active InstitutionalSource records.

    Returns an empty list when the file does not exist (allows the API to
    start cleanly before sources are configured).
    """
    path = Path(config_path)
    if not path.exists():
        logger.warning("Sources config not found at %s; returning empty list.", path)
        return []

    try:
        with open(path, encoding="utf-8") as fh:
            data: dict[str, Any] = yaml.safe_load(fh) or {}
    except Exception as exc:
        logger.error("Failed to load sources config from %s: %s", path, exc)
        return []

    raw_sources: list[dict] = data.get("sources", [])
    sources: list[InstitutionalSource] = []

    for raw in raw_sources:
        try:
            source = InstitutionalSource(
                id=raw["id"],
                url=raw["url"],
                title_hint=raw.get("title_hint"),
                area=AreaInstitucional(raw["area"]),
                regional=raw.get("regional"),
                department=raw.get("department"),
                source_type=TipoFuente(raw.get("source_type", "WEB")),
                active=raw.get("active", True),
                requires_javascript=raw.get("requires_javascript", False),
                crawl_delay_seconds=raw.get("crawl_delay_seconds"),
                include_patterns=raw.get("include_patterns", []),
                exclude_patterns=raw.get("exclude_patterns", []),
            )
            sources.append(source)
        except Exception as exc:
            logger.warning("Skipping malformed source entry %s: %s", raw.get("id", "?"), exc)

    logger.info("Loaded %d sources from %s.", len(sources), path)
    return sources
