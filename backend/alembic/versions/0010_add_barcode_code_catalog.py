"""add barcode code catalog

Revision ID: 0010_add_barcode_code_catalog
Revises: 0009_add_client_id_to_users
Create Date: 2026-06-11 10:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0010_add_barcode_code_catalog"
down_revision: str | None = "0009_add_client_id_to_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "barcode_code_catalog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="available", nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status in ('available', 'active', 'reserved', 'blocked', 'deprecated')",
            name=op.f("ck_barcode_code_catalog_status_allowed"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_barcode_code_catalog")),
    )
    op.create_index(
        op.f("ix_barcode_code_catalog_code"),
        "barcode_code_catalog",
        ["code"],
        unique=True,
    )
    op.create_index(
        op.f("ix_barcode_code_catalog_status"),
        "barcode_code_catalog",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_barcode_code_catalog_status"),
        table_name="barcode_code_catalog",
    )
    op.drop_index(
        op.f("ix_barcode_code_catalog_code"),
        table_name="barcode_code_catalog",
    )
    op.drop_table("barcode_code_catalog")
