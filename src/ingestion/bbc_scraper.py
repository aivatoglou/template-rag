"""Scrape BBC world news from RSS feed."""

from src.ingestion.rss import scrape_rss

FEED = "http://feeds.bbci.co.uk/news/rss.xml"


def scrape_bbc() -> list[dict]:
    return scrape_rss(FEED, source="bbc")
