"""State (jurisdiction) model."""

from __future__ import annotations

from sqlalchemy import Boolean, BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedUpdatedMixin


class State(Base, CreatedUpdatedMixin):
    """US states/jurisdictions (top-level org)."""

    __tablename__ = "states"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(16), nullable=False, index=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    categories: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="state",
        lazy="selectin",
    )
