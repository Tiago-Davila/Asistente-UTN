"""
scraper/run.py — Scraper orchestration.

Iterates configured sources, fetches and extracts content, and returns
(documents, failures).  Individual URL failures are recorded without
stopping the run (FR-014).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from rag.domain.enums import EstadoIndexacion
from rag.domain.sources import ExtractedDocument, InstitutionalSource
from scraper.client import ScraperFetchError
from scraper.extractor import HtmlExtractor

logger = logging.getLogger(__name__)


class Scraper:
    """Orchestrates scraping across a list of configured sources.

    Parameters
    ----------
    extractor:
        HtmlExtractor for fetching and parsing pages.
    """

    def __init__(self, extractor: HtmlExtractor) -> None:
        self._extractor = extractor

    def scrape_sources(
        self,
        sources: list[InstitutionalSource],
    ) -> tuple[list[ExtractedDocument], list[tuple[str, str]]]:
        """Scrape each source and return (documents, failures).

        Parameters
        ----------
        sources:
            Active InstitutionalSource records to process.

        Returns
        -------
        documents:
            Successfully extracted ExtractedDocument objects.
        failures:
            List of (source_id, reason) tuples for sources that failed.
        """
        documents: list[ExtractedDocument] = []
        failures: list[tuple[str, str]] = []

        for source in sources:
            if not source.active:
                logger.debug("Skipping inactive source %s", source.id)
                continue

            try:
                clean_text, title = self._extractor.extract(
                    source.url,
                    requires_javascript=source.requires_javascript,
                )

                if not clean_text.strip():
                    logger.info(
                        "Empty or script-only content for source %s (%s); discarding.",
                        source.id, source.url,
                    )
                    failures.append((source.id, "empty or script-only content"))
                    continue

                doc = ExtractedDocument(
                    id=str(uuid.uuid4()),
                    source_id=source.id,
                    url=source.url,
                    title=title or source.title_hint,
                    raw_text=clean_text,
                    clean_text=clean_text,
                    area=source.area,
                    regional=source.regional,
                    department=source.department,
                    source_type=source.source_type,
                    extracted_at=datetime.now(timezone.utc),
                    status=EstadoIndexacion.COMPLETADO,
                )
                documents.append(doc)
                logger.debug("Extracted document from source %s", source.id)

            except ScraperFetchError as exc:
                reason = str(exc)
                logger.warning(
                    "Fetch failed for source %s (%s): %s",
                    source.id, source.url, reason,
                )
                failures.append((source.id, reason))

            except Exception as exc:
                reason = f"unexpected error: {exc}"
                logger.error(
                    "Unexpected error scraping source %s: %s",
                    source.id, reason,
                )
                failures.append((source.id, reason))

        logger.info(
            "Scraper finished: %d documents, %d failures.",
            len(documents), len(failures),
        )
        return documents, failures
