"""add client_id to users

Revision ID: 0009_add_client_id_to_users
Revises: 0008_add_barcode_lifecycle_fields
Create Date: 2026-06-11 10:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0009_add_client_id_to_users"
down_revision: str | None = "0008_add_barcode_lifecycle_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Имя организации по умолчанию для бэкафилла существующих client-пользователей.
DEFAULT_CLIENT_NAME = "Демо-организация"


def upgrade() -> None:
    op.add_column("users", sa.Column("client_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_users_client_id_clients"),
        "users",
        "clients",
        ["client_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_users_client_id"), "users", ["client_id"], unique=False)

    # Бэкафилл: привязываем существующих пользователей с ролью client
    # (которые ещё не привязаны) к организации по умолчанию.
    bind = op.get_bind()
    has_orphans = bind.execute(
        sa.text(
            "SELECT 1 FROM users WHERE role = 'client' AND client_id IS NULL LIMIT 1"
        )
    ).first()
    if has_orphans is not None:
        client_id = bind.execute(
            sa.text("SELECT id FROM clients WHERE name = :name"),
            {"name": DEFAULT_CLIENT_NAME},
        ).scalar()
        if client_id is None:
            client_id = bind.execute(
                sa.text(
                    "INSERT INTO clients (name, is_active) "
                    "VALUES (:name, true) RETURNING id"
                ),
                {"name": DEFAULT_CLIENT_NAME},
            ).scalar()
        bind.execute(
            sa.text(
                "UPDATE users SET client_id = :cid "
                "WHERE role = 'client' AND client_id IS NULL"
            ),
            {"cid": client_id},
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_users_client_id"), table_name="users")
    op.drop_constraint(
        op.f("fk_users_client_id_clients"),
        "users",
        type_="foreignkey",
    )
    op.drop_column("users", "client_id")
