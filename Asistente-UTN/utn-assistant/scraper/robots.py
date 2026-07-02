"""
scraper/robots.py — robots.txt policy helper.

Caches robots.txt per domain and evaluates whether a given URL is
allowed for the configured user-agent (FR-023).
"""
from __future__ import annotations

import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_USER_AGENT = "UTN-Assistant-Scraper/1.0"


class RobotsChecker:
    """Per-domain robots.txt cache and allow/disallow evaluator.

    Parameters
    ----------
    user_agent:
        The user-agent string used when evaluating robots.txt rules.
    fetch_timeout:
        Timeout (seconds) for fetching robots.txt files.
    """

    def __init__(
        self,
        user_agent: str = _DEFAULT_USER_AGENT,
        fetch_timeout: float = 5.0,
    ) -> None:
        self._user_agent = user_agent
        self._fetch_timeout = fetch_timeout
        self._cache: dict[str, RobotFileParser] = {}

    def is_allowed(self, url: str) -> bool:
        """Return True when the URL is permitted by the domain's robots.txt.

        On any error fetching robots.txt, defaults to allowing the URL
        (fail-open) and logs a warning.
        """
        parser = self._get_parser(url)
        if parser is None:
            return True  # fail-open: if we can't read robots.txt, allow

        try:
            return parser.can_fetch(self._user_agent, url)
        except Exception as exc:
            logger.warning("robots.txt evaluation error for %s: %s", url, exc)
            return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_parser(self, url: str) -> RobotFileParser | None:
        domain = _robots_url(url)
        if domain not in self._cache:
            self._cache[domain] = self._fetch(domain)
        return self._cache[domain]

    def _fetch(self, robots_url: str) -> RobotFileParser | None:
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            with httpx.Client(timeout=self._fetch_timeout) as client:
                response = client.get(robots_url)
            if response.status_code == 200:
                parser.parse(response.text.splitlines())
            else:
                logger.debug("robots.txt not found at %s (%d)", robots_url, response.status_code)
        except Exception as exc:
            logger.warning("Could not fetch robots.txt at %s: %s", robots_url, exc)
            return None
        return parser


def _robots_url(url: str) -> str:
    """Derive the robots.txt URL from any URL on the same host."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"
