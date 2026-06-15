"""add region code to barcode counters

Revision ID: 0014_add_region_code_to_barcode_counters
Revises: 0013_add_generated_barcode_actor_fields
Create Date: 2026-06-15 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0014_add_region_code_to_barcode_counters"
down_revision: str | None = "0013_add_generated_barcode_actor_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "barcode_counters",
        sa.Column("region_code", sa.String(length=2), nullable=True),
    )
    op.execute(
        """
        UPDATE barcode_counters
        SET region_code = COALESCE(
            (
                SELECT CASE
                    WHEN length(trim(value)) = 2 THEN trim(value)
                    ELSE '01'
                END
                FROM app_settings
                WHERE key = 'obl_code'
                LIMIT 1
            ),
            '01'
        )
        WHERE region_code IS NULL
        """
    )
    op.alter_column(
        "barcode_counters",
        "region_code",
        existing_type=sa.String(length=2),
        nullable=False,
    )
    op.drop_constraint(
        op.f("uq_barcode_counters_package_type"),
        "barcode_counters",
        type_="unique",
    )
    op.create_unique_constraint(
        op.f("uq_barcode_counters_package_type_region_code"),
        "barcode_counters",
        ["package_type", "region_code"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("uq_barcode_counters_package_type_region_code"),
        "barcode_counters",
        type_="unique",
    )
    op.drop_column("barcode_counters", "region_code")
    op.create_unique_constraint(
        op.f("uq_barcode_counters_package_type"),
        "barcode_counters",
        ["package_type"],
    )
