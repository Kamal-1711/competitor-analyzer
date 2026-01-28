import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Product(Base):
    __tablename__ = "products"
    
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
    
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    image_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    competitor: Mapped["Competitor"] = relationship("Competitor", back_populates="products")
    features: Mapped[list["ProductFeature"]] = relationship("ProductFeature", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(name='{self.name}')>"


class ProductFeature(Base):
    __tablename__ = "product_features"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )
    
    feature_name: Mapped[str] = mapped_column(String(255), nullable=False)
    feature_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="features")
    
    def __repr__(self):
        return f"<ProductFeature(name='{self.feature_name}')>"
