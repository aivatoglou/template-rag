"""Scrape KPN vacancies via sitemap + JSON-LD."""

import re
import json

import httpx
from bs4 import BeautifulSoup

SITEMAP = "https://jobs.kpn.com/sitemap.vacancy.xml"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; KPNBot/1.0)"}


def scrape_vacancies() -> list[dict]:
    # Caps the number of scraped documents at 10 to speed up ingestion and avoid embedding rate limits.
    urls = re.findall(r"<loc>(https://jobs\.kpn\.com/vacature/[^<]+)</loc>",
                      httpx.get(SITEMAP, headers=HEADERS, timeout=15).text)[:10]
    docs = []
    for url in urls:
        try:
            html = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=15).text
            for raw in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
                job = json.loads(raw)
                if job.get("@type") == "JobPosting":
                    body = BeautifulSoup(job["description"], "lxml").get_text(separator="\n", strip=True)
                    docs.append({"title": job["title"], "url": url, "body": body, "source": "vacancies"})
                    break
        except Exception as exc:
            print(f"[vacancies] skip {url}: {exc}")

    print(f"[vacancies] scraped {len(docs)} vacancies")
    return docs
