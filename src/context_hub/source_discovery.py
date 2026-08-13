from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests

DOWNLOAD_EXTENSIONS = (".csv", ".xlsx", ".xls", ".zip", ".json", ".parquet")


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


def discover_download_links(url: str, timeout: int = 30) -> dict:
    """Descubre archivos enlazados sin asumir que cualquier enlace es un dataset."""
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "ContextHubChile/0.1 (+GitHub Actions)"})
    response.raise_for_status()
    parser = _LinkParser()
    parser.feed(response.text)
    host = urlparse(url).netloc
    links = []
    for href in parser.links:
        absolute = urljoin(url, href)
        parsed = urlparse(absolute)
        path = parsed.path.lower()
        if path.endswith(DOWNLOAD_EXTENSIONS):
            links.append({
                "url": absolute,
                "same_host": parsed.netloc == host,
                "extension": next(ext for ext in DOWNLOAD_EXTENSIONS if path.endswith(ext)),
            })
    unique = {row["url"]: row for row in links}
    return {
        "landing_url": url,
        "http_status": response.status_code,
        "download_links": list(unique.values()),
    }
