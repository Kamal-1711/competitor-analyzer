"""
Advanced SEO analysis utilities for Web-Spy.
Includes: Schema.org detection, Open Graph, Twitter Cards, Core Web Vitals simulation.
"""

import re
import json
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass, field
from collections import Counter

from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class SchemaMarkup:
    """Represents detected schema.org markup."""
    type: str
    properties: Dict
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)


class SchemaAnalyzer:
    """
    Analyzes schema.org structured data markup.
    Supports JSON-LD, Microdata, and RDFa formats.
    """
    
    # Important schema types for SEO
    PRIORITY_SCHEMAS = {
        'Organization', 'LocalBusiness', 'Product', 'Article', 
        'BlogPosting', 'BreadcrumbList', 'FAQPage', 'HowTo',
        'Review', 'Recipe', 'Event', 'Person', 'WebSite', 'WebPage'
    }
    
    @classmethod
    def analyze(cls, soup: BeautifulSoup) -> Dict:
        """Analyze all schema markup on a page."""
        schemas = []
        
        # JSON-LD (preferred format)
        jsonld_schemas = cls._extract_jsonld(soup)
        schemas.extend(jsonld_schemas)
        
        # Microdata
        microdata_schemas = cls._extract_microdata(soup)
        schemas.extend(microdata_schemas)
        
        # Calculate score
        score = cls._calculate_score(schemas)
        
        return {
            'schemas': [
                {
                    'type': s.type,
                    'properties': list(s.properties.keys())[:10],
                    'is_valid': s.is_valid,
                    'errors': s.errors
                }
                for s in schemas
            ],
            'count': len(schemas),
            'has_priority_schema': any(s.type in cls.PRIORITY_SCHEMAS for s in schemas),
            'score': score,
            'recommendations': cls._get_recommendations(schemas)
        }
    
    @classmethod
    def _extract_jsonld(cls, soup: BeautifulSoup) -> List[SchemaMarkup]:
        """Extract JSON-LD structured data."""
        schemas = []
        
        for script in soup.find_all('script', {'type': 'application/ld+json'}):
            try:
                content = script.string
                if not content:
                    continue
                
                data = json.loads(content)
                
                # Handle @graph arrays
                if '@graph' in data:
                    items = data['@graph']
                elif isinstance(data, list):
                    items = data
                else:
                    items = [data]
                
                for item in items:
                    schema_type = item.get('@type', 'Unknown')
                    if isinstance(schema_type, list):
                        schema_type = schema_type[0] if schema_type else 'Unknown'
                    
                    schemas.append(SchemaMarkup(
                        type=schema_type,
                        properties=item,
                        is_valid=True
                    ))
                    
            except json.JSONDecodeError as e:
                schemas.append(SchemaMarkup(
                    type='Invalid',
                    properties={},
                    is_valid=False,
                    errors=[f'JSON parse error: {str(e)}']
                ))
        
        return schemas
    
    @classmethod
    def _extract_microdata(cls, soup: BeautifulSoup) -> List[SchemaMarkup]:
        """Extract Microdata structured data."""
        schemas = []
        
        for item in soup.find_all(itemscope=True):
            item_type = item.get('itemtype', '')
            if item_type:
                # Extract type from URL
                schema_type = item_type.split('/')[-1] if '/' in item_type else item_type
                
                properties = {}
                for prop in item.find_all(itemprop=True):
                    prop_name = prop.get('itemprop')
                    prop_value = prop.get('content') or prop.get_text(strip=True)
                    properties[prop_name] = prop_value
                
                schemas.append(SchemaMarkup(
                    type=schema_type,
                    properties=properties
                ))
        
        return schemas
    
    @classmethod
    def _calculate_score(cls, schemas: List[SchemaMarkup]) -> int:
        """Calculate schema markup score."""
        if not schemas:
            return 0
        
        score = 20  # Base score for having any schema
        
        # Points for valid schemas
        valid_count = sum(1 for s in schemas if s.is_valid)
        score += min(valid_count * 10, 30)
        
        # Points for priority schemas
        priority_count = sum(1 for s in schemas if s.type in cls.PRIORITY_SCHEMAS)
        score += min(priority_count * 15, 30)
        
        # Bonus for multiple schema types
        unique_types = len(set(s.type for s in schemas))
        if unique_types >= 3:
            score += 20
        elif unique_types >= 2:
            score += 10
        
        return min(score, 100)
    
    @classmethod
    def _get_recommendations(cls, schemas: List[SchemaMarkup]) -> List[str]:
        """Generate schema markup recommendations."""
        recommendations = []
        
        if not schemas:
            recommendations.append("Add JSON-LD structured data for better search visibility")
        
        types_present = {s.type for s in schemas}
        
        if 'Organization' not in types_present and 'LocalBusiness' not in types_present:
            recommendations.append("Add Organization or LocalBusiness schema")
        
        if 'BreadcrumbList' not in types_present:
            recommendations.append("Add BreadcrumbList schema for navigation")
        
        if 'WebSite' not in types_present:
            recommendations.append("Add WebSite schema with SearchAction for sitelinks")
        
        # Check for invalid schemas
        invalid = [s for s in schemas if not s.is_valid]
        if invalid:
            recommendations.append(f"Fix {len(invalid)} invalid schema markup(s)")
        
        return recommendations[:5]


