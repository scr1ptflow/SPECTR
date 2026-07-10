# Galnet news scraper — fetches and parses Galnet articles from the Elite
# Dangerous community site (community.elitedangerous.com/galnet).
#
# This is a screen-scraper, not an API client. It downloads the Galnet HTML
# page and uses regex to extract article titles, dates, and body text.
# Fragile to site layout changes.
#
# Data classes:
#   GalnetArticle(title, date, body)
#   GalnetDate(label, url)  — for the date filter buttons
#
# Usage:
#     fetcher = GalnetFetcher()
#     dates = fetcher.get_current_month_dates()
#     articles = fetcher.get_articles("/galnet?date=...")

from __future__ import annotations

import logging
import re
import urllib.request
from dataclasses import dataclass

log = logging.getLogger(__name__)


BASE_URL = "https://community.elitedangerous.com"


@dataclass
class GalnetArticle:
    title: str
    date: str
    body: str


@dataclass
class GalnetDate:
    label: str     # Day number (e.g. "23")
    url: str       # Relative path for that date's page


class GalnetFetcher:
    def __init__(self) -> None:
        self._dates: list[GalnetDate] = []

    def _fetch_text(self, path: str) -> str:
        """Download the HTML page at *path* and return as decoded text."""
        req = urllib.request.Request(
            f"{BASE_URL}{path}",
            headers={"User-Agent": "SPECTR/1.0"},
        )
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, OSError) as exc:
            log.warning("Failed to fetch Galnet %s: %s", path, exc)
            raise

    def _extract_text(self, html: str) -> str:
        """Strip all HTML tags, script blocks, and style blocks from *html*.

        Returns clean plain text with normalised whitespace.
        """
        # Remove <script>...</script> blocks
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        # Remove <style>...</style> blocks
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        # Replace remaining tags with newlines
        text = re.sub(r"<[^>]+>", "\n", text)
        # Collapse multiple newlines
        text = re.sub(r"\n+", "\n", text)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)

    def get_current_month_dates(self) -> list[GalnetDate]:
        """Scrape the Galnet index page for available date filters.

        Returns a list of GalnetDate objects — one per day that has articles.
        """
        html = self._fetch_text("/galnet")
        dates: list[GalnetDate] = []
        m = re.search(
            r'<div class="dateList galnetLinkBoxContainer"[^>]*>(.*?)</div>\s*</div>',
            html, re.DOTALL,
        )
        if m:
            for link in re.finditer(r'href="([^"]+)"[^>]*>(\d+)', m.group(1)):
                dates.append(GalnetDate(label=link.group(2), url=link.group(1)))
        self._dates = dates
        return dates

    def get_articles(self, path: str = "/galnet") -> list[GalnetArticle]:
        """Scrape the Galnet page at *path* and extract all articles.

        Each article is identified by its <h3> tag with class
        "hiLite galnetNewsArticleTitle". Title, date, and body are
        extracted from the surrounding HTML.
        """
        html = self._fetch_text(path)

        # Locate the right-content column (main article area)
        m = re.search(r'<div class="col-md-9 right-content">(.*)', html, re.DOTALL)
        if not m:
            return []
        content_html = m.group(1)

        articles: list[GalnetArticle] = []
        # Match from one article title to the next (or end of content)
        for article_html in re.finditer(
            r'<h3[^>]*class="[^"]*hiLite galnetNewsArticleTitle[^"]*"[^>]*>.*?</h3>'
            r'\s*(.*?)(?=<h3[^>]*class="[^"]*hiLite galnetNewsArticleTitle|\Z)',
            content_html, re.DOTALL,
        ):
            full = article_html.group(0)
            title_m = re.search(r'<h3[^>]*>.*?<a[^>]*>(.*?)</a>', full, re.DOTALL)
            title = self._extract_text(title_m.group(1)).strip() if title_m else ""

            date_m = re.search(
                r"(\d{2} (?:JAN|FEB|MAR|APR|MAY|JUN|"
                r"JUL|AUG|SEP|OCT|NOV|DEC) \d{4})",
                full,
            )
            date = date_m.group(1) if date_m else ""

            body_text = self._extract_text(full)
            body_lines = body_text.split("\n")
            filtered = [l for l in body_lines if l and l != title and l != date]
            body = "\n".join(filtered).strip()

            if title:
                articles.append(GalnetArticle(title=title, date=date, body=body))

        return articles
