"""range request need-based fields

Revision ID: 0011_range_request_need_fields
Revises: 0010_add_barcode_code_catalog
Create Date: 2026-06-11 10:45:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0011_range_request_need_fields"
down_revision: str | None = "0010_add_barcode_code_catalog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("range_requests", sa.Column("purpose", sa.Text(), nullable=True))
    op.add_column(
        "range_requests",
        sa.Column("requested_code", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "range_requests",
        sa.Column("approved_code", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "range_requests",
        sa.Column("decision_notes", sa.Text(), nullable=True),
    )
    # Код больше не обязателен на этапе заявки — его назначает модератор.
    op.alter_column(
        "range_requests",
        "package_type",
        existing_type=sa.String(length=20),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "range_requests",
        "package_type",
        existing_type=sa.String(length=20),
        nullable=False,
    )
    op.drop_column("range_requests", "decision_notes")
    op.drop_column("range_requests", "approved_code")
    op.drop_column("range_requests", "requested_code")
    op.drop_column("range_requests", "purpose")
