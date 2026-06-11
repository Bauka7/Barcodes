from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class RangeRequest(TimestampMixin, Base):
    __tablename__ = "range_requests"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending', 'approved', 'rejected', 'cancelled')",
            name="ck_range_requests_status_allowed",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    package_type: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    request_type: Mapped[str] = mapped_column(
        String(100),
        default="issue_range",
        server_default="issue_range",
        nullable=False,
    )
    # Бизнес-описание потребности клиента (тип товара / назначение).
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Желаемый клиентом 2-буквенный код (необязательно; финальное слово за модератором).
    requested_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Код, назначенный модератором при одобрении (источник диапазона/наклейки).
    approved_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Комментарий модератора к решению (одобрение/отклонение).
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        server_default="pending",
        index=True,
        nullable=False,
    )
    handled_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
