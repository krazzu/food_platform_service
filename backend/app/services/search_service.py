"""
Structured search via SQLAlchemy + semantic search via Qdrant, merged and ranked.
"""
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.supplier import Supplier, Category
from ..schemas.supplier import SupplierSearchResult, SupplierOut
from . import vector_service


async def structured_search(
    db: AsyncSession,
    query: str = "",
    category: str | None = None,
    region: str | None = None,
    max_min_order: float | None = None,
    has_certificates: bool | None = None,
    limit: int = 50,
) -> list[Supplier]:
    q = select(Supplier).options(selectinload(Supplier.category))

    if query:
        like = f"%{query}%"
        q = q.where(or_(
            Supplier.name.ilike(like),
            Supplier.description.ilike(like),
        ))

    if category:
        q = q.join(Supplier.category).where(Category.name.ilike(f"%{category}%"))

    if region:
        q = q.where(or_(
            Supplier.region.ilike(f"%{region}%"),
            Supplier.city.ilike(f"%{region}%"),
        ))

    if max_min_order is not None:
        q = q.where(or_(
            Supplier.min_order_amount == None,  # noqa: E711
            Supplier.min_order_amount <= max_min_order,
        ))

    if has_certificates is not None:
        q = q.where(Supplier.has_certificates == has_certificates)

    result = await db.execute(q.limit(limit))
    return result.scalars().all()


async def merged_search(
    db: AsyncSession,
    query: str,
    category: str | None = None,
    region: str | None = None,
    max_min_order: float | None = None,
    has_certificates: bool | None = None,
    limit: int = 20,
) -> list[SupplierSearchResult]:
    """
    Combine structured + semantic search.
    Semantic scores are used as the primary ranking signal;
    structured matches that didn't appear semantically are appended.
    """
    # 1. Semantic search — returns (id, score) sorted by score desc
    semantic_hits: dict[int, float] = {}
    try:
        for supplier_id, score in vector_service.semantic_search(query, limit=limit * 2):
            semantic_hits[supplier_id] = score
    except Exception:
        pass  # Qdrant might be empty on first boot; fall back to structured only

    # 2. Structured search — always run to apply hard filters
    structured_hits = await structured_search(
        db,
        query=query if not semantic_hits else "",
        category=category,
        region=region,
        max_min_order=max_min_order,
        has_certificates=has_certificates,
        limit=limit * 3,
    )

    # 3. Build supplier id → Supplier map from structured results
    structured_map: dict[int, Supplier] = {s.id: s for s in structured_hits}

    # 4. If filters applied, restrict semantic hits to those passing filters
    if any([category, region, max_min_order is not None, has_certificates is not None]):
        allowed_ids = set(structured_map.keys())
        semantic_hits = {sid: score for sid, score in semantic_hits.items() if sid in allowed_ids}

    # 5. Fetch any supplier_ids from semantic that aren't in structured_map
    missing_ids = set(semantic_hits.keys()) - set(structured_map.keys())
    if missing_ids:
        extra_result = await db.execute(
            select(Supplier)
            .options(selectinload(Supplier.category))
            .where(Supplier.id.in_(missing_ids))
        )
        for s in extra_result.scalars().all():
            structured_map[s.id] = s

    # 6. Score and rank
    results: list[SupplierSearchResult] = []
    seen: set[int] = set()

    for supplier_id, score in sorted(semantic_hits.items(), key=lambda x: -x[1]):
        if supplier_id in seen:
            continue
        seen.add(supplier_id)
        supplier = structured_map.get(supplier_id)
        if supplier:
            results.append(SupplierSearchResult(
                supplier=SupplierOut.model_validate(supplier),
                score=round(score, 4),
            ))

    for supplier in structured_hits:
        if supplier.id in seen:
            continue
        seen.add(supplier.id)
        results.append(SupplierSearchResult(
            supplier=SupplierOut.model_validate(supplier),
            score=0.5,
        ))

    return results[:limit]
