"""PDFVersion model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PDFVersion(Base):
    """Stored PDF versions with hashes and optional S3/OpenSearch keys."""

    __tablename__ = "pdf_versions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    url_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("monitored_urls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    pdf_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    text_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    normalized_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    s3_raw_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    s3_normalized_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    s3_extracted_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    s3_text_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    opensearch_document_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    opensearch_indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    opensearch_index_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("url_id", "version_number", name="uq_pdf_versions_url_version"),)

    monitored_url: Mapped["MonitoredUrl"] = relationship(
        "MonitoredUrl",
        back_populates="pdf_versions",
        lazy="joined",
    )
    change_logs: Mapped[list["ChangeLog"]] = relationship(
        "ChangeLog",
        back_populates="version",
        lazy="selectin",
    )
