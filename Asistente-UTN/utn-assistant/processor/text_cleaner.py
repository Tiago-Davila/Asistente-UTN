"""
processor/text_cleaner.py — Canonical text cleaning and empty-content detection.

Centralises HTML stripping, whitespace normalisation, and empty-content
rejection for all ingestion paths (research.md §Text Cleaning Ownership).

FR-012: exclude navigation, scripts, menus, and irrelevant elements.
"""
from __future__ import annotations

import re
import unicodedata

from bs4 import BeautifulSoup


_REMOVE_TAGS = {
    "script", "style", "nav", "header", "footer",
    "noscript", "iframe", "aside", "head",
}


class TextCleaner:
    """Stateless text cleaner shared across scraper output and any future ingestion path."""

    def clean(self, raw: str) -> str:
        """Strip HTML, remove irrelevant elements, and normalise whitespace.

        Parameters
        ----------
        raw:
            Raw HTML markup or plain text from a scraped page.

        Returns
        -------
        Cleaned plain text with collapsed whitespace.  May be empty when the
        source contains no useful content.
        """
        # Parse with lxml for speed; fall back to html.parser if unavailable.
        try:
            soup = BeautifulSoup(raw, "lxml")
        except Exception:
            soup = BeautifulSoup(raw, "html.parser")

        # Remove non-content elements entirely.
        for tag in _REMOVE_TAGS:
            for element in soup.find_all(tag):
                element.decompose()

        text = soup.get_text(separator=" ")
        return self._normalise(text)

    def is_empty(self, raw: str) -> bool:
        """Return True when the source yields no useful text after cleaning."""
        return self.clean(raw).strip() == ""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(text: str) -> str:
        # Normalise unicode (NFC)
        text = unicodedata.normalize("NFC", text)
        # Collapse all whitespace (spaces, tabs, newlines) into single spaces.
        text = re.sub(r"\s+", " ", text)
        return text.strip()
