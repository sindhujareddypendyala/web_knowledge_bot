"""
Robots.txt handling for the Website Knowledge Module.

Purpose:
    Fetches, parses, caches, and evaluates robots.txt rules so crawlers respect
    site-owner crawl policies before requesting pages.

How it connects:
    Sync crawlers, async crawlers, sitemap loaders, and website refresh jobs use
    `RobotsHandler` to decide whether a URL can be crawled, discover sitemap
    hints, and honor crawl-delay rules when available.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Iterable
from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests

from config import REQUEST_TIMEOUT_SECONDS, RESPECT_ROBOTS_TXT, USER_AGENT
from utils.logger import get_logger, log_event
from utils.validators import normalize_url

logger = get_logger(__name__)


@dataclass(slots=True)
class RobotsRules:
    """Cached robots.txt policy for a single origin."""

    robots_url: str
    parser: RobotFileParser
    fetched_at: float = field(default_factory=time.time)
    available: bool = True
    error: str | None = None

    def can_fetch(self, user_agent: str, url: str) -> bool:
        if not self.available:
            return True
        return self.parser.can_fetch(user_agent, url)

    def crawl_delay(self, user_agent: str) -> float | None:
        if not self.available:
            return None
        delay = self.parser.crawl_delay(user_agent)
        return float(delay) if delay is not None else None

    def sitemaps(self) -> list[str]:
        if not self.available:
            return []
        return list(self.parser.site_maps() or [])


class RobotsHandler:
    """Service object for robots.txt fetching, caching, and policy checks."""

    def __init__(
        self,
        user_agent: str = USER_AGENT,
        respect_robots: bool = RESPECT_ROBOTS_TXT,
        timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
        cache_ttl_seconds: int = 3600,
        session: requests.Session | None = None,
    ) -> None:
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self.timeout_seconds = timeout_seconds
        self.cache_ttl_seconds = cache_ttl_seconds
        self.session = session or requests.Session()
        self._cache: dict[str, RobotsRules] = {}

    def can_fetch(self, url: str) -> bool:
        """Return whether `url` is allowed for this handler's user agent."""

        if not self.respect_robots:
            return True

        normalized_url = normalize_url(url)
        rules = self.get_rules(normalized_url)
        allowed = rules.can_fetch(self.user_agent, normalized_url)

        log_event(
            logger,
            "DEBUG",
            "Evaluated robots.txt rule",
            url=normalized_url,
            robots_url=rules.robots_url,
            allowed=allowed,
            available=rules.available,
        )
        return allowed

    def get_crawl_delay(self, url: str, default: float | None = None) -> float | None:
        """Return crawl-delay from robots.txt, falling back to `default`."""

        if not self.respect_robots:
            return default

        rules = self.get_rules(normalize_url(url))
        return rules.crawl_delay(self.user_agent) or default

    def get_sitemaps(self, url: str) -> list[str]:
        """Return sitemap URLs advertised by robots.txt."""

        rules = self.get_rules(normalize_url(url))
        return rules.sitemaps()

    def filter_allowed_urls(self, urls: Iterable[str]) -> list[str]:
        """Normalize and keep only URLs allowed by robots.txt."""

        allowed_urls: list[str] = []
        for url in urls:
            try:
                normalized = normalize_url(url)
            except ValueError:
                continue
            if self.can_fetch(normalized):
                allowed_urls.append(normalized)
        return allowed_urls

    def get_rules(self, url: str) -> RobotsRules:
        """Return cached robots rules for `url`'s origin, fetching if needed."""

        robots_url = build_robots_url(url)
        cached = self._cache.get(robots_url)
        if cached and not self._is_expired(cached):
            return cached

        rules = self._fetch_rules(robots_url)
        self._cache[robots_url] = rules
        return rules

    def clear_cache(self) -> None:
        """Clear all cached robots.txt policies."""

        self._cache.clear()

    def _is_expired(self, rules: RobotsRules) -> bool:
        return (time.time() - rules.fetched_at) > self.cache_ttl_seconds

    def _fetch_rules(self, robots_url: str) -> RobotsRules:
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            response = self.session.get(
                robots_url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout_seconds,
            )

            if response.status_code == 404:
                parser.parse([])
                log_event(logger, "INFO", "robots.txt not found; allowing crawl", robots_url=robots_url)
                return RobotsRules(robots_url=robots_url, parser=parser, available=True)

            response.raise_for_status()
            parser.parse(response.text.splitlines())
            log_event(logger, "INFO", "Loaded robots.txt", robots_url=robots_url)
            return RobotsRules(robots_url=robots_url, parser=parser, available=True)

        except requests.RequestException as exc:
            parser.parse([])
            log_event(
                logger,
                "WARNING",
                "Could not load robots.txt; allowing crawl by fallback policy",
                robots_url=robots_url,
                error=str(exc),
            )
            return RobotsRules(
                robots_url=robots_url,
                parser=parser,
                available=False,
                error=str(exc),
            )


def build_robots_url(url: str) -> str:
    """Build the robots.txt URL for a page or site URL."""

    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    return urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))


_default_handler: RobotsHandler | None = None


def get_default_robots_handler() -> RobotsHandler:
    """Return a process-wide robots handler for simple module-level callers."""

    global _default_handler
    if _default_handler is None:
        _default_handler = RobotsHandler()
    return _default_handler


def is_allowed_by_robots(url: str) -> bool:
    """Convenience wrapper used by legacy crawler code."""

    return get_default_robots_handler().can_fetch(url)
