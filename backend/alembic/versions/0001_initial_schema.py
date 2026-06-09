"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(512), nullable=True),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("region", sa.String(128), nullable=True),
        sa.Column("delivery_regions", sa.JSON(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("min_order_amount", sa.Float(), nullable=True),
        sa.Column("min_order_unit", sa.String(32), nullable=True),
        sa.Column("price_range_description", sa.String(256), nullable=True),
        sa.Column("has_certificates", sa.Boolean(), nullable=False),
        sa.Column("certificate_types", sa.JSON(), nullable=True),
        sa.Column("delivery_conditions", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("source_platform", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # B2B fields
        sa.Column("inn", sa.String(12), nullable=True),
        sa.Column("legal_name", sa.String(512), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("payment_terms", sa.String(256), nullable=True),
        sa.Column("works_with_nds", sa.Boolean(), nullable=True),
        # Freshness
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_stale", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes
    op.create_index("ix_suppliers_region",          "suppliers", ["region"])
    op.create_index("ix_suppliers_category_id",     "suppliers", ["category_id"])
    op.create_index("ix_suppliers_is_stale",        "suppliers", ["is_stale"])
    op.create_index("ix_suppliers_city",            "suppliers", ["city"])
    op.create_index("ix_suppliers_min_order",       "suppliers", ["min_order_amount"])
    op.create_index("ix_suppliers_has_certs",       "suppliers", ["has_certificates"])
    op.create_index("ix_suppliers_verified",        "suppliers", ["verified"])
    op.create_index("ix_suppliers_inn",             "suppliers", ["inn"])
    op.create_index(
        "ix_suppliers_region_category",
        "suppliers",
        ["region", "category_id"],
    )

    # GIN index for Russian full-text search
    op.execute(
        "CREATE INDEX ix_suppliers_fts ON suppliers "
        "USING gin(to_tsvector('russian', name || ' ' || coalesce(description, '')))"
    )


def downgrade() -> None:
    op.drop_index("ix_suppliers_fts", table_name="suppliers")
    op.drop_index("ix_suppliers_region_category", table_name="suppliers")
    op.drop_index("ix_suppliers_inn", table_name="suppliers")
    op.drop_index("ix_suppliers_verified", table_name="suppliers")
    op.drop_index("ix_suppliers_has_certs", table_name="suppliers")
    op.drop_index("ix_suppliers_min_order", table_name="suppliers")
    op.drop_index("ix_suppliers_city", table_name="suppliers")
    op.drop_index("ix_suppliers_is_stale", table_name="suppliers")
    op.drop_index("ix_suppliers_category_id", table_name="suppliers")
    op.drop_index("ix_suppliers_region", table_name="suppliers")
    op.drop_table("suppliers")
    op.drop_table("categories")
