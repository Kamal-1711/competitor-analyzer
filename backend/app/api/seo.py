from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.seo import SeoAnalysis
from app.models.competitor import Competitor

router = APIRouter()


class SeoScoreCard(BaseModel):
    category: str
    score: int
    max_score: int
    issues: List[str]
    recommendations: List[str]


class SeoAnalysisResponse(BaseModel):
    id: UUID
    competitor_id: UUID
    url: str
    overall_score: int
    
    # On-page
    title: Optional[str] = None
    title_length: Optional[int] = 0
    title_score: int = 0
    meta_description: Optional[str] = None
    meta_description_length: Optional[int] = 0
    meta_description_score: int = 0
    
    # Headers
    h1_count: int = 0
    h2_count: int = 0
    h3_count: int = 0
    headers_score: int = 0
    
    # Content
    word_count: int = 0
    content_score: int = 0
    
    # Images (DB uses images_count, not total_images)
    images_count: int = 0
    images_with_alt: int = 0
    images_score: int = 0
    
    # Links
    internal_links: int = 0
    external_links: int = 0
    broken_links: int = 0
    links_score: int = 0
    
    # Technical (DB uses has_robots_meta and mobile_friendly, not has_robots_txt/is_mobile_friendly)
    has_ssl: bool = False
    has_sitemap: bool = False
    has_robots_meta: bool = False
    has_canonical: bool = False
    mobile_friendly: bool = False
    technical_score: int = 0
    
    # Performance (DB uses load_time_ms and page_size_bytes)
    load_time_ms: Optional[int] = None
    page_size_bytes: Optional[int] = None
    
    analyzed_at: datetime
    
    class Config:
        from_attributes = True


class SeoComparisonItem(BaseModel):
    competitor_id: UUID
    competitor_name: str
    overall_score: int
    title_score: int
    content_score: int
    technical_score: int
    performance_score: int


