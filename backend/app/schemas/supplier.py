from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class SupplierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    delivery_regions: Optional[list[str]] = None
    category: Optional[CategoryOut] = None
    min_order_amount: Optional[float] = None
    min_order_unit: Optional[str] = None
    price_range_description: Optional[str] = None
    has_certificates: bool = False
    certificate_types: Optional[list[str]] = None
    delivery_conditions: Optional[str] = None
    source_url: Optional[str] = None
    source_platform: Optional[str] = None
    notes: Optional[str] = None
    # B2B extra fields
    inn: Optional[str] = None
    legal_name: Optional[str] = None
    verified: bool = False
    rating: Optional[float] = None
    payment_terms: Optional[str] = None
    works_with_nds: Optional[bool] = None
    # Freshness
    is_stale: bool = False
    scraped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SupplierIn(BaseModel):
    """Input schema for creating / upserting a supplier from an external source."""
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    delivery_regions: Optional[list[str]] = None
    category_name: Optional[str] = None
    min_order_amount: Optional[float] = None
    min_order_unit: Optional[str] = None
    price_range_description: Optional[str] = None
    has_certificates: bool = False
    certificate_types: Optional[list[str]] = None
    delivery_conditions: Optional[str] = None
    source_url: Optional[str] = None
    source_platform: Optional[str] = None
    notes: Optional[str] = None
    # B2B extra fields
    inn: Optional[str] = None
    legal_name: Optional[str] = None
    verified: bool = False
    rating: Optional[float] = None
    payment_terms: Optional[str] = None
    works_with_nds: Optional[bool] = None


class BulkUpsertRequest(BaseModel):
    suppliers: list[SupplierIn]


class BulkUpsertResponse(BaseModel):
    created: int
    updated: int


class SupplierSearchResult(BaseModel):
    supplier: SupplierOut
    score: float = 1.0
    match_reason: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    region: Optional[str] = None
    max_min_order: Optional[float] = None
    has_certificates: Optional[bool] = None
    use_ai: bool = True
    limit: int = 20


class SearchResponse(BaseModel):
    results: list[SupplierSearchResult]
    ai_recommendation: Optional[str] = None
    total: int
    query: str
