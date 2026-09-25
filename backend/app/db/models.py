from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass
class Scan(Base):
    __tablename__ = "scans"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    url: Mapped[str] = mapped_column(Text)
    normalized_url: Mapped[str] = mapped_column(Text, index=True)
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)
    requested_by_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped["ScanResult | None"] = relationship(back_populates="scan", uselist=False, cascade="all, delete-orphan")
class ScanResult(Base):
    __tablename__ = "scan_results"
    scan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), primary_key=True)
    tech_stack: Mapped[dict] = mapped_column(JSONB, default=dict)
    api_routes: Mapped[list] = mapped_column(JSONB, default=list)
    seo: Mapped[dict] = mapped_column(JSONB, default=dict)
    performance: Mapped[dict] = mapped_column(JSONB, default=dict)
    raw_headers: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    scan: Mapped[Scan] = relationship(back_populates="result")
