"""
Scraper for agroserver.ru — large Russian B2B food supplier directory.
Scrapes the food section page by page.

Usage:
    asyncio.run(AgroserverScraper().scrape(db_session))
"""
import asyncio
import logging
import re

from playwright.async_api import Browser, Page
from sqlalchemy.orm import Session

from .base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.agroserver.ru"
CATEGORY_PATH = "/category/produkty-pitaniya/"
MAX_PAGES = 10  # safety limit per run


class AgroserverScraper(BaseScraper):
    source_platform = "agroserver"

    async def _scrape(self, browser: Browser, db: Session) -> int:
        page = await browser.new_page()
        await page.set_extra_http_headers({"Accept-Language": "ru-RU,ru;q=0.9"})
        count = 0

        for page_num in range(1, MAX_PAGES + 1):
            if page_num == 1:
                url = f"{BASE_URL}{CATEGORY_PATH}"
            else:
                url = f"{BASE_URL}{CATEGORY_PATH}?page={page_num}"

            logger.info("Scraping %s", url)
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            except Exception as exc:
                logger.warning("Failed to load %s: %s", url, exc)
                break

            links = await page.eval_on_selector_all(
                "a.company-name, a.company_name, h3.company-name a, .firm-name a",
                "els => els.map(e => e.href)",
            )
            if not links:
                logger.info("No more supplier links on page %d", page_num)
                break

            for link in links:
                try:
                    data = await self._scrape_supplier_page(browser, link)
                    if data:
                        cat_name = data.pop("category_name", "Прочее")
                        cat = self._get_or_create_category(db, cat_name)
                        data["category_id"] = cat.id
                        self._upsert_supplier(db, link, data)
                        count += 1
                except Exception as exc:
                    logger.warning("Skipping %s: %s", link, exc)

            db.commit()
            await asyncio.sleep(1)

        await page.close()
        return count

    async def _scrape_supplier_page(self, browser: Browser, url: str) -> dict | None:
        page = await browser.new_page()
        try:
            await page.goto(
                url, wait_until="domcontentloaded", timeout=20_000
            )

            name = await self._text(page, "h1.company-page-name, h1.company_name, h1")
            if not name:
                return None

            description = await self._text(
                page,
                ".company-description, .company_description, .about-company",
            )
            phone = await self._text(
                page, ".phone, .tel, [itemprop='telephone']"
            )
            email = await self._text(page, ".email, [itemprop='email']")
            website = await self._attr(
                page, "a.website, a[itemprop='url']", "href"
            )
            region = await self._text(
                page, ".region, .city, [itemprop='addressLocality']"
            )
            category_name = await self._text(
                page,
                ".breadcrumb li:nth-last-child(2), .category-name",
            )

            min_order = None
            min_order_unit = None
            if description:
                pattern = (
                    r"мин[ии]?мальн\w*\s+заказ[^—:\d]*"
                    r"[—:\s]*([\d\s]+)\s*(руб|кг|т|уп)"
                )
                m = re.search(pattern, description, re.I)
                if m:
                    try:
                        min_order = float(m.group(1).replace(" ", ""))
                        min_order_unit = m.group(2)
                    except ValueError:
                        pass

            return {
                "name": name.strip(),
                "description": description,
                "phone": phone,
                "email": email,
                "website": website,
                "region": region,
                "category_name": category_name or "Продукты питания",
                "min_order_amount": min_order,
                "min_order_unit": min_order_unit,
            }
        finally:
            await page.close()

    @staticmethod
    async def _text(page: Page, selector: str) -> str | None:
        try:
            el = await page.query_selector(selector)
            return (await el.inner_text()).strip() if el else None
        except Exception:
            return None

    @staticmethod
    async def _attr(page: Page, selector: str, attr: str) -> str | None:
        try:
            el = await page.query_selector(selector)
            return await el.get_attribute(attr) if el else None
        except Exception:
            return None


async def scrape(db: Session) -> int:
    return await AgroserverScraper().scrape(db)
