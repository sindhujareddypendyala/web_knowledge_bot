"""
Validation and normalization helpers for the Website Knowledge Module.

Purpose:
    Provides reusable validation for URLs, domains, queries, page text,
    collection names, and crawl limits.

How it connects:
    API schemas, crawlers, sitemap loaders, robots.txt handlers, duplicate
    detectors, website managers, and retrievers all use this module to reject
    invalid input early and normalize URLs consistently before indexing.
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import parse_qsl, quote, unquote, urlencode, urljoin, urlparse, urlunparse

from utils.exceptions import InvalidURLError, ValidationError

HTTP_SCHEMES = {"http", "https"}
DEFAULT_PORTS = {"http": 80, "https": 443}
TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "ref",
    "spm",
}

_DOMAIN_REGEX = re.compile(
    r"^(?=.{1,253}$)(?!-)"
    r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
    r"[a-zA-Z]{2,63}$"
)
_LOCALHOST_REGEX = re.compile(r"^(localhost|127(?:\.\d{1,3}){3}|\[?::1\]?)$", re.IGNORECASE)
_COLLECTION_REGEX = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{1,61}[a-zA-Z0-9]$")


@dataclass(frozen=True, slots=True)
class URLValidationResult:
    """Structured result for URL validation without throwing exceptions."""

    is_valid: bool
    normalized_url: str | None = None
    reason: str | None = None


def ensure_url(url: str) -> str:
    """Normalize and return a URL, raising `InvalidURLError` when invalid."""

    result = validate_url(url)
    if not result.is_valid or not result.normalized_url:
        raise InvalidURLError(url)
    return result.normalized_url


def validate_url(url: str, allow_localhost: bool = False) -> URLValidationResult:
    """Validate a URL and return a structured result."""

    if not isinstance(url, str) or not url.strip():
        return URLValidationResult(False, reason="URL must be a non-empty string.")

    try:
        normalized = normalize_url(url)
    except ValueError as exc:
        return URLValidationResult(False, reason=str(exc))

    parsed = urlparse(normalized)
    if parsed.scheme not in HTTP_SCHEMES:
        return URLValidationResult(False, reason="Only http and https URLs are supported.")

    if not parsed.netloc:
        return URLValidationResult(False, reason="URL must include a domain.")

    hostname = parsed.hostname or ""
    if not is_valid_domain(hostname, allow_localhost=allow_localhost):
        return URLValidationResult(False, reason="URL domain is invalid.")

    return URLValidationResult(True, normalized_url=normalized)


def is_valid_url(url: str, allow_localhost: bool = False) -> bool:
    """Return True when a string is a crawlable http(s) URL."""

    return validate_url(url, allow_localhost=allow_localhost).is_valid


def normalize_url(url: str, base_url: str | None = None, strip_tracking: bool = True) -> str:
    """
    Normalize a URL for crawling and duplicate detection.

    Behavior:
        - Adds `https://` when no scheme is present.
        - Resolves relative URLs against `base_url`.
        - Lowercases scheme and host.
        - Removes fragments.
        - Removes default ports.
        - Normalizes repeated path separators and dot segments.
        - Sorts query parameters and drops common tracking parameters.
    """

    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string.")

    raw_url = url.strip()
    if base_url:
        raw_url = urljoin(base_url, raw_url)
    elif "://" not in raw_url:
        raw_url = "https://" + raw_url

    parsed = urlparse(raw_url)
    scheme = parsed.scheme.lower()
    if scheme not in HTTP_SCHEMES:
        raise ValueError("Only http and https URLs are supported.")

    hostname = (parsed.hostname or "").lower().strip(".")
    if not hostname:
        raise ValueError("URL must include a domain.")

    port = parsed.port
    netloc = hostname
    if port and DEFAULT_PORTS.get(scheme) != port:
        netloc = f"{hostname}:{port}"

    path = _normalize_path(parsed.path)
    query = _normalize_query(parsed.query, strip_tracking=strip_tracking)

    return urlunparse((scheme, netloc, path, "", query, ""))


def _normalize_path(path: str) -> str:
    decoded_path = unquote(path or "/")
    normalized = posixpath.normpath(decoded_path)

    if decoded_path.endswith("/") and not normalized.endswith("/"):
        normalized += "/"
    if not normalized.startswith("/"):
        normalized = "/" + normalized
    if normalized == "/.":
        normalized = "/"

    return quote(normalized, safe="/:@-._~!$&'()*+,;=")


def _normalize_query(query: str, strip_tracking: bool = True) -> str:
    if not query:
        return ""

    pairs = []
    for key, value in parse_qsl(query, keep_blank_values=True):
        key_lower = key.lower()
        if strip_tracking and (
            key_lower in TRACKING_QUERY_KEYS
            or any(key_lower.startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES)
        ):
            continue
        pairs.append((key, value))

    return urlencode(sorted(pairs), doseq=True)


def is_valid_domain(domain: str, allow_localhost: bool = False) -> bool:
    """Validate a DNS hostname used for website crawling."""

    if not isinstance(domain, str) or not domain.strip():
        return False

    cleaned = domain.strip().lower().strip(".")
    if allow_localhost and _LOCALHOST_REGEX.match(cleaned):
        return True
    return bool(_DOMAIN_REGEX.match(cleaned))


def is_same_domain(url: str, base_url: str, include_subdomains: bool = False) -> bool:
    """Return True if `url` belongs to the same domain as `base_url`."""

    url_host = (urlparse(normalize_url(url)).hostname or "").lower()
    base_host = (urlparse(normalize_url(base_url)).hostname or "").lower()

    if include_subdomains:
        return url_host == base_host or url_host.endswith("." + base_host)
    return url_host == base_host


def is_http_url(url: str) -> bool:
    """Return True if a URL uses http or https."""

    try:
        return urlparse(normalize_url(url)).scheme in HTTP_SCHEMES
    except ValueError:
        return False


def is_probably_html_url(url: str) -> bool:
    """Filter out common binary/static assets before fetching."""

    static_extensions = {
        ".7z",
        ".avi",
        ".css",
        ".csv",
        ".doc",
        ".docx",
        ".gif",
        ".gz",
        ".ico",
        ".jpeg",
        ".jpg",
        ".js",
        ".json",
        ".mp3",
        ".mp4",
        ".pdf",
        ".png",
        ".ppt",
        ".pptx",
        ".rar",
        ".svg",
        ".tar",
        ".webm",
        ".webp",
        ".xls",
        ".xlsx",
        ".xml",
        ".zip",
    }
    path = urlparse(url).path.lower()
    return not any(path.endswith(extension) for extension in static_extensions)


def is_valid_text(text: str, min_length: int = 20, min_words: int = 3) -> bool:
    """Return True when extracted page text has enough useful content."""

    if not isinstance(text, str):
        return False

    cleaned = " ".join(text.split())
    if len(cleaned) < min_length:
        return False
    return len(cleaned.split()) >= min_words


def validate_query(query: str, min_length: int = 2, max_length: int = 1000) -> str:
    """Validate and normalize a retrieval query, raising on invalid input."""

    if not isinstance(query, str) or not query.strip():
        raise ValidationError("Query must be a non-empty string.")

    normalized = " ".join(query.split())
    if len(normalized) < min_length:
        raise ValidationError(f"Query must be at least {min_length} characters long.")
    if len(normalized) > max_length:
        raise ValidationError(f"Query must be at most {max_length} characters long.")
    return normalized


def is_valid_query(query: str, min_length: int = 2, max_length: int = 1000) -> bool:
    """Basic sanity check for user retrieval queries."""

    try:
        validate_query(query, min_length=min_length, max_length=max_length)
        return True
    except ValidationError:
        return False


def validate_positive_int(value: int, field_name: str, minimum: int = 1, maximum: int | None = None) -> int:
    """Validate positive integer inputs such as `k`, `max_pages`, or `depth`."""

    if not isinstance(value, int):
        raise ValidationError(f"{field_name} must be an integer.")
    if value < minimum:
        raise ValidationError(f"{field_name} must be greater than or equal to {minimum}.")
    if maximum is not None and value > maximum:
        raise ValidationError(f"{field_name} must be less than or equal to {maximum}.")
    return value


def is_valid_collection_name(collection_name: str) -> bool:
    """Validate a ChromaDB collection name."""

    if not isinstance(collection_name, str):
        return False
    return bool(_COLLECTION_REGEX.match(collection_name))


def dedupe_urls(urls: Iterable[str], base_url: str | None = None) -> list[str]:
    """Normalize and de-duplicate URLs while preserving first-seen order."""

    seen: set[str] = set()
    deduped: list[str] = []

    for url in urls:
        try:
            normalized = normalize_url(url, base_url=base_url)
        except ValueError:
            continue

        if normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)

    return deduped
