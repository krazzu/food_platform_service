"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # IF NOT EXISTS so this migration is safe on DBs created by create_all
    op.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL NOT NULL,
            name VARCHAR(128) NOT NULL,
            parent_id INTEGER,
            slug VARCHAR(128) NOT NULL,
            CONSTRAINT categories_pkey PRIMARY KEY (id),
            CONSTRAINT categories_name_key UNIQUE (name),
            CONSTRAINT categories_slug_key UNIQUE (slug),
            CONSTRAINT categories_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES categories(id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id SERIAL NOT NULL,
            name VARCHAR(256) NOT NULL,
            description TEXT,
            website VARCHAR(512),
            email VARCHAR(256),
            phone VARCHAR(64),
            city VARCHAR(128),
            region VARCHAR(128),
            delivery_regions JSON,
            category_id INTEGER,
            min_order_amount FLOAT,
            min_order_unit VARCHAR(32),
            price_range_description VARCHAR(256),
            has_certificates BOOLEAN NOT NULL DEFAULT FALSE,
            certificate_types JSON,
            delivery_conditions TEXT,
            source_url VARCHAR(1024),
            source_platform VARCHAR(64),
            notes TEXT,
            inn VARCHAR(12),
            legal_name VARCHAR(512),
            verified BOOLEAN NOT NULL DEFAULT FALSE,
            rating FLOAT,
            payment_terms VARCHAR(256),
            works_with_nds BOOLEAN,
            scraped_at TIMESTAMPTZ,
            is_stale BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            CONSTRAINT suppliers_pkey PRIMARY KEY (id),
            CONSTRAINT suppliers_category_id_fkey FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    # Indexes only on columns that exist in the ORIGINAL schema (before B2B fields).
    # Indexes on inn/verified columns are in migration 0002, after those columns are added.
    _idx = "CREATE INDEX IF NOT EXISTS"
    op.execute(f"{_idx} ix_suppliers_region ON suppliers (region)")
    op.execute(f"{_idx} ix_suppliers_category_id ON suppliers (category_id)")
    op.execute(f"{_idx} ix_suppliers_is_stale ON suppliers (is_stale)")
    op.execute(f"{_idx} ix_suppliers_city ON suppliers (city)")
    op.execute(f"{_idx} ix_suppliers_min_order ON suppliers (min_order_amount)")
    op.execute(f"{_idx} ix_suppliers_has_certs ON suppliers (has_certificates)")
    op.execute(
        f"{_idx} ix_suppliers_region_category ON suppliers (region, category_id)"
    )
    op.execute(
        f"{_idx} ix_suppliers_fts ON suppliers "
        "USING gin(to_tsvector('russian', name || ' ' || coalesce(description, '')))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_suppliers_fts")
    op.execute("DROP INDEX IF EXISTS ix_suppliers_region_category")
    op.execute("DROP INDEX IF EXISTS ix_suppliers_inn")
    op.execute("DROP INDEX IF EXISTS ix_suppliers_verified")
    op.execute("DROP INDEX IF EXISTS ix_suppliers_has_certs")
    op.execute("DROP INDEX IF EXISTS ix_suppliers_min_order")
    op.execute("DROP INDEX IF EXISTS ix_suppliers_city")
    op.execute("DROP INDEX IF EXISTS ix_suppliers_is_stale")
    op.execute("DROP INDEX IF EXISTS ix_suppliers_category_id")
    op.execute("DROP INDEX IF EXISTS ix_suppliers_region")
    op.execute("DROP TABLE IF EXISTS suppliers")
    op.execute("DROP TABLE IF EXISTS categories")
