from statistics import mean

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

HEADER_FILL = PatternFill("solid", fgColor="1F5C63")
HEADER_FONT = Font(bold=True, color="FFFFFF")
DEAL_FILL = PatternFill("solid", fgColor="E3F1EE")


def summarize(books):
    if not books:
        return {"count": 0}
    prices = [b.price for b in books]
    by_rating = {}
    for r in range(1, 6):
        group = [b.price for b in books if b.rating == r]
        by_rating[r] = (len(group), round(mean(group), 2) if group else None)
    cheapest = min(books, key=lambda b: b.price)
    priciest = max(books, key=lambda b: b.price)
    return {
        "count": len(books),
        "in_stock": sum(b.in_stock for b in books),
        "avg": round(mean(prices), 2),
        "min": cheapest,
        "max": priciest,
        "by_rating": by_rating,
    }


def write_report(books, path, deal_threshold=20.0):
    wb = Workbook()

    ws = wb.active
    ws.title = "Books"
    headers = ["Title", "Price (£)", "Rating", "In stock", "Link"]
    ws.append(headers)
    for b in sorted(books, key=lambda b: (-b.rating, b.price)):
        ws.append([b.title, b.price, b.rating, "Yes" if b.in_stock else "No", b.url])

    last = ws.max_row
    for c in ws[1]:
        c.fill, c.font = HEADER_FILL, HEADER_FONT
    for row in ws.iter_rows(min_row=2, max_row=last):
        row[1].number_format = "£#,##0.00"
        row[2].alignment = Alignment(horizontal="center")
        row[4].hyperlink = row[4].value
        row[4].style = "Hyperlink"

    if last > 1:
        table = Table(displayName="Books", ref=f"A1:E{last}")
        table.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
        ws.add_table(table)
        ws.conditional_formatting.add(
            f"B2:B{last}", CellIsRule(operator="lessThan", formula=[str(deal_threshold)], fill=DEAL_FILL)
        )

    for col, width in zip("ABCDE", (55, 12, 9, 10, 60)):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"

    # summary sheet
    s = summarize(books)
    sm = wb.create_sheet("Summary")
    sm.column_dimensions["A"].width = 28
    sm.column_dimensions["B"].width = 50
    sm.append(["Books scraped", s["count"]])
    if s["count"]:
        sm.append(["In stock", s["in_stock"]])
        sm.append(["Average price (£)", s["avg"]])
        sm.append(["Cheapest", f"{s['min'].title} (£{s['min'].price:.2f})"])
        sm.append(["Most expensive", f"{s['max'].title} (£{s['max'].price:.2f})"])
        sm.append([])
        sm.append(["Rating", "Books", "Avg price (£)"])
        header_row = sm.max_row
        for r, (n, avg) in s["by_rating"].items():
            sm.append(["★" * r, n, avg])
        for c in sm[header_row]:
            c.fill, c.font = HEADER_FILL, HEADER_FONT
        sm.column_dimensions[get_column_letter(3)].width = 16
    for row in sm.iter_rows(max_row=5):
        row[0].font = Font(bold=True)

    wb.save(path)
    return s
