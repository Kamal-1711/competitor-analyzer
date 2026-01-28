import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from app.database import Base


class SeoAnalysis(Base):
    __tablename__ = "seo_analyses"
    
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
    overall_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # On-page SEO
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    title_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title_score: Mapped[int] = mapped_column(Integer, default=0)
    
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_description_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    meta_description_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Headers
    h1_count: Mapped[int] = mapped_column(Integer, default=0)
    h2_count: Mapped[int] = mapped_column(Integer, default=0)
    h3_count: Mapped[int] = mapped_column(Integer, default=0)
    headers_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Content
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    content_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Technical SEO
    has_canonical: Mapped[bool] = mapped_column(Boolean, default=False)
    has_robots_meta: Mapped[bool] = mapped_column(Boolean, default=False)
    has_sitemap: Mapped[bool] = mapped_column(Boolean, default=False)
    has_ssl: Mapped[bool] = mapped_column(Boolean, default=False)
    mobile_friendly: Mapped[bool] = mapped_column(Boolean, default=False)
    technical_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Links
    internal_links: Mapped[int] = mapped_column(Integer, default=0)
    external_links: Mapped[int] = mapped_column(Integer, default=0)
    broken_links: Mapped[int] = mapped_column(Integer, default=0)
    links_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Images
    images_count: Mapped[int] = mapped_column(Integer, default=0)
    images_with_alt: Mapped[int] = mapped_column(Integer, default=0)
    images_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Performance
    load_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Recommendations
    recommendations: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Timestamps
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    competitor: Mapped["Competitor"] = relationship("Competitor", back_populates="seo_analyses")
    
    def __repr__(self):
        return f"<SeoAnalysis(url='{self.url}', score={self.overall_score})>"
