from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.supplier import SearchRequest, SearchResponse
from ..services import search_service

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    results = await search_service.merged_search(
        db=db,
        query=req.query,
        category=req.category,
        region=req.region,
        max_min_order=req.max_min_order,
        has_certificates=req.has_certificates,
        limit=req.limit,
    )

    return SearchResponse(
        results=results,
        ai_recommendation=None,
        total=len(results),
        query=req.query,
    )
