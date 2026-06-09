"""add printed batches

Revision ID: 0004_add_printed_batches
Revises: 0003_add_generation_history
Create Date: 2026-06-09 11:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0004_add_printed_batches"
down_revision: str | None = "0003_add_generation_history"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "printed_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("generated_batch_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("printed_count", sa.Integer(), nullable=False),
        sa.Column("first_barcode", sa.String(length=50), nullable=False),
        sa.Column("last_barcode", sa.String(length=50), nullable=False),
        sa.Column("printed_by", sa.String(length=100), nullable=True),
        sa.Column("printer_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="printed", nullable=False),
        sa.Column(
            "printed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name=op.f("fk_printed_batches_department_id_departments"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["generated_batch_id"],
            ["generated_batches.id"],
            name=op.f("fk_printed_batches_generated_batch_id_generated_batches"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_printed_batches")),
    )
    op.create_index(
        op.f("ix_printed_batches_department_id"),
        "printed_batches",
        ["department_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_printed_batches_generated_batch_id"),
        "printed_batches",
        ["generated_batch_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_printed_batches_printed_at"),
        "printed_batches",
        ["printed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_printed_batches_printed_at"), table_name="printed_batches")
    op.drop_index(op.f("ix_printed_batches_generated_batch_id"), table_name="printed_batches")
    op.drop_index(op.f("ix_printed_batches_department_id"), table_name="printed_batches")
    op.drop_table("printed_batches")
