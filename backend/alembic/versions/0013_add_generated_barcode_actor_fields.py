"""add generated barcode actor fields

Revision ID: 0013_add_generated_barcode_actor_fields
Revises: 0012_add_range_cancellation_fields
Create Date: 2026-06-12 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0013_add_generated_barcode_actor_fields"
down_revision: str | None = "0012_add_range_cancellation_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "generated_barcodes",
        sa.Column("generated_by", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "generated_barcodes",
        sa.Column("printed_by", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generated_barcodes", "printed_by")
    op.drop_column("generated_barcodes", "generated_by")
