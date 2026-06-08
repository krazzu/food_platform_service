"""Tests for structured search logic."""
from unittest.mock import patch

import pytest

from app.models.supplier import Category, Supplier
from app.services.search_service import structured_search, merged_search
from app.schemas.supplier import SupplierSearchResult


# ── structured_search ────────────────────────────────────────────────────────

def test_structured_search_by_name(db, supplier):
    results = structured_search(db, query="МукоМол")
    assert len(results) == 1
    assert results[0].name == "ООО МукоМол"


def test_structured_search_by_description(db, supplier):
    results = structured_search(db, query="пшеничной")
    assert len(results) == 1


def test_structured_search_no_match(db, supplier):
    results = structured_search(db, query="рыба")
    assert results == []


def test_structured_search_by_region(db, supplier):
    results = structured_search(db, region="Воронеж")
    assert len(results) == 1

    results_miss = structured_search(db, region="Новосибирск")
    assert results_miss == []


def test_structured_search_by_category(db, supplier):
    results = structured_search(db, category="Бакалея")
    assert len(results) == 1

    results_miss = structured_search(db, category="Молочная")
    assert results_miss == []


def test_structured_search_max_min_order(db, supplier):
    # supplier.min_order_amount = 50_000
    results = structured_search(db, max_min_order=50000)
    assert len(results) == 1

    results_miss = structured_search(db, max_min_order=10000)
    assert results_miss == []


def test_structured_search_certificates_filter(db, supplier):
    results = structured_search(db, has_certificates=True)
    assert len(results) == 1

    results_miss = structured_search(db, has_certificates=False)
    assert results_miss == []


def test_structured_search_limit(db, category):
    for i in range(5):
        db.add(Supplier(name=f"Поставщик {i}", category=category, source_platform="seed"))
    db.flush()

    results = structured_search(db, limit=3)
    assert len(results) == 3


# ── merged_search ─────────────────────────────────────────────────────────────

def test_merged_search_falls_back_to_structured_when_qdrant_unavailable(db, supplier):
    """If Qdrant is down semantic_search raises — merged_search must still return results."""
    with patch(
        "app.services.search_service.vector_service.semantic_search",
        side_effect=Exception("qdrant unavailable"),
    ):
        results = merged_search(db, query="мука")

    assert len(results) >= 1
    assert any(r.supplier.name == "ООО МукоМол" for r in results)


def test_merged_search_uses_semantic_scores(db, supplier):
    with patch(
        "app.services.search_service.vector_service.semantic_search",
        return_value=[(supplier.id, 0.95)],
    ):
        results = merged_search(db, query="мука")

    assert results[0].score == pytest.approx(0.95)


def test_merged_search_filter_restricts_semantic_hits(db, category):
    """Semantic hits outside the region filter must be excluded."""
    s_moscow = Supplier(
        name="Московский мукомол", category=category,
        region="Москва", source_platform="seed",
    )
    s_spb = Supplier(
        name="Петербургский мукомол", category=category,
        region="Санкт-Петербург", source_platform="seed",
    )
    db.add_all([s_moscow, s_spb])
    db.flush()

    # Semantic returns both, but filter is Moscow only
    with patch(
        "app.services.search_service.vector_service.semantic_search",
        return_value=[(s_moscow.id, 0.9), (s_spb.id, 0.8)],
    ):
        results = merged_search(db, query="мука", region="Москва")

    names = [r.supplier.name for r in results]
    assert "Московский мукомол" in names
    assert "Петербургский мукомол" not in names
