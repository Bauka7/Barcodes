from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GeneratedBatch(Base):
    __tablename__ = "generated_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    package_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    first_barcode: Mapped[str] = mapped_column(String(50), nullable=False)
    last_barcode: Mapped[str] = mapped_column(String(50), nullable=False)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    generated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(
        String(50),
        default="api",
        server_default="api",
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="generated",
        server_default="generated",
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    barcodes: Mapped[list["GeneratedBarcode"]] = relationship(
        "GeneratedBarcode",
        back_populates="batch",
    )
