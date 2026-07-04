"""Scrape Ars Technica tech/science news from RSS feed."""

from src.ingestion.rss import scrape_rss

FEED = "https://feeds.arstechnica.com/arstechnica/index"


def scrape_ars() -> list[dict]:
    return scrape_rss(FEED, source="ars")
