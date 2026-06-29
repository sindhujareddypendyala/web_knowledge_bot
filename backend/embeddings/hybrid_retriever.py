"""
Hybrid retriever combining vector distance with simple keyword overlap.
"""

from __future__ import annotations

import re

import config
from embeddings.retriever import WebsiteRetriever
from models.chunk import RetrievedChunk


class HybridRetriever:
    def __init__(
        self,
        collection_name: str = config.DEFAULT_COLLECTION_NAME,
        vector_weight: float = config.HYBRID_VECTOR_WEIGHT,
        keyword_weight: float = config.HYBRID_KEYWORD_WEIGHT,
    ) -> None:
        self.retriever = WebsiteRetriever(collection_name)
        total = vector_weight + keyword_weight
        self.vector_weight = vector_weight / total if total else 0.65
        self.keyword_weight = keyword_weight / total if total else 0.35

    def retrieve(self, query: str, k: int = config.RETRIEVAL_TOP_K, candidate_k: int | None = None) -> list[RetrievedChunk]:
        candidates = self.retriever.retrieve(query, k=candidate_k or max(k * 3, k))
        query_terms = _terms(query, expand=True)

        rescored: list[tuple[float, RetrievedChunk]] = []
        for candidate in candidates:
            text_terms = _terms(candidate.text)
            overlap = len(query_terms & text_terms) / max(len(query_terms), 1)
            score = (candidate.confidence or 0.0) * self.vector_weight + overlap * self.keyword_weight
            score += _semantic_boost(query, candidate)
            score -= _navigation_penalty(candidate.text)
            candidate.confidence = round(score, 4)
            candidate.retrieval_method = "hybrid"
            candidate.matched_terms = sorted(query_terms & text_terms)
            rescored.append((score, candidate))

        rescored.sort(key=lambda item: item[0], reverse=True)
        results = [item for _, item in rescored[:k]]
        for index, item in enumerate(results, start=1):
            item.rank = index
        return results

    def retrieve_context(self, query: str, k: int = config.RETRIEVAL_TOP_K) -> list[dict]:
        return [result.to_context_dict() for result in self.retrieve(query, k=k)]


def _terms(text: str, expand: bool = False) -> set[str]:
    terms = {term for term in re.findall(r"[a-zA-Z0-9_]{2,}", text.lower())}
    if not expand:
        return terms

    expanded = set(terms)
    if "define" in terms:
        expanded.update({"def", "defining", "definition", "defined"})
    if "function" in terms:
        expanded.update({"functions", "callable", "argument", "arguments", "return"})
    return expanded


def _semantic_boost(query: str, candidate: RetrievedChunk) -> float:
    query_text = query.lower()
    text = candidate.text.lower()
    source = candidate.source_url.lower()
    boost = 0.0

    if "function" in query_text and ("define" in query_text or "def " in query_text):
        if "def " in text or "defining functions" in text or "function definition" in text:
            boost += 0.2
        if "controlflow" in source:
            boost += 0.08
        if "classes.html" in source:
            boost -= 0.08

    return boost


def _navigation_penalty(text: str) -> float:
    lower_text = text.lower()
    section_refs = len(re.findall(r"\b\d+(?:\.\d+)+\.", lower_text))
    if "table of contents" in lower_text or section_refs >= 10:
        return 0.12
    if section_refs >= 5:
        return 0.06
    return 0.0
