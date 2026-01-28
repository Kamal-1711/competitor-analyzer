import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, Enum, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class CompetitorType(str, PyEnum):
    DIRECT = "direct"
    INDIRECT = "indirect"


class Competitor(Base):
    __tablename__ = "competitors"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    
    competitor_type: Mapped[str] = mapped_column(String(20), default="direct")
    
    # Scores (0-100)
    health_score: Mapped[int] = mapped_column(Integer, default=0)
    seo_score: Mapped[int] = mapped_column(Integer, default=0)
    content_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_monitoring: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    technology_stack: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    # Traffic estimates
    estimated_traffic: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    domain_authority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    last_scanned: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    scans: Mapped[List["Scan"]] = relationship("Scan", back_populates="competitor", cascade="all, delete-orphan")
    contents: Mapped[List["Content"]] = relationship("Content", back_populates="competitor", cascade="all, delete-orphan")
    prices: Mapped[List["PriceHistory"]] = relationship("PriceHistory", back_populates="competitor", cascade="all, delete-orphan")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="competitor", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="competitor", cascade="all, delete-orphan")
    seo_analyses: Mapped[List["SeoAnalysis"]] = relationship("SeoAnalysis", back_populates="competitor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Competitor(name='{self.name}', url='{self.url}')>"
