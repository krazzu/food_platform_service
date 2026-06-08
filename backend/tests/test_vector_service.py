"""Tests for vector service — Qdrant and embedding calls are mocked."""
from unittest.mock import MagicMock, patch

import pytest

from app.services.vector_service import (
    _build_text,
    index_supplier,
    index_all_suppliers,
    semantic_search,
)


# ── _build_text ───────────────────────────────────────────────────────────────

def test_build_text_includes_name_and_description(supplier):
    text = _build_text(supplier)
    assert "МукоМол" in text
    assert "пшеничной" in text


def test_build_text_includes_category(supplier):
    text = _build_text(supplier)
    assert "Бакалея" in text


def test_build_text_includes_region(supplier):
    text = _build_text(supplier)
    assert "Воронеж" in text


def test_build_text_handles_missing_fields(db):
    from app.models.supplier import Supplier
    minimal = Supplier(name="Тест", source_platform="seed")
    text = _build_text(minimal)
    assert "Тест" in text  # no crash on None fields


# ── index_supplier ────────────────────────────────────────────────────────────

def test_index_supplier_calls_upsert(supplier):
    fake_vector = [0.1] * 384
    mock_client = MagicMock()

    with (
        patch("app.services.vector_service.get_client", return_value=mock_client),
        patch("app.services.vector_service._embed", return_value=[fake_vector]),
    ):
        index_supplier(supplier)

    mock_client.upsert.assert_called_once()
    call_kwargs = mock_client.upsert.call_args.kwargs
    assert call_kwargs["points"][0].id == supplier.id
    assert call_kwargs["points"][0].vector == fake_vector


# ── index_all_suppliers ───────────────────────────────────────────────────────

def test_index_all_suppliers_returns_count(db, supplier):
    fake_vector = [0.0] * 384
    mock_client = MagicMock()

    with (
        patch("app.services.vector_service.get_client", return_value=mock_client),
        patch("app.services.vector_service._embed", return_value=[fake_vector]),
        patch("app.services.vector_service.ensure_collection"),
    ):
        count = index_all_suppliers(db)

    assert count == 1
    mock_client.upsert.assert_called_once()


def test_index_all_suppliers_empty_db(db):
    mock_client = MagicMock()
    with (
        patch("app.services.vector_service.get_client", return_value=mock_client),
        patch("app.services.vector_service.ensure_collection"),
    ):
        count = index_all_suppliers(db)

    assert count == 0
    mock_client.upsert.assert_not_called()


# ── semantic_search ───────────────────────────────────────────────────────────

def test_semantic_search_returns_scored_ids():
    fake_vector = [0.1] * 384
    fake_hit = MagicMock()
    fake_hit.payload = {"supplier_id": 42}
    fake_hit.score = 0.87

    mock_client = MagicMock()
    mock_client.search.return_value = [fake_hit]

    with (
        patch("app.services.vector_service.get_client", return_value=mock_client),
        patch("app.services.vector_service._embed", return_value=[fake_vector]),
        patch("app.services.vector_service.ensure_collection"),
    ):
        results = semantic_search("мука", limit=5)

    assert results == [(42, 0.87)]
    mock_client.search.assert_called_once()


def test_semantic_search_passes_limit():
    fake_vector = [0.0] * 384
    mock_client = MagicMock()
    mock_client.search.return_value = []

    with (
        patch("app.services.vector_service.get_client", return_value=mock_client),
        patch("app.services.vector_service._embed", return_value=[fake_vector]),
        patch("app.services.vector_service.ensure_collection"),
    ):
        semantic_search("тест", limit=7)

    _, kwargs = mock_client.search.call_args
    assert kwargs["limit"] == 7
