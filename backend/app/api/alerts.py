from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.alert import Alert, AlertType, AlertSeverity

router = APIRouter()


class AlertItem(BaseModel):
    id: UUID
    competitor_id: UUID
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    related_url: Optional[str]
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlertStats(BaseModel):
    total: int
    unread: int
    critical: int
    high: int
    medium: int
    low: int


@router.get("/", response_model=List[AlertItem])
async def get_alerts(
    is_read: Optional[bool] = None,
    severity: Optional[AlertSeverity] = None,
    alert_type: Optional[AlertType] = None,
    competitor_id: Optional[UUID] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get all alerts with optional filtering."""
    
    query = select(Alert).where(Alert.is_dismissed == False)
    
    if is_read is not None:
        query = query.where(Alert.is_read == is_read)
    
    if severity:
        query = query.where(Alert.severity == severity)
    
    if alert_type:
        query = query.where(Alert.alert_type == alert_type)
    
    if competitor_id:
        query = query.where(Alert.competitor_id == competitor_id)
    
    query = query.order_by(Alert.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats", response_model=AlertStats)
async def get_alert_stats(db: AsyncSession = Depends(get_db)):
    """Get alert statistics."""
    
    # Total alerts
    total_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.is_dismissed == False)
    )
    total = total_result.scalar() or 0
    
    # Unread
    unread_result = await db.execute(
        select(func.count(Alert.id)).where(
            and_(Alert.is_dismissed == False, Alert.is_read == False)
        )
    )
    unread = unread_result.scalar() or 0
    
    # By severity
    severity_counts = {}
    for sev in AlertSeverity:
        result = await db.execute(
            select(func.count(Alert.id)).where(
                and_(Alert.is_dismissed == False, Alert.severity == sev)
            )
        )
        severity_counts[sev.value] = result.scalar() or 0
    
    return AlertStats(
        total=total,
        unread=unread,
        critical=severity_counts.get("critical", 0),
        high=severity_counts.get("high", 0),
        medium=severity_counts.get("medium", 0),
        low=severity_counts.get("low", 0)
    )


@router.get("/unread/count")
async def get_unread_count(db: AsyncSession = Depends(get_db)):
    """Get unread alert count for badge."""
    
    result = await db.execute(
        select(func.count(Alert.id)).where(
            and_(Alert.is_dismissed == False, Alert.is_read == False)
        )
    )
    
    return {"count": result.scalar() or 0}


@router.put("/{alert_id}/read")
async def mark_as_read(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Mark an alert as read."""
    
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_read = True
    alert.read_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Alert marked as read"}


@router.put("/read-all")
async def mark_all_as_read(db: AsyncSession = Depends(get_db)):
    """Mark all alerts as read."""
    
    result = await db.execute(
        select(Alert).where(Alert.is_read == False)
    )
    alerts = result.scalars().all()
    
    now = datetime.utcnow()
    for alert in alerts:
        alert.is_read = True
        alert.read_at = now
    
    await db.commit()
    
    return {"message": f"Marked {len(alerts)} alerts as read"}


@router.delete("/{alert_id}")
async def dismiss_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Dismiss an alert."""
    
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_dismissed = True
    await db.commit()
    
    return {"message": "Alert dismissed"}


@router.get("/recent", response_model=List[AlertItem])
async def get_recent_alerts(
    limit: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """Get most recent alerts for notifications dropdown."""
    
    result = await db.execute(
        select(Alert)
        .where(Alert.is_dismissed == False)
        .order_by(Alert.created_at.desc())
        .limit(limit)
    )
    
    return result.scalars().all()
