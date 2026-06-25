from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class BarcodeRange(TimestampMixin, Base):
    __tablename__ = "barcode_ranges"
    __table_args__ = (
        CheckConstraint(
            "status in ('active', 'exhausted', 'expired', 'cancelled')",
            name="ck_barcode_ranges_status_allowed",
        ),
        CheckConstraint(
            "end_number >= start_number",
            name="ck_barcode_ranges_end_number_gte_start_number",
        ),
        CheckConstraint(
            "current_number >= start_number and current_number <= end_number",
            name="ck_barcode_ranges_current_number_inside_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    package_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    region_code: Mapped[str | None] = mapped_column(String(2), index=True, nullable=True)
    start_number: Mapped[int] = mapped_column(Integer, nullable=False)
    end_number: Mapped[int] = mapped_column(Integer, nullable=False)
    current_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        server_default="active",
        index=True,
        nullable=False,
    )
    issued_to_client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    issued_to_department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    request_id: Mapped[int | None] = mapped_column(
        ForeignKey("range_requests.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    issued_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Отмена диапазона: причина, кто и когда.
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
