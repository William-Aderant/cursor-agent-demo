"""MonitoredUrl model."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedUpdatedMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.change_log import ChangeLog
    from app.models.pdf_version import PDFVersion
    from app.models.state import State


class MonitoredUrl(Base, CreatedUpdatedMixin):
    """Registry of URLs to monitor."""

    __tablename__ = "monitored_urls"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    form_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    revision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    state_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    last_checked: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    state: Mapped["State"] = relationship("State", lazy="joined")
    category: Mapped["Category | None"] = relationship(
        "Category",
        back_populates="monitored_urls",
        lazy="joined",
    )
    pdf_versions: Mapped[list["PDFVersion"]] = relationship(
        "PDFVersion",
        back_populates="monitored_url",
        lazy="selectin",
        order_by="PDFVersion.version_number",
    )
    change_logs: Mapped[list["ChangeLog"]] = relationship(
        "ChangeLog",
        back_populates="monitored_url",
        lazy="selectin",
    )
