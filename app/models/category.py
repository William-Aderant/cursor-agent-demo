"""Category model (hierarchical, per state)."""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedUpdatedMixin


class Category(Base, CreatedUpdatedMixin):
    """Hierarchical categories within states."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_category_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    state_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_path: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)

    state: Mapped["State"] = relationship("State", back_populates="categories", lazy="joined")
    parent: Mapped["Category | None"] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children",
        lazy="joined",
    )
    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        lazy="selectin",
    )
    monitored_urls: Mapped[list["MonitoredUrl"]] = relationship(
        "MonitoredUrl",
        back_populates="category",
        lazy="selectin",
    )
