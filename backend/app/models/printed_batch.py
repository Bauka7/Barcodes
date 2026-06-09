from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PrintedBatch(Base):
    __tablename__ = "printed_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    generated_batch_id: Mapped[int] = mapped_column(
        ForeignKey("generated_batches.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    printed_count: Mapped[int] = mapped_column(Integer, nullable=False)
    first_barcode: Mapped[str] = mapped_column(String(50), nullable=False)
    last_barcode: Mapped[str] = mapped_column(String(50), nullable=False)
    printed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    printer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="printed",
        server_default="printed",
        nullable=False,
    )
    printed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
