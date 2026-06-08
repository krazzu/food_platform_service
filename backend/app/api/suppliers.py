from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.supplier import Supplier, Category
from ..schemas.supplier import (
    SupplierOut, CategoryOut,
    SupplierIn, BulkUpsertRequest, BulkUpsertResponse,
)
from ..services import vector_service

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierOut])
async def list_suppliers(
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Supplier)
        .options(selectinload(Supplier.category))
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    return result.scalars().all()


@router.get("/regions", response_model=list[str])
async def list_regions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Supplier.region).where(Supplier.region.isnot(None)).distinct()
    )
    return sorted({r[0] for r in result.all() if r[0]})


async def _get_or_create_category(
    db: AsyncSession, name: str, cache: dict[str, Category]
) -> Category:
    if name in cache:
        return cache[name]
    result = await db.execute(select(Category).where(Category.name == name))
    cat = result.scalar_one_or_none()
    if not cat:
        slug = name.lower().replace(" ", "_").replace("/", "_")
        cat = Category(name=name, slug=slug)
        db.add(cat)
        await db.flush()
    cache[name] = cat
    return cat


async def _apply_supplier_in(
    supplier: Supplier, data: SupplierIn, db: AsyncSession,
    category_cache: dict[str, Category] | None = None,
) -> None:
    if category_cache is None:
        category_cache = {}
    cat = await _get_or_create_category(db, data.category_name, category_cache) if data.category_name else None
    for field, value in data.model_dump(exclude={"category_name"}).items():
        setattr(supplier, field, value)
    if cat is not None:
        supplier.category = cat
    supplier.scraped_at = datetime.now(timezone.utc)
    supplier.is_stale = False


@router.post("", response_model=SupplierOut, status_code=201)
async def create_supplier(body: SupplierIn, db: AsyncSession = Depends(get_db)):
    """Create a new supplier and add it to the vector index."""
    supplier = Supplier()
    await _apply_supplier_in(supplier, body, db)
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    try:
        vector_service.index_supplier(supplier)
    except Exception:
        pass  # index failures are non-fatal; reindex via /api/admin/reindex
    return supplier


@router.post("/bulk", response_model=BulkUpsertResponse)
async def bulk_upsert_suppliers(body: BulkUpsertRequest, db: AsyncSession = Depends(get_db)):
    """
    Upsert a batch of suppliers.
    Deduplicates by source_url when provided; otherwise always creates new rows.
    After saving, rebuilds the full Qdrant index once.
    """
    created = updated = 0
    category_cache: dict[str, Category] = {}
    for item in body.suppliers:
        existing = None
        if item.source_url:
            result = await db.execute(
                select(Supplier).where(Supplier.source_url == item.source_url)
            )
            existing = result.scalar_one_or_none()

        if existing:
            await _apply_supplier_in(existing, item, db, category_cache)
            updated += 1
        else:
            supplier = Supplier()
            await _apply_supplier_in(supplier, item, db, category_cache)
            db.add(supplier)
            created += 1

    await db.commit()
    try:
        await vector_service.index_all_suppliers(db)
    except Exception:
        pass
    return BulkUpsertResponse(created=created, updated=updated)


@router.get("/{supplier_id}", response_model=SupplierOut)
async def get_supplier(supplier_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Supplier)
        .options(selectinload(Supplier.category))
        .where(Supplier.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier
