"""
T068 — Scraper HTTP failure unit tests.

Tests ScraperClient and Scraper orchestration for error continuation.
FR-014: continue when individual URL fails; record failure without stopping.
FR-023: robots.txt compliance; request delay.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestScraperClientHTTPFailures:
    def test_404_raises_fetch_error(self):
        from scraper.client import ScraperClient, ScraperFetchError
        with patch("scraper.client.httpx.Client") as MockClient:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            MockClient.return_value.__enter__.return_value.get.return_value = mock_resp
            with patch("scraper.client.RobotsChecker") as MockRobots:
                MockRobots.return_value.is_allowed.return_value = True
                client = ScraperClient(delay_seconds=0.0)
                with pytest.raises(ScraperFetchError) as exc_info:
                    client.fetch("https://utn.edu.ar/missing")
                assert exc_info.value.status_code == 404

    def test_500_raises_fetch_error(self):
        from scraper.client import ScraperClient, ScraperFetchError
        with patch("scraper.client.httpx.Client") as MockClient:
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            MockClient.return_value.__enter__.return_value.get.return_value = mock_resp
            with patch("scraper.client.RobotsChecker") as MockRobots:
                MockRobots.return_value.is_allowed.return_value = True
                client = ScraperClient(delay_seconds=0.0)
                with pytest.raises(ScraperFetchError) as exc_info:
                    client.fetch("https://utn.edu.ar/error")
                assert exc_info.value.status_code == 500

    def test_timeout_raises_fetch_error(self):
        import httpx
        from scraper.client import ScraperClient, ScraperFetchError
        with patch("scraper.client.httpx.Client") as MockClient:
            MockClient.return_value.__enter__.return_value.get.side_effect = (
                httpx.TimeoutException("timeout")
            )
            with patch("scraper.client.RobotsChecker") as MockRobots:
                MockRobots.return_value.is_allowed.return_value = True
                client = ScraperClient(delay_seconds=0.0)
                with pytest.raises(ScraperFetchError):
                    client.fetch("https://utn.edu.ar/slow")

    def test_robots_denial_raises_fetch_error(self):
        from scraper.client import ScraperClient, ScraperFetchError
        with patch("scraper.client.RobotsChecker") as MockRobots:
            MockRobots.return_value.is_allowed.return_value = False
            client = ScraperClient(delay_seconds=0.0)
            with pytest.raises(ScraperFetchError) as exc_info:
                client.fetch("https://utn.edu.ar/private")
            assert exc_info.value.status_code is None

    def test_successful_fetch_returns_text(self):
        from scraper.client import ScraperClient
        with patch("scraper.client.httpx.Client") as MockClient:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "<html><body>Contenido</body></html>"
            MockClient.return_value.__enter__.return_value.get.return_value = mock_resp
            with patch("scraper.client.RobotsChecker") as MockRobots:
                MockRobots.return_value.is_allowed.return_value = True
                client = ScraperClient(delay_seconds=0.0)
                result = client.fetch("https://utn.edu.ar/page")
            assert "Contenido" in result


class TestScraperOrchestrationContinuation:
    def _make_source(self, source_id: str, url: str = None):
        from rag.domain.sources import InstitutionalSource
        from rag.domain.enums import AreaInstitucional, TipoFuente
        return InstitutionalSource(
            id=source_id,
            url=url or f"https://utn.edu.ar/{source_id}",
            area=AreaInstitucional.ACADEMICA,
            source_type=TipoFuente.WEB,
            active=True,
        )

    def test_failed_source_does_not_stop_scraping(self):
        from scraper.client import ScraperFetchError
        from scraper.run import Scraper
        from processor.text_cleaner import TextCleaner

        mock_extractor = MagicMock()
        mock_extractor.extract.side_effect = [
            ScraperFetchError("404", status_code=404),
            ("Contenido util de la segunda fuente.", "Pagina 2"),
        ]

        scraper = Scraper(extractor=mock_extractor)
        sources = [self._make_source("src1"), self._make_source("src2")]
        docs, failures = scraper.scrape_sources(sources)

        assert len(failures) == 1
        assert failures[0][0] == "src1"
        assert len(docs) == 1

    def test_all_failures_recorded(self):
        from scraper.client import ScraperFetchError
        from scraper.run import Scraper

        mock_extractor = MagicMock()
        mock_extractor.extract.side_effect = [
            ScraperFetchError("500", status_code=500),
            ScraperFetchError("timeout", status_code=None),
        ]

        scraper = Scraper(extractor=mock_extractor)
        sources = [self._make_source("s1"), self._make_source("s2")]
        docs, failures = scraper.scrape_sources(sources)

        assert len(docs) == 0
        assert len(failures) == 2

    def test_empty_page_discarded_as_failure(self):
        from scraper.run import Scraper

        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = ("", None)  # empty content

        scraper = Scraper(extractor=mock_extractor)
        sources = [self._make_source("s1")]
        docs, failures = scraper.scrape_sources(sources)

        assert len(docs) == 0
        assert len(failures) == 1

    def test_inactive_source_is_skipped(self):
        from scraper.run import Scraper
        from rag.domain.sources import InstitutionalSource
        from rag.domain.enums import AreaInstitucional, TipoFuente

        mock_extractor = MagicMock()
        scraper = Scraper(extractor=mock_extractor)

        inactive = InstitutionalSource(
            id="inactive",
            url="https://utn.edu.ar/inactive",
            area=AreaInstitucional.ACADEMICA,
            source_type=TipoFuente.WEB,
            active=False,
        )
        docs, failures = scraper.scrape_sources([inactive])

        mock_extractor.extract.assert_not_called()
        assert docs == []
        assert failures == []
