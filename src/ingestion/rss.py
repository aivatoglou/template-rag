"""Shared RSS parser. Prefers full-article <content:encoded>, falls back to <description>."""

import xml.etree.ElementTree as ET

import httpx
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}
_CONTENT_ENCODED = "{http://purl.org/rss/1.0/modules/content/}encoded"


def scrape_rss(feed: str, source: str, limit: int = 10) -> list[dict]:
    resp = httpx.get(feed, headers=HEADERS, follow_redirects=True, timeout=15)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)

    docs: list[dict] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or item.findtext("guid") or "").strip()
        # content:encoded carries the full article; description is a short summary.
        html = item.findtext(_CONTENT_ENCODED) or item.findtext("description") or ""
        body = BeautifulSoup(html, "lxml").get_text(separator="\n", strip=True)
        if title and url and body:
            docs.append({"title": title, "url": url, "body": body, "source": source})

    # Cap docs to speed up ingestion and avoid embedding rate limits.
    docs = docs[:limit]
    print(f"[{source}] scraped {len(docs)} articles")
    return docs
