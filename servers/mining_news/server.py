"""
Mining News MCP Server - 矿业新闻聚合服务

Fetches real mining news from RSS feeds with proper HTTP headers.
"""

import re
from datetime import datetime, timedelta
from typing import Annotated

import feedparser
import requests
import trafilatura
from fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("mining-news")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MiningDailyAgent/1.0; +mailto:bot@example.com)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

NEWS_SOURCES = [
    "https://www.mining-technology.com/feed/",
    "https://www.mining.com/feed/",
    "https://www.kitco.com/mining/feed/",
    "https://www.australianmining.com.au/feed/",
    "https://www.miningweekly.com/rss/topic/lithium",
    "https://www.spglobal.com/marketintelligence/en/mi/rss/rss-feed.xml",
    "https://www.resourceworld.com/feed/",
]


def _fetch_feed(url: str) -> list[dict]:
    """Fetch and parse an RSS feed with proper HTTP headers."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        results = []
        for entry in feed.entries:
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            pub_date = ""
            if published:
                try:
                    pub_date = datetime(*published[:6]).strftime("%Y-%m-%d %H:%M")
                except (ValueError, OverflowError):
                    pub_date = entry.get("published", entry.get("updated", ""))

            results.append({
                "title": entry.get("title", "").strip(),
                "url": entry.get("link", "").strip(),
                "published_at": pub_date,
                "summary": _clean_summary(entry.get("summary", entry.get("description", ""))),
                "source": url,
            })
        return results
    except Exception:
        return []


def _parse_date(date_str: str) -> datetime | None:
    """Try to parse a date string in various formats."""
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str[:19], fmt)
        except (ValueError, IndexError):
            continue
    return None


def _build_search_terms(query: str) -> list[str]:
    """Extract meaningful search terms from a query."""
    terms = [t.lower() for t in query.lower().split() if len(t) > 1]
    # Filter out common stop words
    stop = {"the", "a", "an", "in", "on", "at", "of", "for", "to", "and", "or", "is"}
    return [t for t in terms if t not in stop]


@mcp.tool()
async def search_news(
    query: Annotated[str, Field(description="Search query, e.g. 'Pilbara lithium'")],
    days: Annotated[int, Field(description="Number of days to look back (max 7)", ge=1, le=7)] = 3,
) -> list[dict]:
    """Search for real mining news articles from RSS feeds."""
    results = []
    cutoff = datetime.now() - timedelta(days=days)
    query_terms = _build_search_terms(query)

    for source_url in NEWS_SOURCES:
        for entry in _fetch_feed(source_url):
            pub_date = _parse_date(entry["published_at"])
            if pub_date and pub_date < cutoff:
                continue

            title_lower = entry["title"].lower()
            summary_lower = entry["summary"].lower()
            combined = f"{title_lower} {summary_lower}"

            # Match if any query term is found
            if not query_terms or any(t in combined for t in query_terms):
                results.append(entry)

    # Deduplicate by URL
    seen = set()
    unique = []
    for r in sorted(results, key=lambda r: r["published_at"], reverse=True):
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    return unique


@mcp.tool()
async def fetch_article(
    url: Annotated[str, Field(description="URL of the article to fetch")],
) -> dict:
    """Fetch and extract the full text content of a real news article from its URL."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return {"title": "", "content": "", "url": url, "error": "Failed to download article"}

        content = trafilatura.extract(downloaded, include_formatting=False)
        metadata = trafilatura.extract(downloaded, output_format="json", include_formatting=False)

        import json

        title_text = ""
        if metadata:
            try:
                meta = json.loads(metadata)
                title_text = meta.get("title", "")
            except json.JSONDecodeError:
                pass

        return {
            "title": title_text,
            "content": content or "",
            "url": url,
        }
    except Exception as e:
        return {"title": "", "content": "", "url": url, "error": str(e)}


def _clean_summary(text: str) -> str:
    """Remove HTML tags and truncate summary."""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:500] if len(clean) > 500 else clean


def main():
    mcp.run()


if __name__ == "__main__":
    main()
