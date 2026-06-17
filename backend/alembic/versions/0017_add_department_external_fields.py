"""add department external fields

Revision ID: 0017_add_department_external_fields
Revises: 0016_add_phone_to_users
Create Date: 2026-06-17 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0017_add_department_external_fields"
down_revision: str | None = "0016_add_phone_to_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("departments", sa.Column("external_id", sa.String(length=100), nullable=True))
    op.add_column(
        "departments",
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index(op.f("ix_departments_external_id"), "departments", ["external_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_departments_external_id"), table_name="departments")
    op.drop_column("departments", "is_active")
    op.drop_column("departments", "external_id")
