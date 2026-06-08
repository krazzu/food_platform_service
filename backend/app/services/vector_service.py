"""
Qdrant vector search service.
Embeddings: fastembed (ONNX, no torch/CUDA needed) with multilingual MiniLM-L12.
"""
import logging
from typing import Optional

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..models.supplier import Supplier

logger = logging.getLogger(__name__)

_client: Optional[QdrantClient] = None
_model: Optional[TextEmbedding] = None

VECTOR_DIM = 384


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    return _client


def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(settings.embedding_model)
    return _model


def ensure_collection() -> None:
    client = get_client()
    existing = {c.name for c in client.get_collections().collections}
    if settings.qdrant_collection not in existing:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        logger.info("Created Qdrant collection '%s'", settings.qdrant_collection)


def _build_text(supplier) -> str:
    parts = [
        supplier.name,
        supplier.description or "",
        f"Категория: {supplier.category.name}" if supplier.category else "",
        f"Регион: {supplier.region or ''} {supplier.city or ''}",
        supplier.delivery_conditions or "",
        " ".join(supplier.certificate_types or []),
        supplier.price_range_description or "",
    ]
    return " ".join(p for p in parts if p)


def _embed(texts: list[str]) -> list[list[float]]:
    model = get_model()
    return [v.tolist() for v in model.embed(texts)]


def index_supplier(supplier) -> None:
    """Upsert a single supplier into Qdrant."""
    text = _build_text(supplier)
    vector = _embed([text])[0]
    get_client().upsert(
        collection_name=settings.qdrant_collection,
        points=[PointStruct(
            id=supplier.id,
            vector=vector,
            payload={"supplier_id": supplier.id},
        )],
    )


async def index_all_suppliers(db_session: AsyncSession) -> int:
    """Rebuild the full Qdrant index from DB. Returns count indexed."""
    ensure_collection()

    result = await db_session.execute(
        select(Supplier).options(selectinload(Supplier.category))
    )
    suppliers = result.scalars().all()
    if not suppliers:
        return 0

    texts = [_build_text(s) for s in suppliers]
    vectors = _embed(texts)

    points = [
        PointStruct(id=s.id, vector=v, payload={"supplier_id": s.id})
        for s, v in zip(suppliers, vectors)
    ]
    get_client().upsert(collection_name=settings.qdrant_collection, points=points)

    logger.info("Indexed %d suppliers into Qdrant", len(points))
    return len(points)


def semantic_search(query: str, limit: int = 20) -> list[tuple[int, float]]:
    """Return list of (supplier_id, score) sorted by relevance descending."""
    ensure_collection()
    query_vector = _embed([query])[0]
    results = get_client().search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=limit,
        with_payload=True,
    )
    return [(r.payload["supplier_id"], r.score) for r in results]


def remove_supplier(supplier_id: int) -> None:
    get_client().delete(
        collection_name=settings.qdrant_collection,
        points_selector=[supplier_id],
    )
