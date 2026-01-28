from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.models.competitor import Competitor
from app.models.scan import Scan
from app.models.alert import Alert
from app.models.content import ContentChange

router = APIRouter()


class MetricCard(BaseModel):
    label: str
    value: int | str
    change: float | None = None
    change_direction: str | None = None  # "up", "down", "neutral"
    icon: str


class ActivityItem(BaseModel):
    id: str
    type: str
    title: str
    description: str
    competitor_name: str
    timestamp: datetime


class HealthScoreBreakdown(BaseModel):
    overall_score: int
    strengths: int
    neutrals: int
    alerts: int


class DashboardMetrics(BaseModel):
    total_competitors: MetricCard
    changes_24h: MetricCard
    active_monitors: MetricCard
    critical_alerts: MetricCard


class ScanProgress(BaseModel):
    is_scanning: bool
    current_scan_id: str | None
    progress: int
    current_url: str | None
    pages_crawled: int
    pages_discovered: int


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    """Get top-level dashboard metrics."""
    
    # Total competitors
    total_result = await db.execute(
        select(func.count(Competitor.id)).where(Competitor.is_active == True)
    )
    total_competitors = total_result.scalar() or 0
    
    # Changes in last 24 hours
    yesterday = datetime.utcnow() - timedelta(hours=24)
    changes_result = await db.execute(
        select(func.count(ContentChange.id)).where(
            ContentChange.detected_at >= yesterday
        )
    )
    changes_24h = changes_result.scalar() or 0
    
    # Active monitors (running scans)
    active_result = await db.execute(
        select(func.count(Scan.id)).where(
            Scan.status == "running"
        )
    )
    active_monitors = active_result.scalar() or 0
    
    alerts_result = await db.execute(
        select(func.count(Alert.id)).where(
            and_(
                Alert.is_read == False,
                Alert.severity.in_(["high", "critical"])
            )
        )
    )
    critical_alerts = alerts_result.scalar() or 0
    
    return DashboardMetrics(
        total_competitors=MetricCard(
            label="Total Competitors",
            value=total_competitors,
            icon="users"
        ),
        changes_24h=MetricCard(
            label="Changes (24h)",
            value=changes_24h,
            change=15.2,  # TODO: Calculate actual change
            change_direction="up",
            icon="activity"
        ),
        active_monitors=MetricCard(
            label="Active Monitors",
            value=active_monitors,
            icon="radar"
        ),
        critical_alerts=MetricCard(
            label="Critical Alerts",
            value=critical_alerts,
            icon="alert-triangle"
        )
    )


@router.get("/activity", response_model=List[ActivityItem])
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get recent activity feed."""
    
    # Get recent content changes
    result = await db.execute(
        select(ContentChange, Competitor.name)
        .join(ContentChange.content)
        .join(Competitor)
        .order_by(ContentChange.detected_at.desc())
        .limit(limit)
    )
    
    activities = []
    for change, competitor_name in result.all():
        activities.append(ActivityItem(
            id=str(change.id),
            type=change.change_type,
            title=f"Content {change.change_type}",
            description=f"{change.field_changed} was {change.change_type}",
            competitor_name=competitor_name,
            timestamp=change.detected_at
        ))
    
    return activities


@router.get("/health-score", response_model=HealthScoreBreakdown)
async def get_health_score(db: AsyncSession = Depends(get_db)):
    """Get competitive health score breakdown."""
    
    # Get all active competitors and calculate averages
    result = await db.execute(
        select(
            func.avg(Competitor.health_score),
            func.count(Competitor.id).filter(Competitor.health_score >= 70),
            func.count(Competitor.id).filter(
                and_(Competitor.health_score >= 40, Competitor.health_score < 70)
            ),
            func.count(Competitor.id).filter(Competitor.health_score < 40)
        ).where(Competitor.is_active == True)
    )
    
    row = result.one_or_none()
    
    if row:
        avg_score, strengths, neutrals, alerts = row
        return HealthScoreBreakdown(
            overall_score=int(avg_score or 0),
            strengths=strengths or 0,
            neutrals=neutrals or 0,
            alerts=alerts or 0
        )
    
    return HealthScoreBreakdown(
        overall_score=0,
        strengths=0,
        neutrals=0,
        alerts=0
    )


@router.get("/scan-progress", response_model=ScanProgress)
async def get_scan_progress(db: AsyncSession = Depends(get_db)):
    """Get current scan progress if any scan is running."""
    
    result = await db.execute(
        select(Scan)
        .where(Scan.status == "running")
        .order_by(Scan.started_at.desc())
        .limit(1)
    )
    
    scan = result.scalar_one_or_none()
    
    if scan:
        return ScanProgress(
            is_scanning=True,
            current_scan_id=str(scan.id),
            progress=scan.progress,
            current_url=scan.current_url,
            pages_crawled=scan.pages_crawled,
            pages_discovered=scan.pages_discovered
        )
    
    return ScanProgress(
        is_scanning=False,
        current_scan_id=None,
        progress=0,
        current_url=None,
        pages_crawled=0,
        pages_discovered=0
    )
