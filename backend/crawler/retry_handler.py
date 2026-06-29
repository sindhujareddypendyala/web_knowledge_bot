"""
Retry utilities for the Website Knowledge Module.

Purpose:
    Provides reusable retry behavior for network-bound crawler operations such
    as page fetches, sitemap reads, robots.txt loading, and broken-link checks.

How it connects:
    Sync and async crawlers can wrap transient operations with `RetryHandler`
    instead of duplicating retry loops. The handler logs each attempt, applies
    exponential backoff with jitter, and raises `FetchError` only after all
    configured attempts are exhausted.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

import requests

from config import RETRY_ATTEMPTS, RETRY_BACKOFF_SECONDS
from utils.exceptions import FetchError
from utils.logger import get_logger, log_event

logger = get_logger(__name__)

T = TypeVar("T")


DEFAULT_RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})
DEFAULT_RETRYABLE_EXCEPTIONS = (
    requests.Timeout,
    requests.ConnectionError,
    requests.HTTPError,
)


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """Configuration for retrying transient crawler failures."""

    max_attempts: int = RETRY_ATTEMPTS
    base_delay_seconds: float = RETRY_BACKOFF_SECONDS
    max_delay_seconds: float = 30.0
    jitter_seconds: float = 0.25
    retryable_status_codes: frozenset[int] = DEFAULT_RETRYABLE_STATUS_CODES

    def __post_init__(self) -> None:
        if self.max_attempts < 0:
            raise ValueError("max_attempts must be >= 0")
        if self.base_delay_seconds < 0:
            raise ValueError("base_delay_seconds must be >= 0")
        if self.max_delay_seconds < 0:
            raise ValueError("max_delay_seconds must be >= 0")
        if self.jitter_seconds < 0:
            raise ValueError("jitter_seconds must be >= 0")


class RetryHandler:
    """Retry wrapper for synchronous crawler operations."""

    def __init__(self, config: RetryConfig | None = None) -> None:
        self.config = config or RetryConfig()

    def run(
        self,
        operation: Callable[[], T],
        *,
        url: str,
        operation_name: str = "crawler operation",
    ) -> T:
        """
        Execute `operation`, retrying transient request failures.

        `max_attempts` means retries after the first attempt. For example,
        `max_attempts=3` allows up to four total tries.
        """

        total_tries = self.config.max_attempts + 1
        last_error: Exception | None = None

        for attempt in range(1, total_tries + 1):
            try:
                result = operation()
                self._raise_for_retryable_response(result)
                return result
            except Exception as exc:
                if not self._should_retry(exc):
                    raise

                last_error = exc
                if attempt >= total_tries:
                    break

                delay = self._delay_for_attempt(attempt)
                log_event(
                    logger,
                    "WARNING",
                    "Retrying crawler operation after transient failure",
                    operation=operation_name,
                    url=url,
                    attempt=attempt,
                    next_attempt=attempt + 1,
                    max_attempts=self.config.max_attempts,
                    delay_seconds=round(delay, 3),
                    error=str(exc),
                )
                time.sleep(delay)

        raise FetchError(url=url, reason=str(last_error or "unknown retry failure"))

    def _should_retry(self, exc: Exception) -> bool:
        if isinstance(exc, requests.HTTPError):
            response = exc.response
            if response is None:
                return True
            return response.status_code in self.config.retryable_status_codes

        return isinstance(exc, DEFAULT_RETRYABLE_EXCEPTIONS)

    def _raise_for_retryable_response(self, result: T) -> None:
        if not isinstance(result, requests.Response):
            return

        if result.status_code in self.config.retryable_status_codes:
            result.raise_for_status()

    def _delay_for_attempt(self, attempt: int) -> float:
        exponential_delay = self.config.base_delay_seconds * (2 ** (attempt - 1))
        capped_delay = min(exponential_delay, self.config.max_delay_seconds)
        jitter = random.uniform(0, self.config.jitter_seconds) if self.config.jitter_seconds else 0.0
        return capped_delay + jitter


def retry_operation(
    operation: Callable[[], T],
    *,
    url: str,
    operation_name: str = "crawler operation",
    config: RetryConfig | None = None,
) -> T:
    """Convenience function for one-off retry use."""

    return RetryHandler(config=config).run(operation, url=url, operation_name=operation_name)
