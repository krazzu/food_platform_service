"""
Scrape agroserver.ru food suppliers and save results to a CSV file.
The CSV can then be enriched with Ollama and uploaded via import_csv.py.

Usage:
    pip install playwright
    playwright install chromium
    python scripts/scrape_to_csv.py
    python scripts/scrape_to_csv.py --out my_suppliers.csv --pages 20
    python scripts/scrape_to_csv.py --pages 5 --headless false   # watch the browser

Full pipeline example:
    python scripts/scrape_to_csv.py --out raw.csv
    python scripts/import_csv.py raw.csv --enrich --api-url http://your-server:8000
"""
import argparse
import asyncio
import csv
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright, Browser, Page
except ImportError:
    print("Playwright not found. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

BASE_URL = "https://www.agroserver.ru"
CATEGORY_PATH = "/category/produkty-pitaniya/"

CSV_COLUMNS = [
    "name", "category_name", "description",
    "city", "region", "phone", "email", "website",
    "min_order_amount", "min_order_unit", "price_range_description",
    "has_certificates", "certificate_types",
    "delivery_conditions", "delivery_regions",
    "source_url", "source_platform", "notes",
]


async def _text(page: Page, selector: str) -> str:
    try:
        el = await page.query_selector(selector)
        return (await el.inner_text()).strip() if el else ""
    except Exception:
        return ""


async def _attr(page: Page, selector: str, attr: str) -> str:
    try:
        el = await page.query_selector(selector)
        return (await el.get_attribute(attr) or "").strip() if el else ""
    except Exception:
        return ""


async def scrape_supplier_page(browser: Browser, url: str) -> dict | None:
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20_000)

        name = await _text(page, "h1.company-page-name, h1.company_name, h1")
        if not name:
            return None

        description = await _text(
            page, ".company-description, .company_description, .about-company"
        )
        phone = await _text(page, ".phone, .tel, [itemprop='telephone']")
        email = await _text(page, ".email, [itemprop='email']")
        website = await _attr(page, "a.website, a[itemprop='url']", "href")
        region = await _text(page, ".region, .city, [itemprop='addressLocality']")
        category_name = await _text(
            page, ".breadcrumb li:nth-last-child(2), .category-name"
        )

        min_order_amount = ""
        min_order_unit = ""
        if description:
            m = re.search(
                r"мин[ии]?мальн\w*\s+заказ[^—:\d]*[—:\s]*([\d\s]+)\s*(руб|кг|т|уп)",
                description, re.I,
            )
            if m:
                min_order_amount = m.group(1).replace(" ", "")
                min_order_unit = m.group(2)

        return {
            "name": name,
            "category_name": category_name or "Продукты питания",
            "description": description,
            "city": "",
            "region": region,
            "phone": phone,
            "email": email,
            "website": website,
            "min_order_amount": min_order_amount,
            "min_order_unit": min_order_unit,
            "price_range_description": "",
            "has_certificates": "",
            "certificate_types": "",
            "delivery_conditions": "",
            "delivery_regions": "",
            "source_url": url,
            "source_platform": "agroserver",
            "notes": "",
        }
    except Exception as exc:
        logger.warning("Failed to parse %s: %s", url, exc)
        return None
    finally:
        await page.close()


async def run(out_path: Path, max_pages: int, headless: bool) -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context(
            extra_http_headers={"Accept-Language": "ru-RU,ru;q=0.9"},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        rows: list[dict] = []
        seen_urls: set[str] = set()

        for page_num in range(1, max_pages + 1):
            url = BASE_URL + CATEGORY_PATH
            if page_num > 1:
                url += f"?page={page_num}"

            logger.info("Page %d/%d — %s", page_num, max_pages, url)
            nav_page = await context.new_page()
            try:
                await nav_page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                links: list[str] = await nav_page.eval_on_selector_all(
                    "a.company-name, a.company_name, h3.company-name a, .firm-name a",
                    "els => els.map(e => e.href)",
                )
            except Exception as exc:
                logger.warning("Could not load listing page %d: %s", page_num, exc)
                await nav_page.close()
                break
            await nav_page.close()

            if not links:
                logger.info("No supplier links found on page %d — stopping", page_num)
                break

            new_links = [l for l in links if l not in seen_urls]
            seen_urls.update(new_links)
            logger.info("  Found %d supplier links (%d new)", len(links), len(new_links))

            for i, link in enumerate(new_links, 1):
                logger.info("  [%d/%d] %s", i, len(new_links), link)
                data = await scrape_supplier_page(browser, link)
                if data:
                    rows.append(data)
                await asyncio.sleep(0.5)

            logger.info("  Running total: %d suppliers", len(rows))
            await asyncio.sleep(1)

        await browser.close()

    if not rows:
        logger.warning("Nothing scraped — check selectors or site availability")
        return

    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Saved %d suppliers to %s", len(rows), out_path)


def main() -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    parser = argparse.ArgumentParser(description="Scrape agroserver.ru to CSV")
    parser.add_argument("--out", default=f"suppliers_{ts}.csv",
                        help="Output CSV filename (default: suppliers_<timestamp>.csv)")
    parser.add_argument("--pages", type=int, default=10,
                        help="Max listing pages to scrape (default: 10)")
    parser.add_argument("--headless", type=lambda v: v.lower() != "false",
                        default=True, metavar="true|false",
                        help="Run browser headlessly (default: true)")
    args = parser.parse_args()

    out_path = Path(args.out)
    asyncio.run(run(out_path, args.pages, args.headless))


if __name__ == "__main__":
    main()
