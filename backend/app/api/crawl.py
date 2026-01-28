from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from enum import Enum

from app.database import get_db
from app.models.scan import Scan, ScanPage
from app.models.competitor import Competitor

router = APIRouter()


# Schemas
class ScanType(str, Enum):
    FULL = "full"
    QUICK = "quick"


class ScanCreate(BaseModel):
    competitor_id: UUID
    scan_type: ScanType = ScanType.FULL
    max_pages: Optional[int] = 100


class ScanResponse(BaseModel):
    id: UUID
    competitor_id: UUID
    status: str
    progress: int
    pages_crawled: int
    pages_discovered: int
    current_url: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScanDetailResponse(ScanResponse):
    competitor_name: Optional[str] = None
    duration_seconds: Optional[int] = None
    pages_per_minute: Optional[float] = None


class ScanPageResponse(BaseModel):
    id: UUID
    url: str
    title: Optional[str]
    status_code: Optional[int]
    word_count: Optional[int]
    load_time_ms: Optional[int]
    crawled_at: datetime
    
    class Config:
        from_attributes = True


class ScanStatsResponse(BaseModel):
    total_scans: int
    completed_scans: int
    running_scans: int
    failed_scans: int
    total_pages_crawled: int
    avg_pages_per_scan: float
    avg_duration_seconds: float


class QuickScanRequest(BaseModel):
    url: HttpUrl


class QuickScanResponse(BaseModel):
    url: str
    title: Optional[str]
    word_count: int
    load_time_ms: int
    status_code: Optional[int]
    content_hash: str


# Endpoints

@router.get("/test-playwright")
async def test_playwright():
    """Debug endpoint to test Playwright in API context."""
    from loguru import logger
    import traceback
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def run_sync_test():
        """Run playwright test synchronously in thread."""
        from playwright.sync_api import sync_playwright
        
        steps = []
        try:
            steps.append("1. Starting sync_playwright...")
            with sync_playwright() as playwright:
                steps.append("   OK")
                
                steps.append("2. Launching browser...")
                browser = playwright.chromium.launch(headless=True)
                steps.append("   OK")
                
                steps.append("3. Creating page...")
                page = browser.new_page()
                steps.append("   OK")
                
                steps.append("4. Navigating to example.com...")
                page.goto("https://example.com", timeout=30000)
                title = page.title()
                steps.append(f"   OK - Title: {title}")
                
                steps.append("5. Closing browser...")
                browser.close()
                steps.append("   OK")
            
            return {"status": "success", "steps": steps, "title": title}
            
        except Exception as e:
            error_trace = traceback.format_exc()
            steps.append(f"   FAILED: {type(e).__name__}: {str(e)}")
            return {"status": "failed", "steps": steps, "error": str(e), "traceback": error_trace}
    
    # Run in thread pool
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, run_sync_test)
    
    return result


