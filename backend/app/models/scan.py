import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class ScanStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Scan(Base):
    __tablename__ = "scans"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    competitor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False
    )
    
    status: Mapped[str] = mapped_column(String(20), default="pending")
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    
    # Scan metrics
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0)
    pages_crawled: Mapped[int] = mapped_column(Integer, default=0)
    
    # Task info
    current_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    competitor: Mapped["Competitor"] = relationship("Competitor", back_populates="scans")
    pages: Mapped[list["ScanPage"]] = relationship("ScanPage", back_populates="scan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Scan(id='{self.id}', status='{self.status}')>"


class ScanPage(Base):
    __tablename__ = "scan_pages"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False
    )
    
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    load_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    html_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scan: Mapped["Scan"] = relationship("Scan", back_populates="pages")
    
    def __repr__(self):
        return f"<ScanPage(url='{self.url}')>"
