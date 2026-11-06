# python -m scraper.cli --pages 5 --min-rating 4 --out books.xlsx
import argparse
import logging

from .fetch import START_URL, crawl
from .report import write_report


def main(argv=None):
    p = argparse.ArgumentParser(description="Scrape books.toscrape.com into an Excel report.")
    p.add_argument("--pages", type=int, default=None, help="max pages to crawl (default: all 50)")
    p.add_argument("--min-rating", type=int, default=0, choices=range(0, 6), help="keep books rated at least N stars")
    p.add_argument("--in-stock", action="store_true", help="only books that are in stock")
    p.add_argument("--max-price", type=float, default=None, help="only books at or below this price")
    p.add_argument("--delay", type=float, default=1.0, help="seconds to wait between pages")
    p.add_argument("--out", default="books.xlsx", help="output file")
    p.add_argument("--start-url", default=START_URL, help=argparse.SUPPRESS)
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    books = crawl(args.start_url, max_pages=args.pages, delay=args.delay)
    books = [b for b in books if b.rating >= args.min_rating]
    if args.in_stock:
        books = [b for b in books if b.in_stock]
    if args.max_price is not None:
        books = [b for b in books if b.price <= args.max_price]

    summary = write_report(books, args.out)
    print(f"Saved {summary['count']} books to {args.out}")


if __name__ == "__main__":
    main()
