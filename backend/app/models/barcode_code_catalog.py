from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class BarcodeCodeCatalog(TimestampMixin, Base):
    """Справочник 2-буквенных кодов (направлений) ШПИ.

    Модератор выбирает код отсюда при одобрении заявки. Код один на направление,
    клиенты получают числовые срезы внутри него через счётчик barcode_counters.
    """

    __tablename__ = "barcode_code_catalog"
    __table_args__ = (
        CheckConstraint(
            "status in ('available', 'active', 'reserved', 'blocked', 'deprecated')",
            name="ck_barcode_code_catalog_status_allowed",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="available",
        server_default="available",
        index=True,
        nullable=False,
    )
    # Кому/чему принадлежит направление (описание).
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
