"""add range cancellation fields

Revision ID: 0012_add_range_cancellation_fields
Revises: 0011_range_request_need_fields
Create Date: 2026-06-11 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0012_add_range_cancellation_fields"
down_revision: str | None = "0011_range_request_need_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "barcode_ranges",
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "barcode_ranges",
        sa.Column("cancelled_by", sa.Integer(), nullable=True),
    )
    op.add_column(
        "barcode_ranges",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_barcode_ranges_cancelled_by_users"),
        "barcode_ranges",
        "users",
        ["cancelled_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_barcode_ranges_cancelled_by_users"),
        "barcode_ranges",
        type_="foreignkey",
    )
    op.drop_column("barcode_ranges", "cancelled_at")
    op.drop_column("barcode_ranges", "cancelled_by")
    op.drop_column("barcode_ranges", "cancellation_reason")
