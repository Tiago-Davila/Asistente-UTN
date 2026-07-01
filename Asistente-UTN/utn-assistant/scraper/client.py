"""
scraper/client.py — Robots-aware HTTP client.

Uses httpx with configured delay and timeout.  Checks robots.txt before
fetching any URL (FR-023, research.md §robots.txt and Request Delay).
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

import httpx

from scraper.robots import RobotsChecker

logger = logging.getLogger(__name__)

_DEFAULT_USER_AGENT = "UTN-Assistant-Scraper/1.0 (institutional RAG; contact: admin@utn.edu.ar)"


class ScraperClient:
    """HTTP client that respects robots.txt and enforces request delays.

    Parameters
    ----------
    delay_seconds:
        Minimum wait between requests to the same domain.
    timeout_seconds:
        HTTP request timeout per URL.
    user_agent:
        User-agent string sent with every request.
    """

    def __init__(
        self,
        delay_seconds: float = 1.0,
        timeout_seconds: float = 10.0,
        user_agent: str = _DEFAULT_USER_AGENT,
    ) -> None:
        self._delay = delay_seconds
        self._timeout = timeout_seconds
        self._user_agent = user_agent
        self._robots = RobotsChecker(user_agent=user_agent)
        self._last_request: dict[str, float] = {}  # domain → timestamp

    def fetch(self, url: str) -> str:
        """Fetch a URL and return its response body as text.

        Raises
        ------
        ScraperFetchError
            When the URL is disallowed by robots.txt, returns a non-200
            status, or times out.
        """
        if not self._robots.is_allowed(url):
            raise ScraperFetchError(f"robots.txt disallows {url}", status_code=None)

        self._apply_delay(url)

        try:
            with httpx.Client(
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
                follow_redirects=True,
            ) as client:
                response = client.get(url)
        except httpx.TimeoutException as exc:
            raise ScraperFetchError(f"Timeout fetching {url}: {exc}", status_code=None) from exc
        except httpx.RequestError as exc:
            raise ScraperFetchError(f"Request error for {url}: {exc}", status_code=None) from exc

        if response.status_code != 200:
            raise ScraperFetchError(
                f"HTTP {response.status_code} for {url}",
                status_code=response.status_code,
            )

        self._record_request(url)
        return response.text

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_delay(self, url: str) -> None:
        domain = _extract_domain(url)
        last = self._last_request.get(domain, 0.0)
        elapsed = time.monotonic() - last
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)

    def _record_request(self, url: str) -> None:
        self._last_request[_extract_domain(url)] = time.monotonic()


class ScraperFetchError(Exception):
    """Raised when a URL cannot be fetched due to robots, HTTP errors, or timeout."""

    def __init__(self, message: str, status_code: Optional[int]) -> None:
        super().__init__(message)
        self.status_code = status_code


def _extract_domain(url: str) -> str:
    """Extract scheme + host from a URL for per-domain delay tracking."""
    try:
        parsed = httpx.URL(url)
        return f"{parsed.scheme}://{parsed.host}"
    except Exception:
        return url
