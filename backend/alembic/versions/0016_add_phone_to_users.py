"""add phone to users

Revision ID: 0016_add_phone_to_users
Revises: 0015_prepare_users_for_external_auth
Create Date: 2026-06-16 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0016_add_phone_to_users"
down_revision: str | None = "0015_prepare_users_for_external_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "phone")
