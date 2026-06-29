"""
Unit and integration tests for the automatic domain-specific retrieval system.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app import app
from services.domain_classifier import DomainClassifier
from services.trusted_sites import is_trusted_url, get_trusted_prefixes
from services.website_search import sitemap_fallback_search


def test_domain_classifier() -> None:
    classifier = DomainClassifier()
    assert classifier.classify("How do I implement authentication in FastAPI?") == "fastapi"
    assert classifier.classify("docker compose up") == "docker"
    assert classifier.classify("how to write a python list comprehension") == "python"
    assert classifier.classify("what is the weather today?") is None


def test_trusted_sites() -> None:
    assert is_trusted_url("https://docs.python.org/3/tutorial/index.html") is True
    assert is_trusted_url("https://fastapi.tiangolo.com/tutorial/security/") is True
    assert is_trusted_url("https://malicious-site.com/docs.python.org/3/") is False
    assert get_trusted_prefixes("fastapi") == ["https://fastapi.tiangolo.com/"]


@patch("crawler.sitemap_loader.SitemapLoader.discover")
def test_sitemap_fallback_search(mock_discover: MagicMock) -> None:
    mock_res = MagicMock()
    mock_res.page_urls = [
        "https://fastapi.tiangolo.com/tutorial/security/",
        "https://fastapi.tiangolo.com/advanced/custom-request-and-route/",
        "https://fastapi.tiangolo.com/tutorial/dependencies/",
    ]
    mock_discover.return_value = mock_res

    results = sitemap_fallback_search("security dependencies", "https://fastapi.tiangolo.com/", k=2)
    assert len(results) <= 2
    assert "https://fastapi.tiangolo.com/tutorial/security/" in results
    assert "https://fastapi.tiangolo.com/tutorial/dependencies/" in results



@patch("config.GOOGLE_API_KEY", "AIza_mock_key")
@patch("routes.chat.search_trusted_pages", new_callable=AsyncMock)
@patch("routes.chat.AsyncWebsiteCrawler.crawl_pages", new_callable=AsyncMock)
@patch("routes.chat.ChatGoogleGenerativeAI")
def test_chat_route_technical(
    mock_llm_class: MagicMock,
    mock_crawl: AsyncMock,
    mock_search: AsyncMock,
) -> None:
    # Setup LLM mock
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock()
    mock_res = MagicMock()
    mock_res.content = "FastAPI mock response"
    mock_llm.ainvoke.return_value = mock_res
    mock_llm_class.return_value = mock_llm

    # Setup search mock
    mock_search.return_value = ["https://fastapi.tiangolo.com/tutorial/security/"]

    # Setup crawler mock (already cached or empty results)
    mock_crawl.return_value = []

    client = TestClient(app)
    response = client.post(
        "/chat",
        json={"message": "How do I implement authentication in FastAPI?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["response"] == "FastAPI mock response"


@patch("config.GOOGLE_API_KEY", "gsk_mock_key")
@patch("routes.chat.search_trusted_pages", new_callable=AsyncMock)
@patch("routes.chat.AsyncWebsiteCrawler.crawl_pages", new_callable=AsyncMock)
@patch("groq.Groq")
def test_chat_route_groq_fallback(
    mock_groq_class: MagicMock,
    mock_crawl: AsyncMock,
    mock_search: AsyncMock,
) -> None:
    # Setup Groq mock
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "FastAPI groq mock response"
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion
    mock_groq_class.return_value = mock_client

    # Setup search mock
    mock_search.return_value = ["https://fastapi.tiangolo.com/tutorial/security/"]

    # Setup crawler mock
    mock_crawl.return_value = []

    client = TestClient(app)
    response = client.post(
        "/chat",
        json={"message": "How do I implement authentication in FastAPI?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["response"] == "FastAPI groq mock response"

