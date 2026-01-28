import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class AlertType(str, PyEnum):
    SEO_CHANGE = "seo_change"
    PRICE_CHANGE = "price_change"
    CONTENT_CHANGE = "content_change"
    NEW_PRODUCT = "new_product"
    PRODUCT_REMOVED = "product_removed"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    COMPETITOR_ADDED = "competitor_added"


class AlertSeverity(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(Base):
    __tablename__ = "alerts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    competitor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=True
    )
    
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="low")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    related_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    alert_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    competitor: Mapped[Optional["Competitor"]] = relationship("Competitor", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(type='{self.alert_type}', title='{self.title}')>"
