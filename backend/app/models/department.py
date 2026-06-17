from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Department(TimestampMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    department_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    full_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    parent: Mapped["Department | None"] = relationship(
        "Department",
        remote_side="Department.id",
        back_populates="children",
    )
    children: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="parent",
    )
