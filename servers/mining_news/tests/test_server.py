"""
Tests for Mining News MCP Server
"""

import pytest

from servers.mining_news.server import _clean_summary, fetch_article, search_news


@pytest.mark.asyncio
async def test_search_news_basic():
    """Test that search_news returns results in expected format."""
    results = await search_news(query="Pilbara lithium", days=3)
    assert isinstance(results, list)
    for item in results:
        assert "title" in item
        assert "url" in item
        assert "summary" in item
        assert "published_at" in item


@pytest.mark.asyncio
async def test_search_news_max_days():
    """Test search_news with max day range."""
    results = await search_news(query="mining", days=7)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_fetch_article():
    """Test fetch_article handles invalid URLs gracefully."""
    result = await fetch_article(url="https://example.com/not-a-real-page-12345")
    assert "error" in result or "content" in result


def test_clean_summary():
    """Test HTML tag removal from summaries."""
    assert "Hello World" in _clean_summary("<p>Hello <b>World</b></p>")
    assert len(_clean_summary("x" * 1000)) <= 500
