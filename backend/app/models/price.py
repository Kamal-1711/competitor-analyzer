import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class PriceChangeType(str, PyEnum):
    INCREASE = "increase"
    DECREASE = "decrease"
    NEW = "new"
    DISCONTINUED = "discontinued"


class PriceHistory(Base):
    __tablename__ = "price_history"
    
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
    
    product_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    product_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    original_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    discount_percent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    promotion_text: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_on_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    competitor: Mapped["Competitor"] = relationship("Competitor", back_populates="prices")
    
    def __repr__(self):
        return f"<PriceHistory(product='{self.product_name}', price={self.price})>"


class PriceAlert(Base):
    __tablename__ = "price_alerts"
    
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
    
    product_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    old_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    new_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    change_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    change_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    competitor: Mapped["Competitor"] = relationship("Competitor")
    
    def __repr__(self):
        return f"<PriceAlert(type='{self.change_type}', change={self.change_percentage}%)>"
