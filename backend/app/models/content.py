import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ContentType(str, PyEnum):
    PAGE = "page"
    BLOG = "blog"
    PRODUCT = "product"
    LANDING = "landing"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class Content(Base):
    __tablename__ = "contents"
    
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
    
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(50), default="page")
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    reading_time_minutes: Mapped[int] = mapped_column(Integer, default=0)
    readability_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    keywords: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Timestamps
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    competitor: Mapped["Competitor"] = relationship("Competitor", back_populates="contents")
    changes: Mapped[list["ContentChange"]] = relationship("ContentChange", back_populates="content", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Content(url='{self.url}', type='{self.content_type}')>"


class ContentChange(Base):
    __tablename__ = "content_changes"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False
    )
    
    change_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    field_changed: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    old_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    new_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    word_count_change: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content: Mapped["Content"] = relationship("Content", back_populates="changes")
    
    def __repr__(self):
        return f"<ContentChange(type='{self.change_type}', field='{self.field_changed}')>"
