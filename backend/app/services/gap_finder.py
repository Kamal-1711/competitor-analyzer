import json
from typing import List, Dict, Optional
from uuid import UUID
from collections import defaultdict

from loguru import logger

from app.models.competitor import Competitor
from app.models.product import Product, ProductFeature
from app.models.content import Content
from app.models.seo import SeoAnalysis


class GapFinder:
    """
    Service for identifying competitive gaps and opportunities.
    Analyzes features, content, keywords, and market positioning.
    """
    
    def __init__(self):
        self.min_opportunity_score = 20
    
    async def find_feature_gaps(
        self,
        your_competitor_id: Optional[UUID],
        competitor_ids: List[UUID],
        db
    ) -> List[dict]:
        """Find features that competitors have but you might be missing."""
        from sqlalchemy import select
        
        # Collect all features per competitor
        competitor_features: Dict[str, Dict[str, str]] = {}
        all_features: Dict[str, int] = defaultdict(int)
        
        for comp_id in competitor_ids:
            result = await db.execute(
                select(ProductFeature, Product.name)
                .join(Product)
                .where(Product.competitor_id == comp_id)
            )
            
            comp_features = {}
            for feature, product_name in result.all():
                feature_key = feature.feature_name.lower().strip()
                comp_features[feature_key] = feature.feature_value or "Present"
                all_features[feature_key] += 1
            
            competitor_features[str(comp_id)] = comp_features
        
        # Identify gaps
        gaps = []
        
        # Sort features by how many competitors have them
        sorted_features = sorted(
            all_features.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        for feature_name, count in sorted_features:
            # Get your status
            your_status = "Missing"
            if your_competitor_id:
                your_features = competitor_features.get(str(your_competitor_id), {})
                if feature_name in your_features:
                    your_status = "Present"
            
            # Build competitor coverage
            coverage = {}
            for comp_id, features in competitor_features.items():
                if comp_id != str(your_competitor_id):
                    coverage[comp_id] = "Present" if feature_name in features else "Missing"
            
            # Calculate opportunity score
            competitors_with = sum(1 for v in coverage.values() if v == "Present")
            opportunity_score = int((competitors_with / len(coverage)) * 100) if coverage else 0
            
            if your_status == "Missing" and opportunity_score >= self.min_opportunity_score:
                gaps.append({
                    'feature_name': feature_name.title(),
                    'your_status': your_status,
                    'competitors': coverage,
                    'opportunity_score': opportunity_score
                })
        
        # Sort by opportunity score
        gaps.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        return gaps[:50]  # Return top 50 gaps
    
    async def find_content_gaps(
        self,
        your_competitor_id: Optional[UUID],
        competitor_ids: List[UUID],
        db
    ) -> List[dict]:
        """Find content topics that competitors cover but you might be missing."""
        from sqlalchemy import select
        
        # Collect topics/keywords per competitor
        competitor_topics: Dict[str, set] = {}
        all_topics: Dict[str, int] = defaultdict(int)
        
        for comp_id in competitor_ids:
            result = await db.execute(
                select(Content.keywords, Content.content_type, Content.title)
                .where(Content.competitor_id == comp_id)
            )
            
            topics = set()
            for keywords_json, content_type, title in result.all():
                # Add keywords as topics
                if keywords_json:
                    try:
                        keywords = json.loads(keywords_json)
                        for kw in keywords[:5]:
                            topics.add(kw.lower())
                            all_topics[kw.lower()] += 1
                    except:
                        pass
                
                # Add title words as potential topics
                if title:
                    words = title.lower().split()
                    for word in words:
                        if len(word) > 4:  # Only significant words
                            topics.add(word)
            
            competitor_topics[str(comp_id)] = topics
        
        # Identify gaps
        gaps = []
        
        # Get your topics
        your_topics = set()
        if your_competitor_id:
            your_topics = competitor_topics.get(str(your_competitor_id), set())
        
        # Sort topics by frequency
        sorted_topics = sorted(
            all_topics.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for topic, count in sorted_topics[:100]:
            if topic not in your_topics:
                # Build coverage
                coverage = {}
                for comp_id, topics in competitor_topics.items():
                    if comp_id != str(your_competitor_id):
                        coverage[comp_id] = topic in topics
                
                # Calculate opportunity
                competitors_with = sum(1 for v in coverage.values() if v)
                
                if competitors_with >= 2:  # At least 2 competitors cover it
                    gaps.append({
                        'topic': topic.title(),
                        'your_coverage': False,
                        'competitor_coverage': coverage,
                        'opportunity_score': int((competitors_with / len(coverage)) * 100)
                    })
        
        # Sort by opportunity score
        gaps.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        return gaps[:30]
    
    async def find_keyword_opportunities(
        self,
        competitor_ids: List[UUID],
        db
    ) -> List[dict]:
        """Find keyword opportunities based on competitor SEO analysis."""
        from sqlalchemy import select
        
        # Collect keywords from SEO analyses
        keyword_data: Dict[str, List[str]] = defaultdict(list)
        
        for comp_id in competitor_ids:
            result = await db.execute(
                select(SeoAnalysis.keyword_density, Competitor.name)
                .join(Competitor)
                .where(SeoAnalysis.competitor_id == comp_id)
                .order_by(SeoAnalysis.analyzed_at.desc())
                .limit(5)
            )
            
            for kw_json, comp_name in result.all():
                if kw_json:
                    try:
                        keywords = json.loads(kw_json)
                        if isinstance(keywords, dict):
                            for kw in list(keywords.keys())[:10]:
                                keyword_data[kw.lower()].append(comp_name)
                    except:
                        pass
        
        # Rank opportunities
        opportunities = []
        
        for keyword, competitors in keyword_data.items():
            if len(keyword) > 3:
                # Fewer competitors = better opportunity
                opportunity_score = max(100 - len(set(competitors)) * 15, 10)
                
                opportunities.append({
                    'keyword': keyword,
                    'search_volume': None,  # Would need external API
                    'difficulty': None,
                    'competitors_ranking': list(set(competitors)),
                    'opportunity_score': opportunity_score
                })
        
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        return opportunities[:30]
    
    async def get_market_positioning(
        self,
        competitor_ids: List[UUID],
        db
    ) -> dict:
        """Get market positioning data for visualization."""
        from sqlalchemy import select
        
        positioning = []
        
        result = await db.execute(
            select(Competitor)
            .where(Competitor.id.in_(competitor_ids))
        )
        
        for competitor in result.scalars().all():
            positioning.append({
                'name': competitor.name,
                'x': competitor.seo_score,
                'y': competitor.content_score,
                'size': competitor.health_score,
                'type': competitor.competitor_type.value
            })
        
        return {
            'axes': {
                'x': 'SEO Strength',
                'y': 'Content Quality'
            },
            'data': positioning
        }
    
    async def calculate_opportunity_summary(
        self,
        your_competitor_id: Optional[UUID],
        competitor_ids: List[UUID],
        db
    ) -> dict:
        """Calculate overall opportunity summary."""
        feature_gaps = await self.find_feature_gaps(your_competitor_id, competitor_ids, db)
        content_gaps = await self.find_content_gaps(your_competitor_id, competitor_ids, db)
        keyword_opps = await self.find_keyword_opportunities(competitor_ids, db)
        
        # Calculate overall score
        total_opportunities = len(feature_gaps) + len(content_gaps) + len(keyword_opps)
        
        if total_opportunities == 0:
            overall_score = 100
        else:
            # Higher gaps = lower score
            overall_score = max(0, 100 - (total_opportunities * 2))
        
        return {
            'feature_gaps': len(feature_gaps),
            'content_gaps': len(content_gaps),
            'keyword_opportunities': len(keyword_opps),
            'overall_opportunity_score': overall_score
        }
