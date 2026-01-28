from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.models.product import Product, ProductFeature
from app.models.content import Content, ContentType
from app.models.competitor import Competitor
from app.models.seo import SeoAnalysis

router = APIRouter()


class FeatureGap(BaseModel):
    feature_name: str
    your_status: Optional[str]  # Present, Missing, Partial
    competitors: dict  # competitor_name -> status


class ContentGap(BaseModel):
    topic: str
    your_coverage: bool
    competitor_coverage: dict  # competitor_name -> has_coverage


class KeywordOpportunity(BaseModel):
    keyword: str
    search_volume: Optional[int]
    difficulty: Optional[int]
    competitors_ranking: List[str]
    opportunity_score: int


class GapSummary(BaseModel):
    feature_gaps: int
    content_gaps: int
    keyword_opportunities: int
    overall_opportunity_score: int


@router.get("/summary", response_model=GapSummary)
async def get_gap_summary(
    db: AsyncSession = Depends(get_db)
):
    """Get overall gap analysis summary."""
    from app.services.gap_finder import GapFinder
    
    # Fetch all active competitor IDs
    result = await db.execute(
        select(Competitor.id).where(Competitor.is_active == True)
    )
    competitor_ids = [row[0] for row in result.fetchall()]
    
    if not competitor_ids:
        return GapSummary(
            feature_gaps=0,
            content_gaps=0,
            keyword_opportunities=0,
            overall_opportunity_score=100
        )
    
    # Use real GapFinder service
    finder = GapFinder()
    summary = await finder.calculate_opportunity_summary(None, competitor_ids, db)
    
    return GapSummary(**summary)


@router.get("/features", response_model=List[FeatureGap])
async def get_feature_gaps(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Identify feature gaps compared to competitors."""
    
    query = (
        select(ProductFeature.feature_name, ProductFeature.feature_value, Competitor.name)
        .join(Product)
        .join(Competitor)
    )
    
    if category:
        query = query.where(ProductFeature.feature_category == category)
    
    result = await db.execute(query)
    
    # Build feature matrix
    feature_data = {}
    
    for feature_name, value, comp_name in result.all():
        if feature_name not in feature_data:
            feature_data[feature_name] = {}
        feature_data[feature_name][comp_name] = value or "Present"
    
    gaps = []
    for name, competitors in feature_data.items():
        gaps.append(FeatureGap(
            feature_name=name,
            your_status="Missing",  # Placeholder - compare with your own products
            competitors=competitors
        ))
    
    return gaps[:20]  # Limit results


@router.get("/content", response_model=List[ContentGap])
async def get_content_gaps(
    content_type: Optional[ContentType] = None,
    db: AsyncSession = Depends(get_db)
):
    """Identify content topic gaps."""
    
    query = (
        select(Content.keywords, Competitor.name)
        .join(Competitor)
    )
    
    if content_type:
        query = query.where(Content.content_type == content_type)
    
    result = await db.execute(query)
    
    # Extract topics from keywords
    topic_coverage = {}
    
    for keywords_json, comp_name in result.all():
        if keywords_json:
            import json
            try:
                keywords = json.loads(keywords_json)
                for kw in keywords[:5]:  # Top 5 keywords as topics
                    if kw not in topic_coverage:
                        topic_coverage[kw] = {}
                    topic_coverage[kw][comp_name] = True
            except:
                pass
    
    gaps = []
    for topic, coverage in topic_coverage.items():
        gaps.append(ContentGap(
            topic=topic,
            your_coverage=False,  # Placeholder
            competitor_coverage=coverage
        ))
    
    return gaps[:20]


@router.get("/keywords", response_model=List[KeywordOpportunity])
async def get_keyword_opportunities(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Identify keyword ranking opportunities."""
    
    # Get SEO analyses to extract keyword data
    result = await db.execute(
        select(SeoAnalysis.keyword_density, Competitor.name)
        .join(Competitor)
        .order_by(SeoAnalysis.analyzed_at.desc())
        .limit(100)
    )
    
    keyword_data = {}
    
    for kw_json, comp_name in result.all():
        if kw_json:
            import json
            try:
                keywords = json.loads(kw_json)
                for kw, density in keywords.items() if isinstance(keywords, dict) else []:
                    if kw not in keyword_data:
                        keyword_data[kw] = []
                    keyword_data[kw].append(comp_name)
            except:
                pass
    
    opportunities = []
    for kw, competitors in list(keyword_data.items())[:limit]:
        opportunities.append(KeywordOpportunity(
            keyword=kw,
            search_volume=None,  # Would need external API
            difficulty=None,
            competitors_ranking=competitors,
            opportunity_score=max(100 - len(competitors) * 10, 20)
        ))
    
    # Sort by opportunity score
    opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
    
    return opportunities


@router.get("/positioning")
async def get_market_positioning(
    db: AsyncSession = Depends(get_db)
):
    """Get market positioning visualization data."""
    
    result = await db.execute(
        select(Competitor)
        .where(Competitor.is_active == True)
    )
    
    competitors = result.scalars().all()
    
    positioning = []
    for comp in competitors:
        positioning.append({
            "name": comp.name,
            "x": comp.seo_score,  # Use SEO as one axis
            "y": comp.content_score,  # Use content as another
            "size": comp.health_score,
            "type": comp.competitor_type.value
        })
    
    return {
        "axes": {
            "x": "SEO Strength",
            "y": "Content Quality"
        },
        "data": positioning
    }
