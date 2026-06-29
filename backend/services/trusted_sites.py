"""
Trusted documentation website registry for technical domains.
"""
from __future__ import annotations

from urllib.parse import urlparse

TRUSTED_SITES: dict[str, list[str]] = {
    "python": ["https://docs.python.org/3/"],
    "fastapi": ["https://fastapi.tiangolo.com/"],
    "docker": ["https://docs.docker.com/"],
    "kubernetes": ["https://kubernetes.io/docs/"],
    "react": ["https://react.dev/"],
    "aws": ["https://docs.aws.amazon.com/"],
    "linux": ["https://wiki.archlinux.org/"],
    "git": ["https://git-scm.com/docs"],
    "postgresql": ["https://www.postgresql.org/docs/"]
}


def is_trusted_url(url: str) -> bool:
    """
    Check if a URL belongs to a trusted documentation site prefix.
    Prevents arbitrary URL injection.
    """
    if not url:
        return False
    url_lower = url.strip().lower()
    for prefixes in TRUSTED_SITES.values():
        for prefix in prefixes:
            if url_lower.startswith(prefix.lower()):
                return True
    return False


def get_trusted_prefixes(domain_key: str) -> list[str]:
    """Get the trusted URL prefixes for a given domain key."""
    return TRUSTED_SITES.get(domain_key.lower(), [])
