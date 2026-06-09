"""add generation history

Revision ID: 0003_add_generation_history
Revises: 0002_add_department_hierarchy_fields
Create Date: 2026-06-09 10:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_add_generation_history"
down_revision: str | None = "0002_add_department_hierarchy_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "generated_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("package_type", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("first_barcode", sa.String(length=50), nullable=False),
        sa.Column("last_barcode", sa.String(length=50), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("generated_by", sa.String(length=100), nullable=True),
        sa.Column("source", sa.String(length=50), server_default="api", nullable=True),
        sa.Column("status", sa.String(length=50), server_default="generated", nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name=op.f("fk_generated_batches_department_id_departments"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generated_batches")),
    )
    op.create_index(
        op.f("ix_generated_batches_department_id"),
        "generated_batches",
        ["department_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_generated_batches_generated_at"),
        "generated_batches",
        ["generated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_generated_batches_package_type"),
        "generated_batches",
        ["package_type"],
        unique=False,
    )

    op.create_table(
        "generated_barcodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("barcode", sa.String(length=50), nullable=False),
        sa.Column("package_type", sa.String(length=20), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("printed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("printed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["generated_batches.id"],
            name=op.f("fk_generated_barcodes_batch_id_generated_batches"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name=op.f("fk_generated_barcodes_department_id_departments"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generated_barcodes")),
    )
    op.create_index(
        op.f("ix_generated_barcodes_barcode"),
        "generated_barcodes",
        ["barcode"],
        unique=True,
    )
    op.create_index(
        op.f("ix_generated_barcodes_batch_id"),
        "generated_barcodes",
        ["batch_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_generated_barcodes_department_id"),
        "generated_barcodes",
        ["department_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_generated_barcodes_package_type"),
        "generated_barcodes",
        ["package_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_generated_barcodes_package_type"), table_name="generated_barcodes")
    op.drop_index(op.f("ix_generated_barcodes_department_id"), table_name="generated_barcodes")
    op.drop_index(op.f("ix_generated_barcodes_batch_id"), table_name="generated_barcodes")
    op.drop_index(op.f("ix_generated_barcodes_barcode"), table_name="generated_barcodes")
    op.drop_table("generated_barcodes")
    op.drop_index(op.f("ix_generated_batches_package_type"), table_name="generated_batches")
    op.drop_index(op.f("ix_generated_batches_generated_at"), table_name="generated_batches")
    op.drop_index(op.f("ix_generated_batches_department_id"), table_name="generated_batches")
    op.drop_table("generated_batches")
