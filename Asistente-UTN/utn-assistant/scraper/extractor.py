"""
scraper/extractor.py — HTML content extractor.

Uses httpx + BeautifulSoup4 for static pages and Playwright for sources
that require JavaScript rendering (FR-012, research.md §Scraping Strategy).

The extractor returns (clean_text, page_title) from a URL, using the
TextCleaner for canonical normalisation.
"""
from __future__ import annotations

import logging
from typing import Optional

from bs4 import BeautifulSoup

from processor.text_cleaner import TextCleaner
from scraper.client import ScraperClient, ScraperFetchError

logger = logging.getLogger(__name__)


class HtmlExtractor:
    """Extracts useful text and page title from a URL.

    Parameters
    ----------
    client:
        ScraperClient used for static pages.
    text_cleaner:
        TextCleaner for canonical normalisation.
    """

    def __init__(
        self,
        client: ScraperClient,
        text_cleaner: TextCleaner,
    ) -> None:
        self._client = client
        self._cleaner = text_cleaner

    def extract(
        self, url: str, requires_javascript: bool = False
    ) -> tuple[str, Optional[str]]:
        """Fetch and extract useful text and title from a URL.

        Returns
        -------
        (clean_text, page_title)
            clean_text is the normalised body text; may be empty for pages
            with no useful content (handled upstream as a discard case).
            page_title is the <title> text when available, else None.

        Raises
        ------
        ScraperFetchError
            Propagated from ScraperClient on HTTP errors, timeouts, or
            robots.txt denials.
        """
        if requires_javascript:
            html = self._fetch_with_playwright(url)
        else:
            html = self._client.fetch(url)

        return self._parse(html)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse(self, html: str) -> tuple[str, Optional[str]]:
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.find("title")
        page_title: Optional[str] = title_tag.get_text(strip=True) if title_tag else None

        clean_text = self._cleaner.clean(html)
        return clean_text, page_title

    def _fetch_with_playwright(self, url: str) -> str:  # pragma: no cover
        """Fetch a JS-rendered page using Playwright (synchronous wrapper)."""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=30_000)
                html = page.content()
                browser.close()
            return html
        except Exception as exc:
            raise ScraperFetchError(
                f"Playwright fetch failed for {url}: {exc}", status_code=None
            ) from exc