class OpenGraphAnalyzer:
    """
    Analyzes Open Graph and social media meta tags.
    """
    
    # Required OG tags
    REQUIRED_TAGS = {'og:title', 'og:type', 'og:image', 'og:url'}
    
    # Recommended OG tags
    RECOMMENDED_TAGS = {'og:description', 'og:site_name', 'og:locale'}
    
    @classmethod
    def analyze(cls, soup: BeautifulSoup) -> Dict:
        """Analyze Open Graph meta tags."""
        og_tags = {}
        twitter_tags = {}
        
        for meta in soup.find_all('meta'):
            property_attr = meta.get('property', '')
            name_attr = meta.get('name', '')
            content = meta.get('content', '')
            
            if property_attr.startswith('og:'):
                og_tags[property_attr] = content
            elif name_attr.startswith('twitter:'):
                twitter_tags[name_attr] = content
        
        # Calculate scores
        og_score = cls._calculate_og_score(og_tags)
        twitter_score = cls._calculate_twitter_score(twitter_tags)
        
        return {
            'open_graph': {
                'tags': og_tags,
                'has_required': cls.REQUIRED_TAGS.issubset(og_tags.keys()),
                'missing_required': list(cls.REQUIRED_TAGS - og_tags.keys()),
                'score': og_score
            },
            'twitter_cards': {
                'tags': twitter_tags,
                'card_type': twitter_tags.get('twitter:card', 'none'),
                'score': twitter_score
            },
            'overall_score': (og_score + twitter_score) // 2,
            'recommendations': cls._get_recommendations(og_tags, twitter_tags)
        }
    
    @classmethod
    def _calculate_og_score(cls, tags: Dict) -> int:
        """Calculate Open Graph score."""
        if not tags:
            return 0
        
        score = 20  # Base score for having OG tags
        
        # Required tags
        required_present = sum(1 for tag in cls.REQUIRED_TAGS if tag in tags)
        score += required_present * 15
        
        # Recommended tags
        recommended_present = sum(1 for tag in cls.RECOMMENDED_TAGS if tag in tags)
        score += recommended_present * 5
        
        # Check image quality hints
        if 'og:image' in tags:
            if 'og:image:width' in tags and 'og:image:height' in tags:
                score += 10
        
        return min(score, 100)
    
    @classmethod
    def _calculate_twitter_score(cls, tags: Dict) -> int:
        """Calculate Twitter Card score."""
        if not tags:
            return 0
        
        score = 20
        
        # Card type
        card_type = tags.get('twitter:card', '')
        if card_type == 'summary_large_image':
            score += 30
        elif card_type == 'summary':
            score += 20
        elif card_type:
            score += 10
        
        # Other tags
        if 'twitter:title' in tags:
            score += 15
        if 'twitter:description' in tags:
            score += 15
        if 'twitter:image' in tags:
            score += 20
        
        return min(score, 100)
    
    @classmethod
    def _get_recommendations(cls, og_tags: Dict, twitter_tags: Dict) -> List[str]:
        """Generate social meta recommendations."""
        recommendations = []
        
        if not og_tags:
            recommendations.append("Add Open Graph meta tags for better social sharing")
        else:
            missing = cls.REQUIRED_TAGS - og_tags.keys()
            if missing:
                recommendations.append(f"Add missing OG tags: {', '.join(missing)}")
            
            if 'og:image' in og_tags and 'og:image:width' not in og_tags:
                recommendations.append("Specify og:image dimensions for faster rendering")
        
        if not twitter_tags:
            recommendations.append("Add Twitter Card meta tags")
        elif twitter_tags.get('twitter:card') != 'summary_large_image':
            recommendations.append("Use 'summary_large_image' Twitter card for better engagement")
        
        return recommendations[:5]


