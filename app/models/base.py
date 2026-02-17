"""SQLAlchemy DeclarativeBase and optional mixins for app models."""

from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Timestamp type with server default (UTC)
timestamp = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
]


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class CreatedUpdatedMixin:
    """Mixin adding created_at and updated_at (UTC)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
