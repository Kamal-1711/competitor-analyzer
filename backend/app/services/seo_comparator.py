"""
SEO comparison and benchmarking for Web-Spy.
Compares SEO metrics across multiple competitors and generates insights.
"""

from typing import List, Dict, Optional
from uuid import UUID
from dataclasses import dataclass
from collections import defaultdict

from loguru import logger


@dataclass
class SeoMetric:
    """Represents an SEO metric for comparison."""
    name: str
    your_value: Optional[float]
    competitor_values: Dict[str, float]
    average: float
    best: float
    best_competitor: str
    your_rank: int
    total_competitors: int


class SeoComparator:
    """
    Compares SEO performance across multiple competitors.
    Generates insights and recommendations based on competitive analysis.
    """
    
    # Metric weights for overall comparison
    METRIC_WEIGHTS = {
        'overall_score': 1.0,
        'title_score': 0.8,
        'meta_description_score': 0.7,
        'headers_score': 0.6,
        'content_score': 0.9,
        'technical_score': 0.9,
        'images_score': 0.5,
        'links_score': 0.6
    }
    
    @classmethod
    async def compare(
        cls,
        your_competitor_id: Optional[UUID],
        competitor_ids: List[UUID],
        db
    ) -> Dict:
        """Compare SEO metrics across competitors."""
        from sqlalchemy import select, func
        from app.models.seo import SeoAnalysis
        from app.models.competitor import Competitor
        
        # Get latest SEO analysis for each competitor
        analyses = {}
        
        for comp_id in competitor_ids:
            result = await db.execute(
                select(SeoAnalysis, Competitor.name)
                .join(Competitor)
                .where(SeoAnalysis.competitor_id == comp_id)
                .order_by(SeoAnalysis.analyzed_at.desc())
                .limit(1)
            )
            row = result.one_or_none()
            if row:
                analysis, name = row
                analyses[str(comp_id)] = {
                    'name': name,
                    'analysis': analysis
                }
        
        if not analyses:
            return {
                'metrics': [],
                'rankings': [],
                'insights': ['No SEO data available for comparison']
            }
        
        # Compare metrics
        metrics = cls._compare_metrics(analyses, your_competitor_id)
        
        # Generate rankings
        rankings = cls._generate_rankings(analyses, your_competitor_id)
        
        # Generate insights
        insights = cls._generate_insights(metrics, rankings, your_competitor_id)
        
        # Generate radar chart data
        radar_data = cls._generate_radar_data(analyses, your_competitor_id)
        
        return {
            'metrics': metrics,
            'rankings': rankings,
            'insights': insights,
            'radar_chart': radar_data,
            'competitor_count': len(analyses)
        }
    
    @classmethod
    def _compare_metrics(
        cls,
        analyses: Dict,
        your_competitor_id: Optional[UUID]
    ) -> List[Dict]:
        """Compare individual SEO metrics."""
        metrics_to_compare = [
            ('overall_score', 'Overall Score'),
            ('title_score', 'Title Optimization'),
            ('meta_description_score', 'Meta Description'),
            ('headers_score', 'Header Structure'),
            ('content_score', 'Content Quality'),
            ('technical_score', 'Technical SEO'),
            ('images_score', 'Image Optimization'),
            ('links_score', 'Link Profile')
        ]
        
        results = []
        your_id_str = str(your_competitor_id) if your_competitor_id else None
        
        for metric_key, metric_name in metrics_to_compare:
            values = {}
            
            for comp_id, data in analyses.items():
                analysis = data['analysis']
                value = getattr(analysis, metric_key, 0) or 0
                values[comp_id] = {
                    'name': data['name'],
                    'value': value
                }
            
            if not values:
                continue
            
            # Calculate stats
            all_values = [v['value'] for v in values.values()]
            avg = sum(all_values) / len(all_values)
            
            best_comp_id = max(values.keys(), key=lambda k: values[k]['value'])
            best_value = values[best_comp_id]['value']
            best_name = values[best_comp_id]['name']
            
            # Your value and rank
            your_value = values.get(your_id_str, {}).get('value') if your_id_str else None
            your_rank = 0
            
            if your_value is not None:
                sorted_values = sorted(all_values, reverse=True)
                your_rank = sorted_values.index(your_value) + 1
            
            results.append({
                'metric': metric_name,
                'key': metric_key,
                'your_value': your_value,
                'average': round(avg, 1),
                'best_value': best_value,
                'best_competitor': best_name,
                'your_rank': your_rank,
                'total': len(values),
                'competitors': {
                    data['name']: data['value']
                    for data in values.values()
                }
            })
        
        return results
    
    @classmethod
    def _generate_rankings(
        cls,
        analyses: Dict,
        your_competitor_id: Optional[UUID]
    ) -> List[Dict]:
        """Generate overall SEO rankings."""
        your_id_str = str(your_competitor_id) if your_competitor_id else None
        
        # Calculate weighted scores
        scores = []
        for comp_id, data in analyses.items():
            analysis = data['analysis']
            
            weighted_score = 0
            total_weight = 0
            
            for metric, weight in cls.METRIC_WEIGHTS.items():
                value = getattr(analysis, metric, 0) or 0
                weighted_score += value * weight
                total_weight += weight
            
            final_score = weighted_score / total_weight if total_weight > 0 else 0
            
            scores.append({
                'competitor_id': comp_id,
                'name': data['name'],
                'score': round(final_score, 1),
                'is_you': comp_id == your_id_str
            })
        
        # Sort by score
        scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Add ranks
        for i, score in enumerate(scores):
            score['rank'] = i + 1
        
        return scores
    
    @classmethod
    def _generate_insights(
        cls,
        metrics: List[Dict],
        rankings: List[Dict],
        your_competitor_id: Optional[UUID]
    ) -> List[Dict]:
        """Generate competitive insights."""
        insights = []
        your_id_str = str(your_competitor_id) if your_competitor_id else None
        
        if not your_id_str:
            insights.append({
                'type': 'info',
                'message': 'Add your website to get personalized insights'
            })
            return insights
        
        # Find your ranking
        your_rank = next(
            (r for r in rankings if r['is_you']),
            None
        )
        
        if your_rank:
            if your_rank['rank'] == 1:
                insights.append({
                    'type': 'success',
                    'message': f"You're leading in overall SEO with a score of {your_rank['score']}"
                })
            elif your_rank['rank'] <= 3:
                insights.append({
                    'type': 'info',
                    'message': f"You're ranked #{your_rank['rank']} in SEO performance"
                })
            else:
                insights.append({
                    'type': 'warning',
                    'message': f"You're ranked #{your_rank['rank']} - significant room for improvement"
                })
        
        # Analyze individual metrics
        for metric in metrics:
            if metric['your_value'] is None:
                continue
            
            your_val = metric['your_value']
            avg = metric['average']
            best = metric['best_value']
            
            if your_val >= best:
                insights.append({
                    'type': 'success',
                    'metric': metric['key'],
                    'message': f"Leading in {metric['metric']} ({your_val})"
                })
            elif your_val < avg * 0.8:
                gap = round(avg - your_val, 1)
                insights.append({
                    'type': 'danger',
                    'metric': metric['key'],
                    'message': f"{metric['metric']} is {gap} points below average",
                    'priority': 'high'
                })
            elif your_val < avg:
                insights.append({
                    'type': 'warning',
                    'metric': metric['key'],
                    'message': f"{metric['metric']} slightly below average"
                })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        insights.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 2))
        
        return insights[:10]
    
    @classmethod
    def _generate_radar_data(
        cls,
        analyses: Dict,
        your_competitor_id: Optional[UUID]
    ) -> Dict:
        """Generate data for radar chart visualization."""
        categories = [
            ('overall_score', 'Overall'),
            ('title_score', 'Title'),
            ('meta_description_score', 'Meta'),
            ('headers_score', 'Headers'),
            ('content_score', 'Content'),
            ('technical_score', 'Technical'),
            ('links_score', 'Links'),
            ('images_score', 'Images')
        ]
        
        your_id_str = str(your_competitor_id) if your_competitor_id else None
        
        datasets = []
        
        for comp_id, data in analyses.items():
            analysis = data['analysis']
            
            values = []
            for metric_key, _ in categories:
                value = getattr(analysis, metric_key, 0) or 0
                values.append(value)
            
            dataset = {
                'label': data['name'],
                'data': values,
                'is_you': comp_id == your_id_str
            }
            datasets.append(dataset)
        
        return {
            'labels': [cat[1] for cat in categories],
            'datasets': datasets
        }


