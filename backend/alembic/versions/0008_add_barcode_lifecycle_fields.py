"""add barcode lifecycle fields

Revision ID: 0008_add_barcode_lifecycle_fields
Revises: 0007_add_range_links_to_generated_history
Create Date: 2026-06-09 14:45:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008_add_barcode_lifecycle_fields"
down_revision: str | None = "0007_add_range_links_to_generated_history"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "generated_barcodes",
        sa.Column("status", sa.String(length=50), server_default="generated", nullable=False),
    )
    op.add_column(
        "generated_barcodes",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "generated_barcodes",
        sa.Column("cancelled_by", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "generated_barcodes",
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "generated_barcodes",
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "generated_barcodes",
        sa.Column("used_by", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "generated_barcodes",
        sa.Column("usage_notes", sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        op.f("ck_generated_barcodes_status_allowed"),
        "generated_barcodes",
        "status in ('generated', 'printed', 'used', 'cancelled')",
    )
    op.create_index(
        op.f("ix_generated_barcodes_status"),
        "generated_barcodes",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_generated_barcodes_status"), table_name="generated_barcodes")
    op.drop_constraint(
        op.f("ck_generated_barcodes_status_allowed"),
        "generated_barcodes",
        type_="check",
    )
    op.drop_column("generated_barcodes", "usage_notes")
    op.drop_column("generated_barcodes", "used_by")
    op.drop_column("generated_barcodes", "used_at")
    op.drop_column("generated_barcodes", "cancellation_reason")
    op.drop_column("generated_barcodes", "cancelled_by")
    op.drop_column("generated_barcodes", "cancelled_at")
    op.drop_column("generated_barcodes", "status")
