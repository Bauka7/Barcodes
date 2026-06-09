from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GeneratedBarcode(Base):
    __tablename__ = "generated_barcodes"
    __table_args__ = (
        CheckConstraint(
            "status in ('generated', 'printed', 'used', 'cancelled')",
            name="ck_generated_barcodes_status_allowed",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("generated_batches.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    barcode: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    package_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    range_id: Mapped[int | None] = mapped_column(
        ForeignKey("barcode_ranges.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    printed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    printed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="generated",
        server_default="generated",
        index=True,
        nullable=False,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    used_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    usage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    batch: Mapped["GeneratedBatch"] = relationship(
        "GeneratedBatch",
        back_populates="barcodes",
    )
