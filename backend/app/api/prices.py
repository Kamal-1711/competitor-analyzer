from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime, timedelta
from decimal import Decimal

from app.database import get_db
from app.models.price import PriceHistory, PriceAlert, PriceChangeType
from app.models.competitor import Competitor

router = APIRouter()


class PriceItem(BaseModel):
    id: UUID
    competitor_id: UUID
    product_name: str
    product_url: Optional[str]
    price: Decimal
    original_price: Optional[Decimal]
    currency: str
    is_on_sale: bool
    discount_percent: Optional[int]
    promotion_text: Optional[str]
    captured_at: datetime
    
    class Config:
        from_attributes = True


class PriceHistoryPoint(BaseModel):
    date: datetime
    price: Decimal


class PriceChangeAlert(BaseModel):
    id: UUID
    product_name: str
    competitor_name: str
    change_type: PriceChangeType
    old_price: Optional[Decimal]
    new_price: Decimal
    change_percent: Optional[float]
    created_at: datetime


class PriceComparison(BaseModel):
    product_name: str
    prices: dict  # competitor_name -> price


class PriceScanResult(BaseModel):
    new: int
    updated: int
    unchanged: int
    message: str


@router.post("/{competitor_id}/scan", response_model=PriceScanResult)
async def scan_competitor_prices(
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Scan a competitor's website for pricing information."""
    from app.services.crawler import PlaywrightCrawler
    from app.services.price_monitor import PriceMonitor
    from app.models.competitor import Competitor
    
    # Get competitor
    result = await db.execute(
        select(Competitor).where(Competitor.id == competitor_id)
    )
    competitor = result.scalar_one_or_none()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    # Initialize services
    crawler = PlaywrightCrawler()
    price_monitor = PriceMonitor()
    
    total_results = {'new': 0, 'updated': 0, 'unchanged': 0}
    
    try:
        # First try the main URL
        scan_result = await crawler.quick_scan(competitor.url)
        
        if scan_result and scan_result.get('html'):
            results = await price_monitor.process_prices(
                competitor_id, competitor.url, scan_result['html'], db
            )
            total_results['new'] += results.get('new', 0)
            total_results['updated'] += results.get('updated', 0)
            total_results['unchanged'] += results.get('unchanged', 0)
        
        # Also try common pricing page URLs
        pricing_paths = ['/pricing', '/prices', '/plans', '/products', '/services']
        base_url = competitor.url.rstrip('/')
        
        for path in pricing_paths:
            try:
                pricing_url = f"{base_url}{path}"
                scan_result = await crawler.quick_scan(pricing_url)
                
                if scan_result and scan_result.get('html') and scan_result.get('status_code') == 200:
                    results = await price_monitor.process_prices(
                        competitor_id, pricing_url, scan_result['html'], db
                    )
                    total_results['new'] += results.get('new', 0)
                    total_results['updated'] += results.get('updated', 0)
                    total_results['unchanged'] += results.get('unchanged', 0)
            except Exception as e:
                # Skip pages that don't exist
                pass
        
        total_found = total_results['new'] + total_results['updated'] + total_results['unchanged']
        
        if total_found == 0:
            return PriceScanResult(
                new=0,
                updated=0,
                unchanged=0,
                message="No pricing information found. This website may not display public pricing."
            )
        
        return PriceScanResult(
            **total_results,
            message=f"Found {total_found} price(s): {total_results['new']} new, {total_results['updated']} updated"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price scan failed: {str(e)}")


@router.get("/{competitor_id}", response_model=List[PriceItem])
async def get_competitor_prices(
    competitor_id: UUID,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get current prices for a competitor."""
    
    # Get latest price for each product
    subquery = (
        select(
            PriceHistory.product_name,
            func.max(PriceHistory.captured_at).label("latest")
        )
        .where(PriceHistory.competitor_id == competitor_id)
        .group_by(PriceHistory.product_name)
        .subquery()
    )
    
    result = await db.execute(
        select(PriceHistory)
        .join(
            subquery,
            (PriceHistory.product_name == subquery.c.product_name) &
            (PriceHistory.captured_at == subquery.c.latest)
        )
        .where(PriceHistory.competitor_id == competitor_id)
        .limit(limit)
    )
    
    return result.scalars().all()


@router.get("/{competitor_id}/history")
async def get_price_history(
    competitor_id: UUID,
    product_name: str,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get price history for a specific product."""
    
    since = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(PriceHistory)
        .where(
            PriceHistory.competitor_id == competitor_id,
            PriceHistory.product_name == product_name,
            PriceHistory.captured_at >= since
        )
        .order_by(PriceHistory.captured_at.asc())
    )
    
    prices = result.scalars().all()
    
    return {
        "product_name": product_name,
        "history": [
            {"date": p.captured_at, "price": p.price, "currency": p.currency}
            for p in prices
        ]
    }


@router.get("/compare")
async def compare_prices(
    product_name: str,
    competitor_ids: Optional[str] = None,  # Comma-separated UUIDs
    db: AsyncSession = Depends(get_db)
):
    """Compare prices across competitors for a product."""
    
    query = select(PriceHistory, Competitor.name).join(Competitor)
    
    if competitor_ids:
        ids = [UUID(id.strip()) for id in competitor_ids.split(",")]
        query = query.where(PriceHistory.competitor_id.in_(ids))
    
    # Get latest price per competitor
    subquery = (
        select(
            PriceHistory.competitor_id,
            func.max(PriceHistory.captured_at).label("latest")
        )
        .where(PriceHistory.product_name.ilike(f"%{product_name}%"))
        .group_by(PriceHistory.competitor_id)
        .subquery()
    )
    
    result = await db.execute(
        select(PriceHistory, Competitor.name)
        .join(Competitor)
        .join(
            subquery,
            (PriceHistory.competitor_id == subquery.c.competitor_id) &
            (PriceHistory.captured_at == subquery.c.latest)
        )
        .where(PriceHistory.product_name.ilike(f"%{product_name}%"))
    )
    
    comparisons = {}
    for price, comp_name in result.all():
        comparisons[comp_name] = {
            "price": price.price,
            "currency": price.currency,
            "is_on_sale": price.is_on_sale,
            "discount_percent": price.discount_percent
        }
    
    return {
        "product_name": product_name,
        "comparisons": comparisons
    }


@router.get("/alerts/recent", response_model=List[PriceChangeAlert])
async def get_recent_price_alerts(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get recent price change alerts."""
    
    result = await db.execute(
        select(PriceAlert, PriceHistory, Competitor.name)
        .join(PriceHistory)
        .join(Competitor, PriceHistory.competitor_id == Competitor.id)
        .order_by(PriceAlert.created_at.desc())
        .limit(limit)
    )
    
    alerts = []
    for alert, price, comp_name in result.all():
        alerts.append(PriceChangeAlert(
            id=alert.id,
            product_name=price.product_name,
            competitor_name=comp_name,
            change_type=alert.change_type,
            old_price=alert.old_price,
            new_price=alert.new_price,
            change_percent=float(alert.change_percent) if alert.change_percent else None,
            created_at=alert.created_at
        ))
    
    return alerts


@router.get("/deals")
async def get_current_deals(
    db: AsyncSession = Depends(get_db)
):
    """Get all products currently on sale."""
    
    # Get latest price records that are on sale
    subquery = (
        select(
            PriceHistory.competitor_id,
            PriceHistory.product_name,
            func.max(PriceHistory.captured_at).label("latest")
        )
        .group_by(PriceHistory.competitor_id, PriceHistory.product_name)
        .subquery()
    )
    
    result = await db.execute(
        select(PriceHistory, Competitor.name)
        .join(Competitor)
        .join(
            subquery,
            (PriceHistory.competitor_id == subquery.c.competitor_id) &
            (PriceHistory.product_name == subquery.c.product_name) &
            (PriceHistory.captured_at == subquery.c.latest)
        )
        .where(PriceHistory.is_on_sale == True)
    )
    
    deals = []
    for price, comp_name in result.all():
        deals.append({
            "competitor_name": comp_name,
            "product_name": price.product_name,
            "price": price.price,
            "original_price": price.original_price,
            "discount_percent": price.discount_percent,
            "promotion_text": price.promotion_text,
            "url": price.product_url
        })
    
    return deals
