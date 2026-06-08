import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func

from .database import engine, AsyncSessionLocal, Base
from .models.supplier import Supplier  # noqa: F401 — registers SQLAlchemy metadata
from scrapers.seed_data import load_seed_data
from .api import search, suppliers, admin
from .services import vector_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        count = await db.scalar(select(func.count()).select_from(Supplier))
        if not count:
            logger.info("Loading seed data...")
            await load_seed_data(db)

        try:
            vector_service.ensure_collection()
            indexed = await vector_service.index_all_suppliers(db)
            logger.info("Qdrant index ready: %d suppliers", indexed)
        except Exception as exc:
            logger.warning("Qdrant indexing skipped on startup: %s", exc)

    yield


app = FastAPI(
    title="Food Supplier Search",
    description="Поиск поставщиков продуктов питания с AI-рекомендациями",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(suppliers.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
