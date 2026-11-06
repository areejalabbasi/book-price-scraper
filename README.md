# book-price-scraper

Scrapes all the books from [books.toscrape.com](https://books.toscrape.com) (a practice site for scraping) and saves them to an Excel file.

### What you get
- Title, price, rating, stock and link for every book (it goes through all the pages)
- Excel file with 2 sheets:
  - **Books**: sorted by rating, books under £20 highlighted
  - **Summary**: average price, cheapest / most expensive, count per rating
- Filters: min rating, in stock only, max price
- Retries on errors, and waits between pages so it doesn't hammer the site

### Usage
```
pip install -r requirements.txt

python -m scraper.cli --out books.xlsx
python -m scraper.cli --pages 10 --min-rating 4 --in-stock --max-price 30 --out deals.xlsx
```

### Tests
```
pytest
```
Tests use saved HTML pages in `tests/fixtures`, so they don't need internet.

### Other sites
To scrape a different site, change the selectors in `scraper/parse.py` and `START_URL` in `fetch.py`.
