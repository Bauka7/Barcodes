"""add clients and ranges

Revision ID: 0006_add_clients_and_ranges
Revises: 0005_add_auth_and_audit
Create Date: 2026-06-09 13:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0006_add_clients_and_ranges"
down_revision: str | None = "0005_add_auth_and_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("contact_person", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clients")),
    )
    op.create_index(op.f("ix_clients_name"), "clients", ["name"], unique=True)

    op.create_table(
        "range_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("package_type", sa.String(length=20), nullable=False),
        sa.Column("requested_quantity", sa.Integer(), nullable=False),
        sa.Column("request_type", sa.String(length=100), server_default="issue_range", nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("handled_by", sa.Integer(), nullable=True),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status in ('pending', 'approved', 'rejected', 'cancelled')",
            name=op.f("ck_range_requests_status_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["clients.id"],
            name=op.f("fk_range_requests_client_id_clients"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name=op.f("fk_range_requests_department_id_departments"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["handled_by"],
            ["users.id"],
            name=op.f("fk_range_requests_handled_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["requester_id"],
            ["users.id"],
            name=op.f("fk_range_requests_requester_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_range_requests")),
    )
    op.create_index(op.f("ix_range_requests_client_id"), "range_requests", ["client_id"], unique=False)
    op.create_index(op.f("ix_range_requests_department_id"), "range_requests", ["department_id"], unique=False)
    op.create_index(op.f("ix_range_requests_handled_by"), "range_requests", ["handled_by"], unique=False)
    op.create_index(op.f("ix_range_requests_package_type"), "range_requests", ["package_type"], unique=False)
    op.create_index(op.f("ix_range_requests_requester_id"), "range_requests", ["requester_id"], unique=False)
    op.create_index(op.f("ix_range_requests_status"), "range_requests", ["status"], unique=False)

    op.create_table(
        "barcode_ranges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("package_type", sa.String(length=20), nullable=False),
        sa.Column("start_number", sa.Integer(), nullable=False),
        sa.Column("end_number", sa.Integer(), nullable=False),
        sa.Column("current_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("issued_to_client_id", sa.Integer(), nullable=True),
        sa.Column("issued_to_department_id", sa.Integer(), nullable=True),
        sa.Column("request_id", sa.Integer(), nullable=True),
        sa.Column("issued_by", sa.Integer(), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "current_number >= start_number and current_number <= end_number",
            name=op.f("ck_barcode_ranges_current_number_inside_range"),
        ),
        sa.CheckConstraint(
            "end_number >= start_number",
            name=op.f("ck_barcode_ranges_end_number_gte_start_number"),
        ),
        sa.CheckConstraint(
            "status in ('active', 'exhausted', 'expired', 'cancelled')",
            name=op.f("ck_barcode_ranges_status_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["issued_by"],
            ["users.id"],
            name=op.f("fk_barcode_ranges_issued_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["issued_to_client_id"],
            ["clients.id"],
            name=op.f("fk_barcode_ranges_issued_to_client_id_clients"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["issued_to_department_id"],
            ["departments.id"],
            name=op.f("fk_barcode_ranges_issued_to_department_id_departments"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["range_requests.id"],
            name=op.f("fk_barcode_ranges_request_id_range_requests"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_barcode_ranges")),
    )
    op.create_index(op.f("ix_barcode_ranges_issued_by"), "barcode_ranges", ["issued_by"], unique=False)
    op.create_index(op.f("ix_barcode_ranges_issued_to_client_id"), "barcode_ranges", ["issued_to_client_id"], unique=False)
    op.create_index(op.f("ix_barcode_ranges_issued_to_department_id"), "barcode_ranges", ["issued_to_department_id"], unique=False)
    op.create_index(op.f("ix_barcode_ranges_package_type"), "barcode_ranges", ["package_type"], unique=False)
    op.create_index(op.f("ix_barcode_ranges_request_id"), "barcode_ranges", ["request_id"], unique=False)
    op.create_index(op.f("ix_barcode_ranges_status"), "barcode_ranges", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_barcode_ranges_status"), table_name="barcode_ranges")
    op.drop_index(op.f("ix_barcode_ranges_request_id"), table_name="barcode_ranges")
    op.drop_index(op.f("ix_barcode_ranges_package_type"), table_name="barcode_ranges")
    op.drop_index(op.f("ix_barcode_ranges_issued_to_department_id"), table_name="barcode_ranges")
    op.drop_index(op.f("ix_barcode_ranges_issued_to_client_id"), table_name="barcode_ranges")
    op.drop_index(op.f("ix_barcode_ranges_issued_by"), table_name="barcode_ranges")
    op.drop_table("barcode_ranges")

    op.drop_index(op.f("ix_range_requests_status"), table_name="range_requests")
    op.drop_index(op.f("ix_range_requests_requester_id"), table_name="range_requests")
    op.drop_index(op.f("ix_range_requests_package_type"), table_name="range_requests")
    op.drop_index(op.f("ix_range_requests_handled_by"), table_name="range_requests")
    op.drop_index(op.f("ix_range_requests_department_id"), table_name="range_requests")
    op.drop_index(op.f("ix_range_requests_client_id"), table_name="range_requests")
    op.drop_table("range_requests")

    op.drop_index(op.f("ix_clients_name"), table_name="clients")
    op.drop_table("clients")
