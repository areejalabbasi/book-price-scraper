import logging
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .parse import parse_page

log = logging.getLogger(__name__)

START_URL = "https://books.toscrape.com/catalogue/page-1.html"


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = "book-price-scraper/1.0 (portfolio project)"
    return session


def crawl(start_url=START_URL, max_pages=None, delay=1.0, session=None):
    session = session or make_session()
    url, page, books = start_url, 0, []

    while url and (max_pages is None or page < max_pages):
        page += 1
        log.info("page %d: %s", page, url)
        resp = session.get(url, timeout=20)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        page_books, url = parse_page(resp.text, resp.url)
        books.extend(page_books)
        if url and delay:
            time.sleep(delay)

    log.info("collected %d books from %d pages", len(books), page)
    return books
