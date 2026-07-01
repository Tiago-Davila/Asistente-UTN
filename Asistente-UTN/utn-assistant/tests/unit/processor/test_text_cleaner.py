"""
T031 — Failing unit tests for text cleaning.

Defines the contract that processor/text_cleaner.py must satisfy.
FR-012: exclude navigation, scripts, menus, and irrelevant page elements.
research.md §Text Cleaning Ownership: canonical normalisation lives here.
"""
from __future__ import annotations

import pytest


def _cleaner():
    from processor.text_cleaner import TextCleaner
    return TextCleaner()


class TestTextCleanerHTMLRemnants:
    def test_html_tags_are_stripped(self):
        c = _cleaner()
        assert "<p>" not in c.clean("<p>Hola mundo</p>")

    def test_script_content_is_removed(self):
        c = _cleaner()
        result = c.clean("<script>alert('x')</script>Contenido util")
        assert "alert" not in result
        assert "Contenido util" in result

    def test_style_content_is_removed(self):
        c = _cleaner()
        result = c.clean("<style>.nav{display:none}</style>Texto")
        assert ".nav" not in result
        assert "Texto" in result

    def test_nav_element_is_removed(self):
        c = _cleaner()
        result = c.clean("<nav><a>Menu</a></nav>Contenido principal")
        assert "Menu" not in result
        assert "Contenido principal" in result

    def test_header_element_is_removed(self):
        c = _cleaner()
        result = c.clean("<header>Logo</header>Texto principal")
        assert "Logo" not in result

    def test_footer_element_is_removed(self):
        c = _cleaner()
        result = c.clean("<footer>Copyright 2024</footer>Texto")
        assert "Copyright" not in result

    def test_multiple_spaces_collapsed(self):
        c = _cleaner()
        result = c.clean("Texto   con    espacios")
        assert "  " not in result

    def test_plain_text_preserved(self):
        c = _cleaner()
        text = "Inscripciones abiertas para el segundo cuatrimestre."
        assert c.clean(text).strip() == text


class TestTextCleanerEmptyContent:
    def test_empty_string_raises_or_returns_empty(self):
        c = _cleaner()
        result = c.clean("")
        assert result.strip() == ""

    def test_whitespace_only_returns_empty(self):
        c = _cleaner()
        result = c.clean("   \n\t  ")
        assert result.strip() == ""

    def test_script_only_page_returns_empty(self):
        c = _cleaner()
        result = c.clean("<script>var x=1;</script>")
        assert result.strip() == ""

    def test_is_empty_detects_no_useful_content(self):
        c = _cleaner()
        assert c.is_empty("<script>x</script><style>y</style>") is True

    def test_is_empty_returns_false_for_useful_content(self):
        c = _cleaner()
        assert c.is_empty("<p>Texto institucional</p>") is False