class KeywordAnalyzer:
    """
    Advanced keyword analysis including density, prominence, and semantic relevance.
    """
    
    # Common stop words to exclude
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'it',
        'its', 'you', 'your', 'we', 'our', 'they', 'their', 'he', 'she', 'his',
        'her', 'i', 'me', 'my', 'not', 'no', 'so', 'if', 'then', 'than', 'when'
    }
    
    @classmethod
    def analyze(cls, soup: BeautifulSoup) -> Dict:
        """Perform comprehensive keyword analysis."""
        # Extract text from different areas
        title_text = cls._get_title_text(soup)
        h1_text = cls._get_header_text(soup, 'h1')
        h2_text = cls._get_header_text(soup, 'h2')
        body_text = cls._get_body_text(soup)
        meta_desc = cls._get_meta_description(soup)
        
        # Tokenize
        title_words = cls._tokenize(title_text)
        h1_words = cls._tokenize(h1_text)
        h2_words = cls._tokenize(h2_text)
        body_words = cls._tokenize(body_text)
        meta_words = cls._tokenize(meta_desc)
        
        # Calculate keyword density
        all_words = body_words
        word_count = len(all_words)
        
        word_freq = Counter(all_words)
        top_keywords = word_freq.most_common(20)
        
        # Calculate density percentages
        keyword_density = {
            word: round(count / word_count * 100, 2) if word_count > 0 else 0
            for word, count in top_keywords
        }
        
        # Analyze keyword prominence (position-based importance)
        prominence = cls._calculate_prominence(
            top_keywords, title_words, h1_words, h2_words, meta_words
        )
        
        # Find n-grams (phrases)
        bigrams = cls._extract_ngrams(all_words, 2)
        trigrams = cls._extract_ngrams(all_words, 3)
        
        return {
            'word_count': word_count,
            'unique_words': len(set(all_words)),
            'keyword_density': keyword_density,
            'top_keywords': [
                {
                    'keyword': word,
                    'count': count,
                    'density': keyword_density.get(word, 0),
                    'prominence': prominence.get(word, 0)
                }
                for word, count in top_keywords[:10]
            ],
            'top_phrases': {
                'two_word': bigrams[:5],
                'three_word': trigrams[:5]
            },
            'recommendations': cls._get_recommendations(
                keyword_density, prominence, title_words, h1_words
            )
        }
    
    @classmethod
    def _tokenize(cls, text: str) -> List[str]:
        """Tokenize text into words."""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return [w for w in words if w not in cls.STOP_WORDS]
    
    @classmethod
    def _get_title_text(cls, soup: BeautifulSoup) -> str:
        """Extract title text."""
        return soup.title.string if soup.title else ""
    
    @classmethod
    def _get_header_text(cls, soup: BeautifulSoup, tag: str) -> str:
        """Extract text from header tags."""
        headers = soup.find_all(tag)
        return " ".join(h.get_text(strip=True) for h in headers)
    
    @classmethod
    def _get_body_text(cls, soup: BeautifulSoup) -> str:
        """Extract main body text."""
        # Clone soup to avoid modifying original
        body = soup.find('body')
        if not body:
            return ""
        
        # Create a copy and remove unwanted elements
        text_parts = []
        for element in body.stripped_strings:
            text_parts.append(element)
        
        return " ".join(text_parts)
    
    @classmethod
    def _get_meta_description(cls, soup: BeautifulSoup) -> str:
        """Extract meta description."""
        meta = soup.find('meta', {'name': 'description'})
        return meta.get('content', '') if meta else ""
    
    @classmethod
    def _calculate_prominence(
        cls,
        top_keywords: List[Tuple[str, int]],
        title_words: List[str],
        h1_words: List[str],
        h2_words: List[str],
        meta_words: List[str]
    ) -> Dict[str, int]:
        """Calculate keyword prominence based on position."""
        prominence = {}
        
        for word, _ in top_keywords:
            score = 0
            
            if word in title_words:
                score += 40  # Title is most important
            
            if word in h1_words:
                score += 30  # H1 is second most important
            
            if word in h2_words:
                score += 15  # H2 headers
            
            if word in meta_words:
                score += 15  # Meta description
            
            prominence[word] = min(score, 100)
        
        return prominence
    
    @classmethod
    def _extract_ngrams(cls, words: List[str], n: int) -> List[Tuple[str, int]]:
        """Extract n-grams from word list."""
        if len(words) < n:
            return []
        
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = " ".join(words[i:i+n])
            ngrams.append(ngram)
        
        return Counter(ngrams).most_common(10)
    
    @classmethod
    def _get_recommendations(
        cls,
        density: Dict,
        prominence: Dict,
        title_words: List[str],
        h1_words: List[str]
    ) -> List[str]:
        """Generate keyword recommendations."""
        recommendations = []
        
        # Check for keyword stuffing (density > 3%)
        stuffed = [k for k, v in density.items() if v > 3.0]
        if stuffed:
            recommendations.append(f"Reduce keyword density for: {', '.join(stuffed[:3])}")
        
        # Check if top keywords are in title
        top_keywords = list(density.keys())[:5]
        missing_in_title = [k for k in top_keywords if k not in title_words]
        if missing_in_title:
            recommendations.append(f"Add top keywords to title: {', '.join(missing_in_title[:2])}")
        
        # Check if top keywords are in H1
        missing_in_h1 = [k for k in top_keywords if k not in h1_words]
        if missing_in_h1:
            recommendations.append(f"Include keywords in H1: {', '.join(missing_in_h1[:2])}")
        
        return recommendations[:5]


