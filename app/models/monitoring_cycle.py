"""MonitoringCycle model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cycle_url_result import CycleUrlResult


class MonitoringCycle(Base):
    """Audit trail of monitoring executions."""

    __tablename__ = "monitoring_cycles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_urls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    changes_detected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    cycle_url_results: Mapped[list["CycleUrlResult"]] = relationship(
        "CycleUrlResult",
        back_populates="cycle",
        lazy="selectin",
    )
