"""CycleUrlResult model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.monitored_url import MonitoredUrl
    from app.models.monitoring_cycle import MonitoringCycle


class CycleUrlResult(Base):
    """Per-URL results within a monitoring cycle."""

    __tablename__ = "cycle_url_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cycle_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("monitoring_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("monitored_urls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    change_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    cycle: Mapped["MonitoringCycle"] = relationship(
        "MonitoringCycle",
        back_populates="cycle_url_results",
        lazy="joined",
    )
    monitored_url: Mapped["MonitoredUrl"] = relationship(
        "MonitoredUrl",
        lazy="joined",
    )