class SeoTrendAnalyzer:
    """
    Analyzes SEO trends over time for a competitor.
    """
    
    @classmethod
    async def get_trends(
        cls,
        competitor_id: UUID,
        days: int,
        db
    ) -> Dict:
        """Get SEO score trends over time."""
        from sqlalchemy import select
        from datetime import datetime, timedelta
        from app.models.seo import SeoAnalysis
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        result = await db.execute(
            select(SeoAnalysis)
            .where(
                SeoAnalysis.competitor_id == competitor_id,
                SeoAnalysis.analyzed_at >= cutoff
            )
            .order_by(SeoAnalysis.analyzed_at.asc())
        )
        
        analyses = result.scalars().all()
        
        if not analyses:
            return {'data': [], 'trend': 'neutral'}
        
        # Build trend data
        data = []
        for analysis in analyses:
            data.append({
                'date': analysis.analyzed_at.isoformat(),
                'overall_score': analysis.overall_score,
                'technical_score': analysis.technical_score or 0,
                'content_score': analysis.content_score or 0
            })
        
        # Calculate trend direction
        if len(data) >= 2:
            first = data[0]['overall_score']
            last = data[-1]['overall_score']
            
            if last > first + 5:
                trend = 'improving'
            elif last < first - 5:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'neutral'
        
        return {
            'data': data,
            'trend': trend,
            'change': data[-1]['overall_score'] - data[0]['overall_score'] if len(data) >= 2 else 0
        }


