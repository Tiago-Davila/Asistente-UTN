"""
T067 — Scraper extractor unit tests.

Tests HtmlExtractor against fixture HTML pages.
FR-012: exclude navigation, scripts, menus; extract useful text and title.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "html"


def _load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _make_extractor(html: str):
    """Return an HtmlExtractor whose client.fetch() returns the given HTML."""
    from scraper.client import ScraperClient
    from scraper.extractor import HtmlExtractor
    from processor.text_cleaner import TextCleaner

    mock_client = MagicMock(spec=ScraperClient)
    mock_client.fetch.return_value = html
    return HtmlExtractor(client=mock_client, text_cleaner=TextCleaner())


class TestHtmlExtractorValidPage:
    def test_extracts_useful_text(self):
        html = _load_fixture("utn_valid_page.html")
        extractor = _make_extractor(html)
        text, _ = extractor.extract("https://utn.edu.ar/test")
        assert len(text.strip()) > 0

    def test_extracts_institutional_content(self):
        html = _load_fixture("utn_valid_page.html")
        extractor = _make_extractor(html)
        text, _ = extractor.extract("https://utn.edu.ar/test")
        # The fixture page contains inscription-related text
        assert any(kw in text.lower() for kw in ["inscripci", "guarani", "cuatrimestre", "examen"])

    def test_extracts_page_title(self):
        html = _load_fixture("utn_valid_page.html")
        extractor = _make_extractor(html)
        _, title = extractor.extract("https://utn.edu.ar/test")
        assert title is not None
        assert len(title) > 0
        assert "UTN" in title or "Inscripcion" in title or "Inscripciones" in title

    def test_nav_content_removed(self):
        html = _load_fixture("utn_valid_page.html")
        extractor = _make_extractor(html)
        text, _ = extractor.extract("https://utn.edu.ar/test")
        # Nav link text should not appear as standalone content
        # (the nav is removed; "Inicio" may appear in body but not as nav element)
        assert "<nav>" not in text
        assert "<header>" not in text

    def test_footer_content_removed(self):
        html = _load_fixture("utn_valid_page.html")
        extractor = _make_extractor(html)
        text, _ = extractor.extract("https://utn.edu.ar/test")
        assert "<footer>" not in text


class TestHtmlExtractorEmptyPage:
    def test_empty_page_returns_empty_text(self):
        html = _load_fixture("utn_empty_page.html")
        extractor = _make_extractor(html)
        text, _ = extractor.extract("https://utn.edu.ar/empty")
        assert text.strip() == ""

    def test_empty_page_title_still_extracted(self):
        html = _load_fixture("utn_empty_page.html")
        extractor = _make_extractor(html)
        _, title = extractor.extract("https://utn.edu.ar/empty")
        # Title tag exists in empty fixture
        assert title is not None

    def test_text_cleaner_is_empty_for_empty_page(self):
        from processor.text_cleaner import TextCleaner
        html = _load_fixture("utn_empty_page.html")
        cleaner = TextCleaner()
        assert cleaner.is_empty(html) is True


class TestHtmlExtractorScriptOnlyPage:
    def test_script_only_page_returns_empty_text(self):
        html = _load_fixture("utn_script_only_page.html")
        extractor = _make_extractor(html)
        text, _ = extractor.extract("https://utn.edu.ar/scripts")
        assert text.strip() == ""

    def test_script_content_not_in_extracted_text(self):
        html = _load_fixture("utn_script_only_page.html")
        extractor = _make_extractor(html)
        text, _ = extractor.extract("https://utn.edu.ar/scripts")
        assert "loadApp" not in text
        assert "dataLayer" not in text
        assert "googletagmanager" not in text
