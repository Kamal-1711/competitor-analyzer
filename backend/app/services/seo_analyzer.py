import re
import json
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import httpx
from loguru import logger


class SeoAnalyzer:
    """
    Comprehensive SEO analysis engine.
    Analyzes on-page, technical, and content SEO factors.
    """
    
    def __init__(self):
        self.scores = {}
        
    async def analyze(self, url: str, competitor_id: UUID) -> dict:
        """Run full SEO analysis on a URL."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, follow_redirects=True)
                html = response.text
                final_url = str(response.url)
                
            soup = BeautifulSoup(html, "lxml")
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Run all analyses
            on_page = self._analyze_on_page(soup)
            technical = await self._analyze_technical(base_url, soup)
            content = self._analyze_content(soup)
            links = self._analyze_links(soup, base_url)
            images = self._analyze_images(soup)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                on_page, technical, content, links, images
            )
            
            # Save to database
            from app.database import async_session_maker
            from app.models.seo import SeoAnalysis
            
            async with async_session_maker() as db:
                analysis = SeoAnalysis(
                    competitor_id=competitor_id,
                    url=final_url,
                    overall_score=overall_score,
                    
                    # On-page
                    title=on_page["title"],
                    title_length=on_page["title_length"],
                    title_score=on_page["title_score"],
                    meta_description=on_page["meta_description"],
                    meta_description_length=on_page["meta_description_length"],
                    meta_description_score=on_page["meta_description_score"],
                    
                    # Headers
                    h1_count=on_page["h1_count"],
                    h2_count=on_page["h2_count"],
                    h3_count=on_page["h3_count"],
                    headers_score=on_page["headers_score"],
                    
                    # Content
                    word_count=content["word_count"],
                    content_score=content["content_score"],
                    
                    # Images
                    images_count=images["total"],
                    images_with_alt=images["with_alt"],
                    images_score=images["score"],
                    
                    # Links
                    internal_links=links["internal"],
                    external_links=links["external"],
                    broken_links=0,  # Would need async checking
                    links_score=links["score"],
                    
                    # Technical
                    has_ssl=technical["has_ssl"],
                    has_sitemap=technical["has_sitemap"],
                    has_robots_meta=technical["has_robots_txt"],
                    has_canonical=technical["has_canonical"],
                    mobile_friendly=True,  # Would need more complex check
                    technical_score=technical["score"],
                    
                    # Store recommendations as JSON
                    recommendations={
                        "on_page": on_page,
                        "technical": technical,
                        "content": content,
                        "links": links,
                        "images": images
                    }
                )
                
                db.add(analysis)
                await db.commit()
                
            return {
                "overall_score": overall_score,
                "on_page": on_page,
                "technical": technical,
                "content": content
            }
            
        except Exception as e:
            logger.error(f"SEO analysis failed for {url}: {e}")
            raise
            
    def _analyze_on_page(self, soup: BeautifulSoup) -> dict:
        """Analyze on-page SEO factors."""
        
        # Title
        title = ""
        title_score = 0
        if soup.title:
            title = soup.title.string or ""
            title_length = len(title)
            
            if 50 <= title_length <= 60:
                title_score = 100
            elif 40 <= title_length <= 70:
                title_score = 80
            elif 30 <= title_length <= 80:
                title_score = 60
            elif title_length > 0:
                title_score = 40
        else:
            title_length = 0
            
        # Meta description
        meta_desc = ""
        meta_desc_score = 0
        meta_tag = soup.find("meta", {"name": "description"})
        if meta_tag:
            meta_desc = meta_tag.get("content", "")
            meta_length = len(meta_desc)
            
            if 150 <= meta_length <= 160:
                meta_desc_score = 100
            elif 120 <= meta_length <= 180:
                meta_desc_score = 80
            elif 80 <= meta_length <= 200:
                meta_desc_score = 60
            elif meta_length > 0:
                meta_desc_score = 40
        else:
            meta_length = 0
            
        # Headers
        h1_tags = soup.find_all("h1")
        h1_count = len(h1_tags)
        h1_content = h1_tags[0].get_text(strip=True) if h1_tags else None
        h2_count = len(soup.find_all("h2"))
        h3_count = len(soup.find_all("h3"))
        
        headers_score = 0
        if h1_count == 1:
            headers_score += 50
        elif h1_count > 0:
            headers_score += 25
            
        if h2_count >= 2:
            headers_score += 30
        elif h2_count > 0:
            headers_score += 15
            
        if h3_count >= 2:
            headers_score += 20
        elif h3_count > 0:
            headers_score += 10
            
        return {
            "title": title[:512],
            "title_length": title_length,
            "title_score": title_score,
            "meta_description": meta_desc[:2000],
            "meta_description_length": meta_length,
            "meta_description_score": meta_desc_score,
            "h1_count": h1_count,
            "h1_content": h1_content[:500] if h1_content else None,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "headers_score": headers_score
        }
        
    async def _analyze_technical(self, base_url: str, soup: BeautifulSoup) -> dict:
        """Analyze technical SEO factors."""
        
        parsed = urlparse(base_url)
        has_ssl = parsed.scheme == "https"
        
        # Check canonical
        canonical = soup.find("link", {"rel": "canonical"})
        has_canonical = bool(canonical)
        
        # Check schema markup
        schema_scripts = soup.find_all("script", {"type": "application/ld+json"})
        has_schema = len(schema_scripts) > 0
        
        # Check sitemap and robots.txt
        has_sitemap = False
        has_robots = False
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(f"{base_url}/sitemap.xml")
                has_sitemap = resp.status_code == 200
            except:
                pass
                
            try:
                resp = await client.get(f"{base_url}/robots.txt")
                has_robots = resp.status_code == 200
            except:
                pass
                
        # Calculate score
        score = 0
        if has_ssl:
            score += 30
        if has_canonical:
            score += 20
        if has_schema:
            score += 20
        if has_sitemap:
            score += 15
        if has_robots:
            score += 15
            
        return {
            "has_ssl": has_ssl,
            "has_canonical": has_canonical,
            "has_schema": has_schema,
            "has_sitemap": has_sitemap,
            "has_robots_txt": has_robots,
            "score": score
        }
        
    def _analyze_content(self, soup: BeautifulSoup) -> dict:
        """Analyze content quality."""
        
        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
            
        text = soup.get_text(separator=" ", strip=True)
        words = text.lower().split()
        word_count = len(words)
        
        # Calculate keyword density
        word_freq = {}
        for word in words:
            word = re.sub(r'[^\w]', '', word)
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
                
        # Get top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        top_keywords = dict(sorted_words[:20])
        
        # Content score based on word count
        content_score = 0
        if word_count >= 2000:
            content_score = 100
        elif word_count >= 1500:
            content_score = 90
        elif word_count >= 1000:
            content_score = 80
        elif word_count >= 500:
            content_score = 60
        elif word_count >= 300:
            content_score = 40
        else:
            content_score = 20
            
        return {
            "word_count": word_count,
            "keyword_density": top_keywords,
            "content_score": content_score
        }
        
    def _analyze_links(self, soup: BeautifulSoup, base_url: str) -> dict:
        """Analyze internal and external links."""
        
        internal = 0
        external = 0
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/") or href.startswith(base_url):
                internal += 1
            elif href.startswith("http"):
                external += 1
                
        # Score based on link balance
        score = 50
        if internal >= 5:
            score += 25
        if 3 <= external <= 10:
            score += 25
        elif external > 0:
            score += 15
            
        return {
            "internal": internal,
            "external": external,
            "score": min(score, 100)
        }
        
    def _analyze_images(self, soup: BeautifulSoup) -> dict:
        """Analyze image optimization."""
        
        images = soup.find_all("img")
        total = len(images)
        with_alt = sum(1 for img in images if img.get("alt"))
        
        score = 0
        if total == 0:
            score = 100  # No images to optimize
        else:
            score = int((with_alt / total) * 100)
            
        return {
            "total": total,
            "with_alt": with_alt,
            "score": score
        }
        
    def _calculate_overall_score(
        self,
        on_page: dict,
        technical: dict,
        content: dict,
        links: dict,
        images: dict
    ) -> int:
        """Calculate weighted overall SEO score."""
        
        weights = {
            "title": 0.15,
            "meta": 0.10,
            "headers": 0.10,
            "content": 0.20,
            "technical": 0.25,
            "links": 0.10,
            "images": 0.10
        }
        
        score = (
            on_page["title_score"] * weights["title"] +
            on_page["meta_description_score"] * weights["meta"] +
            on_page["headers_score"] * weights["headers"] +
            content["content_score"] * weights["content"] +
            technical["score"] * weights["technical"] +
            links["score"] * weights["links"] +
            images["score"] * weights["images"]
        )
        
        return int(score)
