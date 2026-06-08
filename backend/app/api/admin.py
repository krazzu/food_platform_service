"""Admin endpoints: trigger scrape, reindex, mark stale suppliers."""
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models.supplier import Supplier
from ..services import vector_service
from scrapers.agroserver import scrape as run_scrape

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/reindex")
async def reindex(db: AsyncSession = Depends(get_db)):
    """Rebuild Qdrant index from current DB state."""
    count = await vector_service.index_all_suppliers(db)
    return {"indexed": count}


@router.post("/mark-stale")
async def mark_stale(db: AsyncSession = Depends(get_db)):
    """
    Mark scraped suppliers whose scraped_at is older than TTL as stale.
    Seed data (scraped_at=None) is never stale.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.data_ttl_days)
    result = await db.execute(
        update(Supplier)
        .where(Supplier.scraped_at.isnot(None), Supplier.scraped_at < cutoff)
        .values(is_stale=True)
    )
    await db.commit()
    return {"marked_stale": result.rowcount}


@router.post("/scrape/agroserver")
async def scrape_agroserver(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger agroserver.ru scrape in the background."""
    background_tasks.add_task(_run_scrape, run_scrape, db)
    return {"status": "started"}


async def _run_scrape(scrape_fn, db: AsyncSession):
    try:
        count = await scrape_fn(db)
        logger.info("Scrape finished: %d suppliers upserted", count)
        await vector_service.index_all_suppliers(db)
    except Exception as exc:
        logger.error("Scrape failed: %s", exc)
