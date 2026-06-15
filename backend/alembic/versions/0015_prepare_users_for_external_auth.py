"""prepare users for external auth

Revision ID: 0015_prepare_users_for_external_auth
Revises: 0014_add_region_code_to_barcode_counters
Create Date: 2026-06-15 00:00:01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0015_prepare_users_for_external_auth"
down_revision: str | None = "0014_add_region_code_to_barcode_counters"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_column("users", "email")
