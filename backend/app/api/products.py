from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.product import Product, ProductFeature
from app.models.competitor import Competitor

router = APIRouter()


class ProductItem(BaseModel):
    id: UUID
    competitor_id: UUID
    name: str
    url: str
    description: Optional[str]
    category: Optional[str]
    image_url: Optional[str]
    is_available: bool
    is_new: bool
    first_seen: datetime
    last_checked: datetime
    
    class Config:
        from_attributes = True


class ProductDetail(ProductItem):
    features: List[dict]


class FeatureMatrixItem(BaseModel):
    feature_name: str
    values: dict  # competitor_name -> value


@router.get("/{competitor_id}", response_model=List[ProductItem])
async def get_competitor_products(
    competitor_id: UUID,
    category: Optional[str] = None,
    is_available: Optional[bool] = None,
    is_new: Optional[bool] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get products for a competitor."""
    
    query = select(Product).where(Product.competitor_id == competitor_id)
    
    if category:
        query = query.where(Product.category == category)
    
    if is_available is not None:
        query = query.where(Product.is_available == is_available)
    
    if is_new is not None:
        query = query.where(Product.is_new == is_new)
    
    query = query.order_by(Product.last_checked.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{competitor_id}/{product_id}", response_model=ProductDetail)
async def get_product_detail(
    competitor_id: UUID,
    product_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get product details with features."""
    
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.competitor_id == competitor_id
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get features
    features_result = await db.execute(
        select(ProductFeature).where(ProductFeature.product_id == product_id)
    )
    features = features_result.scalars().all()
    
    return ProductDetail(
        id=product.id,
        competitor_id=product.competitor_id,
        name=product.name,
        url=product.url,
        description=product.description,
        category=product.category,
        image_url=product.image_url,
        is_available=product.is_available,
        is_new=product.is_new,
        first_seen=product.first_seen,
        last_checked=product.last_checked,
        features=[
            {
                "name": f.feature_name,
                "value": f.feature_value,
                "category": f.feature_category,
                "is_highlight": f.is_highlight
            }
            for f in features
        ]
    )


@router.get("/compare/features", response_model=List[FeatureMatrixItem])
async def compare_product_features(
    product_names: str,  # Comma-separated product names
    competitor_ids: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Compare features across similar products."""
    
    names = [n.strip() for n in product_names.split(",")]
    
    query = (
        select(ProductFeature, Product, Competitor.name)
        .join(Product)
        .join(Competitor)
        .where(Product.name.in_(names))
    )
    
    if competitor_ids:
        ids = [UUID(id.strip()) for id in competitor_ids.split(",")]
        query = query.where(Product.competitor_id.in_(ids))
    
    result = await db.execute(query)
    
    # Build feature matrix
    feature_matrix = {}
    
    for feature, product, comp_name in result.all():
        if feature.feature_name not in feature_matrix:
            feature_matrix[feature.feature_name] = {}
        
        feature_matrix[feature.feature_name][comp_name] = feature.feature_value
    
    return [
        FeatureMatrixItem(feature_name=name, values=values)
        for name, values in feature_matrix.items()
    ]


@router.get("/new")
async def get_new_products(
    days: int = 7,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get recently discovered products."""
    
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(Product, Competitor.name)
        .join(Competitor)
        .where(Product.first_seen >= since)
        .order_by(Product.first_seen.desc())
        .limit(limit)
    )
    
    products = []
    for product, comp_name in result.all():
        products.append({
            "id": str(product.id),
            "competitor_name": comp_name,
            "name": product.name,
            "url": product.url,
            "category": product.category,
            "image_url": product.image_url,
            "first_seen": product.first_seen
        })
    
    return products


@router.get("/categories")
async def get_product_categories(
    competitor_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all product categories."""
    
    query = select(Product.category).distinct()
    
    if competitor_id:
        query = query.where(Product.competitor_id == competitor_id)
    
    query = query.where(Product.category.isnot(None))
    
    result = await db.execute(query)
    categories = [row[0] for row in result.all()]
    
    return {"categories": categories}
