"""ScheduleConfig model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ScheduleConfig(Base):
    """User-configurable schedule settings."""

    __tablename__ = "schedule_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cron_expression: Mapped[str] = mapped_column(String(128), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