class PageSpeedEstimator:
    """
    Estimates page speed metrics based on HTML analysis.
    Note: For accurate metrics, use Google PageSpeed Insights API.
    """
    
    @classmethod
    def estimate(cls, soup: BeautifulSoup, html: str) -> Dict:
        """Estimate page speed metrics."""
        page_size = len(html.encode('utf-8'))
        
        # Count resources
        scripts = soup.find_all('script')
        external_scripts = [s for s in scripts if s.get('src')]
        inline_scripts = [s for s in scripts if s.string and len(s.string) > 100]
        
        stylesheets = soup.find_all('link', {'rel': 'stylesheet'})
        inline_styles = soup.find_all('style')
        
        images = soup.find_all('img')
        lazy_images = [img for img in images if img.get('loading') == 'lazy']
        
        # Check for performance optimizations
        has_async_scripts = any(s.get('async') or s.get('defer') for s in external_scripts)
        has_preload = bool(soup.find('link', {'rel': 'preload'}))
        has_preconnect = bool(soup.find('link', {'rel': 'preconnect'}))
        
        # Calculate estimated metrics
        estimated_fcp = cls._estimate_fcp(page_size, len(external_scripts), len(stylesheets))
        estimated_lcp = cls._estimate_lcp(page_size, len(images), has_lazy_images=len(lazy_images) > 0)
        
        # Performance score
        score = cls._calculate_score(
            page_size, external_scripts, stylesheets, images,
            has_async_scripts, has_preload, has_preconnect
        )
        
        return {
            'page_size_bytes': page_size,
            'page_size_kb': round(page_size / 1024, 2),
            'resources': {
                'external_scripts': len(external_scripts),
                'inline_scripts': len(inline_scripts),
                'stylesheets': len(stylesheets),
                'inline_styles': len(inline_styles),
                'images': len(images),
                'lazy_images': len(lazy_images)
            },
            'optimizations': {
                'has_async_scripts': has_async_scripts,
                'has_preload': has_preload,
                'has_preconnect': has_preconnect,
                'has_lazy_loading': len(lazy_images) > 0
            },
            'estimated_metrics': {
                'fcp_ms': estimated_fcp,
                'lcp_ms': estimated_lcp
            },
            'score': score,
            'recommendations': cls._get_recommendations(
                page_size, external_scripts, stylesheets, images,
                has_async_scripts, len(lazy_images)
            )
        }
    
    @classmethod
    def _estimate_fcp(cls, page_size: int, scripts: int, stylesheets: int) -> int:
        """Estimate First Contentful Paint in ms."""
        base = 800
        base += (page_size // 10000) * 100
        base += scripts * 50
        base += stylesheets * 30
        return min(base, 5000)
    
    @classmethod
    def _estimate_lcp(cls, page_size: int, images: int, has_lazy_images: bool) -> int:
        """Estimate Largest Contentful Paint in ms."""
        base = 1200
        base += (page_size // 10000) * 150
        
        if has_lazy_images:
            base += images * 20
        else:
            base += images * 50
        
        return min(base, 8000)
    
    @classmethod
    def _calculate_score(
        cls,
        page_size: int,
        scripts: List,
        stylesheets: List,
        images: List,
        has_async: bool,
        has_preload: bool,
        has_preconnect: bool
    ) -> int:
        """Calculate performance score."""
        score = 100
        
        # Penalize large page size
        if page_size > 500000:
            score -= 30
        elif page_size > 200000:
            score -= 15
        elif page_size > 100000:
            score -= 5
        
        # Penalize many resources
        score -= min(len(scripts) * 2, 20)
        score -= min(len(stylesheets) * 3, 15)
        
        # Bonus for optimizations
        if has_async:
            score += 10
        if has_preload:
            score += 5
        if has_preconnect:
            score += 5
        
        return max(0, min(score, 100))
    
    @classmethod
    def _get_recommendations(
        cls,
        page_size: int,
        scripts: List,
        stylesheets: List,
        images: List,
        has_async: bool,
        lazy_count: int
    ) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        if page_size > 200000:
            recommendations.append(f"Reduce page size (currently {page_size // 1024}KB)")
        
        if len(scripts) > 5 and not has_async:
            recommendations.append("Add async/defer to script tags")
        
        if len(stylesheets) > 3:
            recommendations.append("Combine or inline critical CSS")
        
        if len(images) > 5 and lazy_count == 0:
            recommendations.append("Implement lazy loading for images")
        
        if len(images) > 0:
            recommendations.append("Use next-gen image formats (WebP, AVIF)")
        
        return recommendations[:5]
