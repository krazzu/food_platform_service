"""Base class for all Playwright-based scrapers."""
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from playwright.async_api import async_playwright, Browser, Page
from sqlalchemy.orm import Session

from app.models.supplier import Supplier, Category

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    source_platform: str = "unknown"

    async def scrape(self, db: Session) -> int:
        """Run scraper and return number of upserted suppliers."""
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                count = await self._scrape(browser, db)
            finally:
                await browser.close()
        return count

    @abstractmethod
    async def _scrape(self, browser: Browser, db: Session) -> int:
        ...

    def _get_or_create_category(self, db: Session, name: str) -> Category:
        slug = name.lower().replace(" ", "_").replace("/", "_")
        cat = db.query(Category).filter_by(slug=slug).first()
        if not cat:
            cat = Category(name=name, slug=slug)
            db.add(cat)
            db.flush()
        return cat

    def _upsert_supplier(self, db: Session, source_url: str, data: dict) -> Supplier:
        """Create or update a supplier by source_url."""
        supplier = db.query(Supplier).filter_by(source_url=source_url).first()
        if not supplier:
            supplier = Supplier(source_url=source_url, source_platform=self.source_platform)
            db.add(supplier)

        for key, value in data.items():
            setattr(supplier, key, value)

        supplier.scraped_at = datetime.now(timezone.utc)
        supplier.is_stale = False
        db.flush()
        return supplier
