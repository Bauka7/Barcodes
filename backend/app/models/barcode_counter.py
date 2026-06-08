from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class BarcodeCounter(TimestampMixin, Base):
    __tablename__ = "barcode_counters"

    id: Mapped[int] = mapped_column(primary_key=True)
    package_type: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )
    current_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
