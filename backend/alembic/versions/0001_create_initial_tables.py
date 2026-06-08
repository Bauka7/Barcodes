"""create initial tables

Revision ID: 0001_create_initial_tables
Revises:
Create Date: 2026-06-08 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_create_initial_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_app_settings")),
        sa.UniqueConstraint("key", name=op.f("uq_app_settings_key")),
    )

    op.create_table(
        "barcode_counters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("package_type", sa.String(length=20), nullable=False),
        sa.Column("current_value", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_barcode_counters")),
        sa.UniqueConstraint(
            "package_type",
            name=op.f("uq_barcode_counters_package_type"),
        ),
    )

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_departments")),
        sa.UniqueConstraint("code", name=op.f("uq_departments_code")),
    )
    op.create_index(op.f("ix_departments_code"), "departments", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_departments_code"), table_name="departments")
    op.drop_table("departments")
    op.drop_table("barcode_counters")
    op.drop_table("app_settings")
