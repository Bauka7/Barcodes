"""add region code to barcode ranges

Revision ID: 0020_add_region_code_to_barcode_ranges
Revises: 0019_add_shpi_region_code_to_departments
Create Date: 2026-06-25 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0020_add_region_code_to_barcode_ranges"
down_revision: str | None = "0019_add_shpi_region_code_to_departments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "barcode_ranges",
        sa.Column("region_code", sa.String(length=2), nullable=True),
    )
    op.create_index(
        op.f("ix_barcode_ranges_region_code"),
        "barcode_ranges",
        ["region_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_barcode_ranges_region_code"), table_name="barcode_ranges")
    op.drop_column("barcode_ranges", "region_code")
