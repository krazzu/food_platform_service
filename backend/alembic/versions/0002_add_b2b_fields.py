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
    # ADD COLUMN IF NOT EXISTS — safe on DBs that already have these columns
    # (e.g. created fresh via 0001 which included them from the start)
    cols = [
        "inn VARCHAR(12)",
        "legal_name VARCHAR(512)",
        "verified BOOLEAN NOT NULL DEFAULT FALSE",
        "rating FLOAT",
        "payment_terms VARCHAR(256)",
        "works_with_nds BOOLEAN",
    ]
    for col in cols:
        name = col.split()[0]
        op.execute(
            f"ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS {col}"
        )
        # Back-fill verified = FALSE for existing rows if column was just added
        if name == "verified":
            op.execute(
                "UPDATE suppliers SET verified = FALSE WHERE verified IS NULL"
            )


def downgrade() -> None:
    for col in ("works_with_nds", "payment_terms", "rating",
                "verified", "legal_name", "inn"):
        op.execute(f"ALTER TABLE suppliers DROP COLUMN IF EXISTS {col}")