class SeoAuditReporter:
    """
    Generates comprehensive SEO audit reports.
    """
    
    @classmethod
    async def generate_report(
        cls,
        competitor_id: UUID,
        db
    ) -> Dict:
        """Generate a full SEO audit report."""
        from sqlalchemy import select
        from app.models.seo import SeoAnalysis
        from app.models.competitor import Competitor
        import json
        
        # Get latest analysis
        result = await db.execute(
            select(SeoAnalysis, Competitor.name, Competitor.url)
            .join(Competitor)
            .where(SeoAnalysis.competitor_id == competitor_id)
            .order_by(SeoAnalysis.analyzed_at.desc())
            .limit(1)
        )
        
        row = result.one_or_none()
        if not row:
            return {'error': 'No SEO analysis found'}
        
        analysis, name, url = row
        
        # Build report sections
        sections = []
        
        # Overall Score
        sections.append({
            'title': 'Overall Score',
            'score': analysis.overall_score,
            'status': cls._get_status(analysis.overall_score),
            'items': []
        })
        
        # On-Page SEO
        on_page_items = []
        on_page_items.append(cls._create_item(
            'Page Title',
            analysis.title_score or 0,
            f'"{analysis.title}"' if analysis.title else 'Missing',
            cls._get_title_recommendation(analysis.title, analysis.title_length or 0)
        ))
        on_page_items.append(cls._create_item(
            'Meta Description',
            analysis.meta_description_score or 0,
            f'{analysis.meta_description_length or 0} characters',
            cls._get_meta_recommendation(analysis.meta_description, analysis.meta_description_length or 0)
        ))
        on_page_items.append(cls._create_item(
            'Header Structure',
            analysis.headers_score or 0,
            f'H1: {analysis.h1_count or 0}, H2: {analysis.h2_count or 0}, H3: {analysis.h3_count or 0}',
            cls._get_headers_recommendation(analysis.h1_count or 0, analysis.h2_count or 0)
        ))
        
        sections.append({
            'title': 'On-Page SEO',
            'score': (
                (analysis.title_score or 0) + 
                (analysis.meta_description_score or 0) + 
                (analysis.headers_score or 0)
            ) // 3,
            'status': cls._get_status((analysis.title_score or 0 + analysis.meta_description_score or 0) // 2),
            'items': on_page_items
        })
        
        # Technical SEO
        tech_items = []
        tech_items.append(cls._create_item(
            'HTTPS/SSL',
            100 if analysis.has_ssl else 0,
            'Enabled' if analysis.has_ssl else 'Not Enabled',
            None if analysis.has_ssl else 'Enable HTTPS for security and SEO benefits'
        ))
        tech_items.append(cls._create_item(
            'Sitemap',
            100 if analysis.has_sitemap else 0,
            'Found' if analysis.has_sitemap else 'Not Found',
            None if analysis.has_sitemap else 'Create and submit an XML sitemap'
        ))
        tech_items.append(cls._create_item(
            'Robots.txt',
            100 if analysis.has_robots_txt else 0,
            'Found' if analysis.has_robots_txt else 'Not Found',
            None if analysis.has_robots_txt else 'Create a robots.txt file'
        ))
        tech_items.append(cls._create_item(
            'Canonical Tag',
            100 if analysis.has_canonical else 0,
            'Present' if analysis.has_canonical else 'Missing',
            None if analysis.has_canonical else 'Add canonical tags to prevent duplicate content issues'
        ))
        tech_items.append(cls._create_item(
            'Schema Markup',
            100 if analysis.has_schema_markup else 0,
            'Found' if analysis.has_schema_markup else 'Not Found',
            None if analysis.has_schema_markup else 'Add structured data for rich snippets'
        ))
        
        sections.append({
            'title': 'Technical SEO',
            'score': analysis.technical_score or 0,
            'status': cls._get_status(analysis.technical_score or 0),
            'items': tech_items
        })
        
        # Content
        content_items = []
        content_items.append(cls._create_item(
            'Word Count',
            cls._score_word_count(analysis.word_count or 0),
            f'{analysis.word_count or 0} words',
            cls._get_word_count_recommendation(analysis.word_count or 0)
        ))
        
        sections.append({
            'title': 'Content',
            'score': analysis.content_score or 0,
            'status': cls._get_status(analysis.content_score or 0),
            'items': content_items
        })
        
        # Images
        image_items = []
        image_items.append(cls._create_item(
            'Alt Text Coverage',
            analysis.images_score or 0,
            f'{analysis.images_with_alt or 0}/{analysis.total_images or 0} images have alt text',
            cls._get_images_recommendation(analysis.images_with_alt or 0, analysis.total_images or 0)
        ))
        
        sections.append({
            'title': 'Images',
            'score': analysis.images_score or 0,
            'status': cls._get_status(analysis.images_score or 0),
            'items': image_items
        })
        
        # Links
        link_items = []
        link_items.append(cls._create_item(
            'Internal Links',
            min(100, (analysis.internal_links or 0) * 10),
            f'{analysis.internal_links or 0} internal links',
            None if (analysis.internal_links or 0) >= 5 else 'Add more internal links'
        ))
        link_items.append(cls._create_item(
            'External Links',
            min(100, (analysis.external_links or 0) * 15),
            f'{analysis.external_links or 0} external links',
            None if (analysis.external_links or 0) >= 2 else 'Add relevant external links'
        ))
        
        sections.append({
            'title': 'Links',
            'score': analysis.links_score or 0,
            'status': cls._get_status(analysis.links_score or 0),
            'items': link_items
        })
        
        return {
            'competitor_name': name,
            'url': url,
            'analyzed_at': analysis.analyzed_at.isoformat(),
            'overall_score': analysis.overall_score,
            'overall_status': cls._get_status(analysis.overall_score),
            'sections': sections,
            'priority_fixes': cls._get_priority_fixes(sections)
        }
    
    @classmethod
    def _create_item(cls, name: str, score: int, value: str, recommendation: Optional[str]) -> Dict:
        return {
            'name': name,
            'score': score,
            'status': cls._get_status(score),
            'value': value,
            'recommendation': recommendation
        }
    
    @classmethod
    def _get_status(cls, score: int) -> str:
        if score >= 80:
            return 'good'
        elif score >= 50:
            return 'warning'
        return 'error'
    
    @classmethod
    def _get_title_recommendation(cls, title: Optional[str], length: int) -> Optional[str]:
        if not title:
            return 'Add a unique, descriptive page title'
        if length < 30:
            return 'Title is too short - aim for 50-60 characters'
        if length > 70:
            return 'Title is too long - it may be truncated in search results'
        return None
    
    @classmethod
    def _get_meta_recommendation(cls, desc: Optional[str], length: int) -> Optional[str]:
        if not desc:
            return 'Add a meta description to improve click-through rates'
        if length < 120:
            return 'Meta description is too short - aim for 150-160 characters'
        if length > 170:
            return 'Meta description is too long - it may be truncated'
        return None
    
    @classmethod
    def _get_headers_recommendation(cls, h1: int, h2: int) -> Optional[str]:
        if h1 == 0:
            return 'Add an H1 heading to the page'
        if h1 > 1:
            return 'Use only one H1 heading per page'
        if h2 == 0:
            return 'Add H2 subheadings to structure your content'
        return None
    
    @classmethod
    def _score_word_count(cls, count: int) -> int:
        if count >= 2000:
            return 100
        elif count >= 1000:
            return 80
        elif count >= 500:
            return 60
        elif count >= 300:
            return 40
        return 20
    
    @classmethod
    def _get_word_count_recommendation(cls, count: int) -> Optional[str]:
        if count < 300:
            return 'Content is too thin - aim for at least 500 words'
        if count < 1000:
            return 'Consider expanding content for better rankings'
        return None
    
    @classmethod
    def _get_images_recommendation(cls, with_alt: int, total: int) -> Optional[str]:
        if total == 0:
            return None
        ratio = with_alt / total
        if ratio < 0.5:
            return 'Add descriptive alt text to images for accessibility and SEO'
        elif ratio < 1.0:
            return 'Some images are missing alt text'
        return None
    
    @classmethod
    def _get_priority_fixes(cls, sections: List[Dict]) -> List[Dict]:
        """Extract priority fixes from report."""
        fixes = []
        
        for section in sections:
            for item in section.get('items', []):
                if item.get('status') == 'error' and item.get('recommendation'):
                    fixes.append({
                        'section': section['title'],
                        'item': item['name'],
                        'recommendation': item['recommendation'],
                        'priority': 'high'
                    })
                elif item.get('status') == 'warning' and item.get('recommendation'):
                    fixes.append({
                        'section': section['title'],
                        'item': item['name'],
                        'recommendation': item['recommendation'],
                        'priority': 'medium'
                    })
        
        # Sort by priority
        fixes.sort(key=lambda x: 0 if x['priority'] == 'high' else 1)
        
        return fixes[:10]
