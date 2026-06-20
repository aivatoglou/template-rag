"""Scrape KPN news from RSS feed."""

import httpx
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

FEED = "https://www.overons.kpn/nieuws/feed/en"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; KPNBot/1.0)"}


def scrape_news() -> list[dict]:
    resp = httpx.get(FEED, headers=HEADERS, follow_redirects=True, timeout=15)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)

    docs: list[dict] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or item.findtext("guid") or "").strip()
        html = item.findtext("description") or ""
        body = BeautifulSoup(html, "lxml").get_text(separator="\n", strip=True)
        if title and url and body:
            docs.append({"title": title, "url": url, "body": body, "source": "news"})

    print(f"[news] scraped {len(docs[:10])} articles")
    # Caps the number of scraped documents at 10 to speed up ingestion and avoid embedding rate limits.
    return docs[:10]
