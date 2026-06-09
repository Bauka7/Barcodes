"""add department hierarchy fields

Revision ID: 0002_add_department_hierarchy_fields
Revises: 0001_create_initial_tables
Create Date: 2026-06-08 16:40:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_department_hierarchy_fields"
down_revision: str | None = "0001_create_initial_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("departments", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.add_column("departments", sa.Column("department_type", sa.String(length=50), nullable=True))
    op.add_column("departments", sa.Column("full_path", sa.String(length=1000), nullable=True))
    op.create_index(op.f("ix_departments_parent_id"), "departments", ["parent_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_departments_parent_id_departments"),
        "departments",
        "departments",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_departments_parent_id_departments"), "departments", type_="foreignkey")
    op.drop_index(op.f("ix_departments_parent_id"), table_name="departments")
    op.drop_column("departments", "full_path")
    op.drop_column("departments", "department_type")
    op.drop_column("departments", "parent_id")