@router.get("/{competitor_id}", response_model=SeoAnalysisResponse)
async def get_seo_analysis(
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get latest SEO analysis for a competitor."""
    
    result = await db.execute(
        select(SeoAnalysis)
        .where(SeoAnalysis.competitor_id == competitor_id)
        .order_by(SeoAnalysis.analyzed_at.desc())
        .limit(1)
    )
    
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="No SEO analysis found for this competitor"
        )
    
    return analysis


@router.get("/{competitor_id}/history", response_model=List[SeoAnalysisResponse])
async def get_seo_history(
    competitor_id: UUID,
    limit: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get SEO analysis history for trending."""
    
    result = await db.execute(
        select(SeoAnalysis)
        .where(SeoAnalysis.competitor_id == competitor_id)
        .order_by(SeoAnalysis.analyzed_at.desc())
        .limit(limit)
    )
    
    return result.scalars().all()


@router.get("/compare", response_model=List[SeoComparisonItem])
async def compare_seo(
    competitor_ids: str,  # Comma-separated UUIDs
    db: AsyncSession = Depends(get_db)
):
    """Compare SEO scores across multiple competitors."""
    
    ids = [UUID(id.strip()) for id in competitor_ids.split(",")]
    
    comparisons = []
    
    for comp_id in ids:
        # Get competitor name
        comp_result = await db.execute(
            select(Competitor.name).where(Competitor.id == comp_id)
        )
        name = comp_result.scalar_one_or_none()
        
        if not name:
            continue
        
        # Get latest SEO analysis
        seo_result = await db.execute(
            select(SeoAnalysis)
            .where(SeoAnalysis.competitor_id == comp_id)
            .order_by(SeoAnalysis.analyzed_at.desc())
            .limit(1)
        )
        analysis = seo_result.scalar_one_or_none()
        
        if analysis:
            comparisons.append(SeoComparisonItem(
                competitor_id=comp_id,
                competitor_name=name,
                overall_score=analysis.overall_score,
                title_score=analysis.title_score,
                content_score=analysis.content_score,
                technical_score=analysis.technical_score,
                performance_score=analysis.performance_score
            ))
    
    return comparisons


@router.post("/{competitor_id}/analyze")
async def trigger_seo_analysis(
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Trigger a new SEO analysis for a competitor."""
    
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
    
    # Run SEO analysis
    from app.services.seo_analyzer import SeoAnalyzer
    
    try:
        analyzer = SeoAnalyzer()
        analysis_result = await analyzer.analyze(competitor.url, competitor_id)
        
        # Update competitor SEO score
        competitor.seo_score = analysis_result["overall_score"]
        await db.commit()
        
        return {
            "message": "SEO analysis completed",
            "competitor_id": str(competitor_id),
            "overall_score": analysis_result["overall_score"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SEO analysis failed: {str(e)}")


@router.get("/{competitor_id}/audit", response_model=List[SeoScoreCard])
async def get_seo_audit(
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed SEO audit with issues and recommendations."""
    
    result = await db.execute(
        select(SeoAnalysis)
        .where(SeoAnalysis.competitor_id == competitor_id)
        .order_by(SeoAnalysis.analyzed_at.desc())
        .limit(1)
    )
    
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="No SEO analysis found"
        )
    
    audit_cards = []
    
    # Title audit
    title_issues = []
    title_recs = []
    if not analysis.title:
        title_issues.append("Missing title tag")
        title_recs.append("Add a descriptive title tag")
    elif analysis.title_length < 30:
        title_issues.append("Title too short")
        title_recs.append("Expand title to 50-60 characters")
    elif analysis.title_length > 60:
        title_issues.append("Title too long")
        title_recs.append("Shorten title to under 60 characters")
    
    audit_cards.append(SeoScoreCard(
        category="Title Tag",
        score=analysis.title_score,
        max_score=100,
        issues=title_issues,
        recommendations=title_recs
    ))
    
    # Meta description audit
    meta_issues = []
    meta_recs = []
    if not analysis.meta_description:
        meta_issues.append("Missing meta description")
        meta_recs.append("Add a compelling meta description")
    elif analysis.meta_description_length < 120:
        meta_issues.append("Meta description too short")
        meta_recs.append("Expand to 150-160 characters")
    
    audit_cards.append(SeoScoreCard(
        category="Meta Description",
        score=analysis.meta_description_score,
        max_score=100,
        issues=meta_issues,
        recommendations=meta_recs
    ))
    
    # Headers audit
    header_issues = []
    header_recs = []
    if analysis.h1_count == 0:
        header_issues.append("No H1 heading found")
        header_recs.append("Add exactly one H1 heading")
    elif analysis.h1_count > 1:
        header_issues.append(f"Multiple H1 headings ({analysis.h1_count})")
        header_recs.append("Use only one H1 heading per page")
    
    audit_cards.append(SeoScoreCard(
        category="Headings",
        score=analysis.headers_score,
        max_score=100,
        issues=header_issues,
        recommendations=header_recs
    ))
    
    # Images audit
    image_issues = []
    image_recs = []
    if analysis.total_images > 0:
        missing_alt = analysis.total_images - analysis.images_with_alt
        if missing_alt > 0:
            image_issues.append(f"{missing_alt} images missing alt text")
            image_recs.append("Add descriptive alt text to all images")
    
    audit_cards.append(SeoScoreCard(
        category="Images",
        score=analysis.images_score,
        max_score=100,
        issues=image_issues,
        recommendations=image_recs
    ))
    
    # Technical audit
    tech_issues = []
    tech_recs = []
    if not analysis.has_ssl:
        tech_issues.append("No SSL certificate")
        tech_recs.append("Enable HTTPS")
    if not analysis.has_sitemap:
        tech_issues.append("Missing sitemap.xml")
        tech_recs.append("Create and submit a sitemap")
    if not analysis.has_robots_txt:
        tech_issues.append("Missing robots.txt")
        tech_recs.append("Add a robots.txt file")
    if not analysis.has_canonical:
        tech_issues.append("Missing canonical tag")
        tech_recs.append("Add canonical tags to prevent duplicate content")
    if not analysis.has_schema_markup:
        tech_issues.append("No schema markup detected")
        tech_recs.append("Implement structured data")
    
    audit_cards.append(SeoScoreCard(
        category="Technical SEO",
        score=analysis.technical_score,
        max_score=100,
        issues=tech_issues,
        recommendations=tech_recs
    ))
    
    return audit_cards


@router.get("/{competitor_id}/report")
async def get_full_seo_report(
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive SEO audit report."""
    from app.services.seo_comparator import SeoAuditReporter
    
    report = await SeoAuditReporter.generate_report(competitor_id, db)
    
    if 'error' in report:
        raise HTTPException(status_code=404, detail=report['error'])
    
    return report


@router.get("/{competitor_id}/trends")
async def get_seo_trends(
    competitor_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get SEO score trends over time."""
    from app.services.seo_comparator import SeoTrendAnalyzer
    
    return await SeoTrendAnalyzer.get_trends(competitor_id, days, db)


@router.post("/compare/detailed")
async def compare_seo_detailed(
    competitor_ids: List[UUID],
    your_competitor_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed SEO comparison with insights and radar chart data."""
    from app.services.seo_comparator import SeoComparator
    
    return await SeoComparator.compare(your_competitor_id, competitor_ids, db)


@router.post("/analyze/quick")
async def quick_seo_analysis(
    url: str,
    db: AsyncSession = Depends(get_db)
):
    """Run quick SEO analysis on any URL (without saving)."""
    from app.services.seo_analyzer import SeoAnalyzer
    from app.services.seo_utils import SchemaAnalyzer, OpenGraphAnalyzer, KeywordAnalyzer, PageSpeedEstimator
    import httpx
    from bs4 import BeautifulSoup
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, follow_redirects=True)
            html = response.text
        
        soup = BeautifulSoup(html, "lxml")
        
        # Run all analyzers
        schema = SchemaAnalyzer.analyze(soup)
        social = OpenGraphAnalyzer.analyze(soup)
        keywords = KeywordAnalyzer.analyze(soup)
        performance = PageSpeedEstimator.estimate(soup, html)
        
        # Basic SEO checks
        title = soup.title.string if soup.title else None
        meta_desc = soup.find("meta", {"name": "description"})
        meta_desc = meta_desc.get("content") if meta_desc else None
        
        h1_tags = soup.find_all("h1")
        h2_tags = soup.find_all("h2")
        
        return {
            "url": url,
            "basic": {
                "title": title,
                "title_length": len(title) if title else 0,
                "meta_description": meta_desc,
                "meta_description_length": len(meta_desc) if meta_desc else 0,
                "h1_count": len(h1_tags),
                "h2_count": len(h2_tags)
            },
            "schema_markup": schema,
            "social_meta": social,
            "keywords": keywords,
            "performance": performance,
            "recommendations": (
                schema.get('recommendations', []) +
                social.get('recommendations', []) +
                keywords.get('recommendations', []) +
                performance.get('recommendations', [])
            )[:15]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

