from pathlib import Path

import pytest
from openpyxl import load_workbook

from scraper.cli import main
from scraper.fetch import crawl
from scraper.parse import parse_page, parse_price
from scraper.report import write_report

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://books.toscrape.com/catalogue/"


class FakeResponse:
    def __init__(self, url):
        self.url = url
        self.text = (FIXTURES / url.rsplit("/", 1)[-1]).read_text(encoding="utf-8")
        self.encoding = "utf-8"

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self):
        self.requested = []

    def get(self, url, timeout=None):
        self.requested.append(url)
        return FakeResponse(url)


@pytest.mark.parametrize("text,expected", [
    ("£51.77", 51.77),
    ("Â£22.65", 22.65),
    ("£1,024.50", 1024.50),
    ("  £9 ", 9.0),
])
def test_parse_price(text, expected):
    assert parse_price(text) == expected


def test_parse_price_rejects_garbage():
    with pytest.raises(ValueError):
        parse_price("free")


def test_parse_page_extracts_books_and_next_link():
    html = (FIXTURES / "page-1.html").read_text(encoding="utf-8")
    books, next_url = parse_page(html, BASE + "page-1.html")

    assert [b.title for b in books] == [
        "A Light in the Attic", "Tipping the Velvet", "Sapiens: A Brief History of Humankind",
    ]
    first = books[0]
    assert first.price == 51.77
    assert first.rating == 3
    assert first.in_stock is True
    assert first.url == BASE + "a-light-in-the-attic_1000/index.html"
    assert books[2].in_stock is False
    assert next_url == BASE + "page-2.html"


def test_parse_page_skips_malformed_cards_and_stops_at_last_page():
    html = (FIXTURES / "page-2.html").read_text(encoding="utf-8")
    books, next_url = parse_page(html, BASE + "page-2.html")
    assert [b.title for b in books] == ["The Requiem Red"]
    assert next_url is None


def test_crawl_follows_pagination():
    session = FakeSession()
    books = crawl(BASE + "page-1.html", delay=0, session=session)
    assert len(books) == 4
    assert session.requested == [BASE + "page-1.html", BASE + "page-2.html"]


def test_crawl_respects_max_pages():
    session = FakeSession()
    books = crawl(BASE + "page-1.html", max_pages=1, delay=0, session=session)
    assert len(books) == 3
    assert len(session.requested) == 1


def test_report_contents(tmp_path):
    books = crawl(BASE + "page-1.html", delay=0, session=FakeSession())
    out = tmp_path / "books.xlsx"
    summary = write_report(books, out)

    assert summary["count"] == 4
    assert summary["min"].title.startswith("Sapiens")

    wb = load_workbook(out)
    rows = list(wb["Books"].iter_rows(values_only=True))
    assert rows[0] == ("Title", "Price (£)", "Rating", "In stock", "Link")
    # sorted by rating (high first), then price
    assert [r[0] for r in rows[1:]] == [
        "Sapiens: A Brief History of Humankind", "The Requiem Red",
        "A Light in the Attic", "Tipping the Velvet",
    ]
    summary_sheet = {r[0]: r[1] for r in wb["Summary"].iter_rows(values_only=True) if r[0]}
    assert summary_sheet["Books scraped"] == 4
    assert summary_sheet["Average price (£)"] == round((51.77 + 53.74 + 14.23 + 22.65) / 4, 2)


def test_empty_report(tmp_path):
    summary = write_report([], tmp_path / "empty.xlsx")
    assert summary["count"] == 0


def test_cli_filters(tmp_path, monkeypatch):
    monkeypatch.setattr("scraper.fetch.make_session", FakeSession)
    out = tmp_path / "filtered.xlsx"
    main(["--min-rating", "3", "--in-stock", "--delay", "0", "--out", str(out),
          "--start-url", BASE + "page-1.html"])

    titles = [r[0] for r in load_workbook(out)["Books"].iter_rows(min_row=2, values_only=True)]
    assert titles == ["The Requiem Red", "A Light in the Attic"]
