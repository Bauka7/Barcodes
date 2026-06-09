"""add range links to generated history

Revision ID: 0007_add_range_links_to_generated_history
Revises: 0006_add_clients_and_ranges
Create Date: 2026-06-09 14:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007_add_range_links_to_generated_history"
down_revision: str | None = "0006_add_clients_and_ranges"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("generated_batches", sa.Column("range_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_generated_batches_range_id_barcode_ranges"),
        "generated_batches",
        "barcode_ranges",
        ["range_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_generated_batches_range_id"),
        "generated_batches",
        ["range_id"],
        unique=False,
    )

    op.add_column("generated_barcodes", sa.Column("range_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_generated_barcodes_range_id_barcode_ranges"),
        "generated_barcodes",
        "barcode_ranges",
        ["range_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_generated_barcodes_range_id"),
        "generated_barcodes",
        ["range_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_generated_barcodes_range_id"), table_name="generated_barcodes")
    op.drop_constraint(
        op.f("fk_generated_barcodes_range_id_barcode_ranges"),
        "generated_barcodes",
        type_="foreignkey",
    )
    op.drop_column("generated_barcodes", "range_id")

    op.drop_index(op.f("ix_generated_batches_range_id"), table_name="generated_batches")
    op.drop_constraint(
        op.f("fk_generated_batches_range_id_barcode_ranges"),
        "generated_batches",
        type_="foreignkey",
    )
    op.drop_column("generated_batches", "range_id")
