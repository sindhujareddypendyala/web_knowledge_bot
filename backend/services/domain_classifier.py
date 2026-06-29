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
            # Broad technical concept fallback rule
            (
                re.compile(
                    r"\b(ai|ml|genai|artificial\s+intelligence|machine\s+learning|deep\s+learning|"
                    r"langchain|llama|rag|embedding|llm|nlp|neural\s+network|"
                    r"backend|frontend|server|client|api|rest|graphql|grpc|http|"
                    r"sdk|auth|login|signin|signup|credential|token|jwt|oauth|authenticate|authentication|authorize|"
                    r"rate\s+limit|throttle|middleware|route|controller|view|template|"
                    r"database|sql|nosql|query|index|schema|migration|orm|"
                    r"code|programming|develop|software|deploy|ci/cd|devops|"
                    r"cloud|gcp|azure|serverless|lambda|"
                    r"npm|pip|maven|gradle|composer|package|dependency|"
                    r"javascript|typescript|java|c\+\+|c\#|ruby|php|go|rust|"
                    r"html|css|vue|angular|svelte|nextjs|nuxt|"
                    r"django|flask|express|spring|rails|laravel|"
                    r"mysql|sqlite|mongodb|redis|elasticsearch|explain|examples?|quick\s+start|guide)\b",
                    re.IGNORECASE,
                ),
                "general",
            ),
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

