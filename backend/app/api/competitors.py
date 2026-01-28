from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, HttpUrl
from datetime import datetime
import tldextract

from app.database import get_db
from app.models.competitor import Competitor
from app.models.scan import Scan
from typing import Literal

router = APIRouter()


# Pydantic Schemas
class CompetitorCreate(BaseModel):
    name: str
    url: HttpUrl
    competitor_type: Literal["direct", "indirect"] = "direct"
    description: Optional[str] = None
    industry: Optional[str] = None


class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    competitor_type: Optional[Literal["direct", "indirect"]] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    is_monitoring: Optional[bool] = None


class CompetitorResponse(BaseModel):
    id: UUID
    name: str
    url: str
    domain: str
    logo_url: Optional[str]
    favicon_url: Optional[str]
    competitor_type: str
    health_score: int
    seo_score: int
    content_score: int
    is_monitoring: bool
    last_scanned: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CompetitorDetail(CompetitorResponse):
    description: Optional[str]
    industry: Optional[str]
    technology_stack: Optional[str]
    estimated_traffic: Optional[int]
    domain_authority: Optional[int]


class ScanResponse(BaseModel):
    id: UUID
    competitor_id: UUID
    status: str
    progress: int
    pages_crawled: int
    pages_discovered: int
    started_at: Optional[datetime]
    
    class Config:
        from_attributes = True


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    extracted = tldextract.extract(str(url))
    return f"{extracted.domain}.{extracted.suffix}"


@router.get("/", response_model=List[CompetitorResponse])
async def list_competitors(
    skip: int = 0,
    limit: int = 50,
    competitor_type: Optional[str] = None,
    is_monitoring: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all competitors with optional filtering."""
    
    query = select(Competitor).where(Competitor.is_active == True)
    
    if competitor_type:
        query = query.where(Competitor.competitor_type == competitor_type)
    
    if is_monitoring is not None:
        query = query.where(Competitor.is_monitoring == is_monitoring)
    
    query = query.order_by(Competitor.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    competitors = result.scalars().all()
    
    return competitors


@router.post("/", response_model=CompetitorResponse, status_code=201)
async def create_competitor(
    competitor: CompetitorCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a new competitor to monitor."""
    
    # Check if URL already exists
    existing = await db.execute(
        select(Competitor).where(Competitor.url == str(competitor.url))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="A competitor with this URL already exists"
        )
    
    domain = extract_domain(str(competitor.url))
    
    db_competitor = Competitor(
        name=competitor.name,
        url=str(competitor.url),
        domain=domain,
        competitor_type=competitor.competitor_type,
        description=competitor.description,
        industry=competitor.industry,
        favicon_url=f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    )
    
    db.add(db_competitor)
    await db.commit()
    await db.refresh(db_competitor)
    
    return db_competitor


@router.get("/{competitor_id}", response_model=CompetitorDetail)
async def get_competitor(
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get competitor details by ID."""
    
    result = await db.execute(
        select(Competitor).where(
            Competitor.id == competitor_id,
            Competitor.is_active == True
        )
    )
    competitor = result.scalar_one_or_none()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    return competitor


@router.put("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(
    competitor_id: UUID,
    competitor_update: CompetitorUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update competitor information."""
    
    result = await db.execute(
        select(Competitor).where(Competitor.id == competitor_id)
    )
    competitor = result.scalar_one_or_none()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    update_data = competitor_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(competitor, field, value)
    
    await db.commit()
    await db.refresh(competitor)
    
    return competitor


@router.delete("/{competitor_id}", status_code=204)
async def delete_competitor(
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a competitor."""
    
    result = await db.execute(
        select(Competitor).where(Competitor.id == competitor_id)
    )
    competitor = result.scalar_one_or_none()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    competitor.is_active = False
    await db.commit()
    
    return None


@router.post("/{competitor_id}/scan", response_model=ScanResponse)
async def trigger_scan(
    competitor_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger a new scan for a competitor."""
    
    # Verify competitor exists
    result = await db.execute(
        select(Competitor).where(
            Competitor.id == competitor_id,
            Competitor.is_active == True
        )
    )
    competitor = result.scalar_one_or_none()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    # Check for existing running scan
    running_result = await db.execute(
        select(Scan).where(
            Scan.competitor_id == competitor_id,
            Scan.status == "running"
        )
    )
    if running_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="A scan is already running for this competitor"
        )
    
    # Create new scan
    scan = Scan(
        competitor_id=competitor_id,
        status="pending"
    )
    
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    
    # Trigger background task
    from app.tasks.crawl_tasks import crawl_competitor
    background_tasks.add_task(crawl_competitor, str(competitor_id), str(scan.id))
    
    return scan


@router.get("/{competitor_id}/scans", response_model=List[ScanResponse])
async def get_competitor_scans(
    competitor_id: UUID,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get scan history for a competitor."""
    
    result = await db.execute(
        select(Scan)
        .where(Scan.competitor_id == competitor_id)
        .order_by(Scan.created_at.desc())
        .limit(limit)
    )
    
    return result.scalars().all()
