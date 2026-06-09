"""add B2B fields to suppliers

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ADD COLUMN IF NOT EXISTS — safe if columns already exist (e.g. fresh DB from 0001)
    new_cols = [
        ("inn",           "VARCHAR(12)"),
        ("legal_name",    "VARCHAR(512)"),
        ("verified",      "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("rating",        "FLOAT"),
        ("payment_terms", "VARCHAR(256)"),
        ("works_with_nds","BOOLEAN"),
    ]
    for name, typedef in new_cols:
        op.execute(
            f"ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS {name} {typedef}"
        )

    # Indexes for the new columns (safe to run after columns are guaranteed to exist)
    _idx = "CREATE INDEX IF NOT EXISTS"
    op.execute(f"{_idx} ix_suppliers_verified ON suppliers (verified)")
    op.execute(f"{_idx} ix_suppliers_inn ON suppliers (inn)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_suppliers_inn")
    op.execute("DROP INDEX IF EXISTS ix_suppliers_verified")
    for col in ("works_with_nds", "payment_terms", "rating",
                "verified", "legal_name", "inn"):
        op.execute(f"ALTER TABLE suppliers DROP COLUMN IF EXISTS {col}")
