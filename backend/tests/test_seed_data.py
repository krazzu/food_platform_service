"""Tests for seed data loading."""
import pytest

from app.models.supplier import Category, Supplier
from scrapers.seed_data import CATEGORIES, SUPPLIERS, load_seed_data


def test_seed_constants_are_consistent():
    """Every supplier references a category slug that exists in CATEGORIES."""
    valid_slugs = {c["slug"] for c in CATEGORIES}
    for s in SUPPLIERS:
        assert s["category_slug"] in valid_slugs, (
            f"Supplier '{s['name']}' has unknown category_slug '{s['category_slug']}'"
        )


def test_seed_suppliers_have_required_fields():
    required = {"name", "category_slug", "source_platform"}
    for s in SUPPLIERS:
        missing = required - s.keys()
        assert not missing, f"Supplier '{s.get('name')}' missing fields: {missing}"


def test_seed_data_does_not_mutate_source_list(db):
    """load_seed_data must not pop/modify SUPPLIERS dicts."""
    slugs_before = [s["category_slug"] for s in SUPPLIERS]
    load_seed_data(db)
    slugs_after = [s["category_slug"] for s in SUPPLIERS]
    assert slugs_before == slugs_after


def test_load_seed_data_populates_db(db):
    load_seed_data(db)
    assert db.query(Category).count() == len(CATEGORIES)
    assert db.query(Supplier).count() == len(SUPPLIERS)


def test_load_seed_data_is_idempotent(db):
    """Calling twice must not duplicate data."""
    load_seed_data(db)
    load_seed_data(db)
    assert db.query(Supplier).count() == len(SUPPLIERS)


def test_loaded_suppliers_have_categories(db):
    load_seed_data(db)
    without_category = (
        db.query(Supplier).filter(Supplier.category_id.is_(None)).count()
    )
    assert without_category == 0