@router.get("/", response_model=List[ScanResponse])
async def list_scans(
    competitor_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all scans with optional filtering."""
    query = select(Scan)
    
    if competitor_id:
        query = query.where(Scan.competitor_id == competitor_id)
    
    if status:
        query = query.where(Scan.status == status)
    
    query = query.order_by(Scan.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ScanResponse, status_code=201)
async def create_scan(
    scan_data: ScanCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create and start a new scan."""
    # Verify competitor exists
    result = await db.execute(
        select(Competitor).where(
            Competitor.id == scan_data.competitor_id,
            Competitor.is_active == True
        )
    )
    competitor = result.scalar_one_or_none()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    # Check for running scans
    running = await db.execute(
        select(Scan).where(
            Scan.competitor_id == scan_data.competitor_id,
            Scan.status == "running"
        )
    )
    if running.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A scan is already running")
    
    # Create scan
    scan = Scan(
        competitor_id=scan_data.competitor_id,
        status="pending",
        pages_discovered=scan_data.max_pages or 100
    )
    
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    
    # Trigger crawl task
    from app.tasks.crawl_tasks import crawl_competitor, quick_scan
    
    if scan_data.scan_type == ScanType.FULL:
        background_tasks.add_task(crawl_competitor, str(scan_data.competitor_id), str(scan.id))
    else:
        background_tasks.add_task(quick_scan, competitor.url)
    
    return scan


@router.get("/stats", response_model=ScanStatsResponse)
async def get_scan_stats(db: AsyncSession = Depends(get_db)):
    """Get overall scan statistics."""
    # Total scans
    total = await db.execute(select(func.count(Scan.id)))
    total_scans = total.scalar()
    
    # By status
    completed = await db.execute(
        select(func.count(Scan.id)).where(Scan.status == "completed")
    )
    completed_scans = completed.scalar()
    
    running = await db.execute(
        select(func.count(Scan.id)).where(Scan.status == "running")
    )
    running_scans = running.scalar()
    
    failed = await db.execute(
        select(func.count(Scan.id)).where(Scan.status == "failed")
    )
    failed_scans = failed.scalar()
    
    # Total pages
    pages = await db.execute(select(func.sum(Scan.pages_crawled)))
    total_pages = pages.scalar() or 0
    
    # Averages
    avg_pages = total_pages / total_scans if total_scans > 0 else 0
    
    # Average duration for completed scans
    # This is simplified - in production would use proper timestamp diff
    avg_duration = 120.0  # Placeholder
    
    return ScanStatsResponse(
        total_scans=total_scans,
        completed_scans=completed_scans,
        running_scans=running_scans,
        failed_scans=failed_scans,
        total_pages_crawled=total_pages,
        avg_pages_per_scan=round(avg_pages, 1),
        avg_duration_seconds=avg_duration
    )


@router.get("/running", response_model=List[ScanDetailResponse])
async def get_running_scans(db: AsyncSession = Depends(get_db)):
    """Get all currently running scans."""
    result = await db.execute(
        select(Scan, Competitor.name)
        .join(Competitor)
        .where(Scan.status == "running")
        .order_by(Scan.started_at.desc())
    )
    
    scans = []
    for scan, comp_name in result.all():
        scan_dict = {
            "id": scan.id,
            "competitor_id": scan.competitor_id,
            "status": scan.status,
            "progress": scan.progress,
            "pages_crawled": scan.pages_crawled,
            "pages_discovered": scan.pages_discovered,
            "current_url": scan.current_url,
            "error_message": scan.error_message,
            "started_at": scan.started_at,
            "completed_at": scan.completed_at,
            "created_at": scan.created_at,
            "competitor_name": comp_name
        }
        scans.append(ScanDetailResponse(**scan_dict))
    
    return scans


@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(scan_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get scan details by ID."""
    result = await db.execute(
        select(Scan, Competitor.name)
        .join(Competitor)
        .where(Scan.id == scan_id)
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan, comp_name = row
    
    # Calculate duration
    duration = None
    ppm = None
    if scan.started_at and scan.completed_at:
        duration = int((scan.completed_at - scan.started_at).total_seconds())
        if duration > 0:
            ppm = round(scan.pages_crawled / (duration / 60), 2)
    
    return ScanDetailResponse(
        id=scan.id,
        competitor_id=scan.competitor_id,
        status=scan.status,
        progress=scan.progress,
        pages_crawled=scan.pages_crawled,
        pages_discovered=scan.pages_discovered,
        current_url=scan.current_url,
        error_message=scan.error_message,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        created_at=scan.created_at,
        competitor_name=comp_name,
        duration_seconds=duration,
        pages_per_minute=ppm
    )


@router.get("/{scan_id}/pages", response_model=List[ScanPageResponse])
async def get_scan_pages(
    scan_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get pages crawled in a scan."""
    result = await db.execute(
        select(ScanPage)
        .where(ScanPage.scan_id == scan_id)
        .order_by(ScanPage.crawled_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    return result.scalars().all()


@router.delete("/{scan_id}", status_code=204)
async def cancel_scan(scan_id: UUID, db: AsyncSession = Depends(get_db)):
    """Cancel a running scan."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan.status == "completed":
        raise HTTPException(status_code=400, detail="Scan already completed")
    
    scan.status = "failed"
    scan.error_message = "Cancelled by user"
    scan.completed_at = datetime.utcnow()
    
    await db.commit()
    
    return None


@router.post("/quick", response_model=QuickScanResponse)
async def run_quick_scan(request: QuickScanRequest):
    """Run a quick single-page scan."""
    from app.services.crawler import PlaywrightCrawler
    
    crawler = PlaywrightCrawler()
    
    try:
        result = await crawler.quick_scan(str(request.url))
        
        return QuickScanResponse(
            url=result.get("url", str(request.url)),
            title=result.get("title"),
            word_count=result.get("word_count", 0),
            load_time_ms=result.get("load_time_ms", 0),
            status_code=result.get("status_code"),
            content_hash=result.get("content_hash", "")
        )
    except Exception as e:
        import traceback
        from loguru import logger
        logger.error(f"Quick scan failed: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Scan failed: {type(e).__name__}: {str(e)}")


@router.post("/{scan_id}/retry", response_model=ScanResponse)
async def retry_scan(
    scan_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Retry a failed scan."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    original_scan = result.scalar_one_or_none()
    
    if not original_scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if original_scan.status not in ["failed", "completed"]:
        raise HTTPException(status_code=400, detail="Can only retry failed or completed scans")
    
    # Create new scan
    new_scan = Scan(
        competitor_id=original_scan.competitor_id,
        status="pending"
    )
    
    db.add(new_scan)
    await db.commit()
    await db.refresh(new_scan)
    
    # Trigger crawl
    from app.tasks.crawl_tasks import crawl_competitor
    background_tasks.add_task(crawl_competitor, str(original_scan.competitor_id), str(new_scan.id))
    
    return new_scan
