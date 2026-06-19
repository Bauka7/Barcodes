"""add department id to audit logs

Revision ID: 0018_add_department_id_to_audit_logs
Revises: 0017_add_department_external_fields
Create Date: 2026-06-17 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0018_add_department_id_to_audit_logs"
down_revision: str | None = "0017_add_department_external_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("department_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_audit_logs_department_id_departments"),
        "audit_logs",
        "departments",
        ["department_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_audit_logs_department_id"),
        "audit_logs",
        ["department_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_department_id_created_at",
        "audit_logs",
        ["department_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_department_id_created_at", table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_department_id"), table_name="audit_logs")
    op.drop_constraint(
        op.f("fk_audit_logs_department_id_departments"),
        "audit_logs",
        type_="foreignkey",
    )
    op.drop_column("audit_logs", "department_id")
