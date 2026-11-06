import re
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

from bs4 import BeautifulSoup

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
PRICE_RE = re.compile(r"\d+(?:\.\d+)?")


@dataclass
class Book:
    title: str
    price: float
    rating: int
    in_stock: bool
    url: str

    def as_row(self):
        return asdict(self)


def parse_price(text: str) -> float:
    # sometimes comes back as "Â£51.77" (encoding)
    match = PRICE_RE.search(text.replace(",", ""))
    if not match:
        raise ValueError(f"no price in {text!r}")
    return float(match.group())


def parse_rating(tag) -> int:
    for cls in tag.get("class", []):
        if cls in RATINGS:
            return RATINGS[cls]
    return 0


def parse_page(html: str, page_url: str):
    # returns (books, next_url)
    soup = BeautifulSoup(html, "lxml")
    books = []

    for pod in soup.select("article.product_pod"):
        link = pod.select_one("h3 a")
        price = pod.select_one("p.price_color")
        if link is None or price is None:
            continue
        stock = pod.select_one("p.availability")
        rating = pod.select_one("p.star-rating")
        books.append(Book(
            title=(link.get("title") or link.get_text()).strip(),
            price=parse_price(price.get_text()),
            rating=parse_rating(rating) if rating else 0,
            in_stock=bool(stock and "in stock" in stock.get_text().lower()),
            url=urljoin(page_url, link["href"]),
        ))

    next_link = soup.select_one("li.next a")
    next_url = urljoin(page_url, next_link["href"]) if next_link else None
    return books, next_url
