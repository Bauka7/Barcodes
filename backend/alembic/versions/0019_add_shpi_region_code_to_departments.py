"""add shpi region code to departments

Revision ID: 0019_add_shpi_region_code_to_departments
Revises: 0018_add_department_id_to_audit_logs
Create Date: 2026-06-25 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0019_add_shpi_region_code_to_departments"
down_revision: str | None = "0018_add_department_id_to_audit_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "departments",
        sa.Column("shpi_region_code", sa.String(length=2), nullable=True),
    )
    op.create_index(
        op.f("ix_departments_shpi_region_code"),
        "departments",
        ["shpi_region_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_departments_shpi_region_code"), table_name="departments")
    op.drop_column("departments", "shpi_region_code")
