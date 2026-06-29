"""
Domain classifier to identify technical domains from queries.
"""
from __future__ import annotations

import re


class DomainClassifier:
    """
    Identifies if a query refers to a known technical domain.
    Initially uses modular keyword matching so it can later be swapped
    with semantic classification or an LLM-based router.
    """

    def __init__(self) -> None:
        # Dictionary mapping regex patterns (case-insensitive) to domain keys
        self.rules: list[tuple[re.Pattern, str]] = [
            (re.compile(r"\bpython\b", re.IGNORECASE), "python"),
            (re.compile(r"\bfastapi\b", re.IGNORECASE), "fastapi"),
            (re.compile(r"\bdocker\b", re.IGNORECASE), "docker"),
            (re.compile(r"\b(kubernetes|k8s)\b", re.IGNORECASE), "kubernetes"),
            (re.compile(r"\breact\b", re.IGNORECASE), "react"),
            (re.compile(r"\b(aws|amazon\s+web\s+services)\b", re.IGNORECASE), "aws"),
            (re.compile(r"\b(linux|wiki\.arch|arch\s+linux)\b", re.IGNORECASE), "linux"),
            (re.compile(r"\bgit\b", re.IGNORECASE), "git"),
            (re.compile(r"\b(postgres|postgresql)\b", re.IGNORECASE), "postgresql"),
        ]

    def classify(self, query: str) -> str | None:
        """
        Classify a query into a technical domain.
        Returns the domain key (e.g., 'fastapi') or None if no match is found.
        """
        if not query:
            return None

        for pattern, domain_key in self.rules:
            if pattern.search(query):
                return domain_key

        return None
