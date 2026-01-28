import hashlib
import re
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from bs4 import BeautifulSoup
from loguru import logger
import httpx

from app.models.content import Content, ContentChange, ContentType
from app.models.alert import Alert, AlertType, AlertSeverity


class ContentTracker:
    """
    Service for tracking content changes on competitor websites.
    Detects new pages, content updates, and generates change diffs.
    """
    
    def __init__(self):
        self.min_content_length = 100  # Minimum characters to track
        
    def calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content."""
        normalized = re.sub(r'\s+', ' ', content.strip().lower())
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def extract_main_content(self, html: str) -> str:
        """Extract main content from HTML, removing navigation, footers, etc."""
        soup = BeautifulSoup(html, "lxml")
        
        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        
        # Try to find main content area
        main_content = soup.find("main") or soup.find("article") or soup.find(id="content") or soup.find(class_="content")
        
        if main_content:
            text = main_content.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)
        
        return text
    
    def categorize_content(self, url: str, title: str, content: str) -> ContentType:
        """Categorize content based on URL patterns and content analysis."""
        url_lower = url.lower()
        title_lower = title.lower()
        
        # URL-based categorization
        if "/blog" in url_lower or "/post" in url_lower or "/article" in url_lower:
            return ContentType.BLOG
        if "/product" in url_lower or "/shop" in url_lower or "/item" in url_lower:
            return ContentType.PRODUCT
        if "/pricing" in url_lower or "/plans" in url_lower or "/subscription" in url_lower:
            return ContentType.PRICING
        if "/docs" in url_lower or "/documentation" in url_lower or "/help" in url_lower:
            return ContentType.DOCUMENTATION
        if "/about" in url_lower or "/team" in url_lower or "/company" in url_lower:
            return ContentType.ABOUT
        if "/contact" in url_lower:
            return ContentType.CONTACT
        if url_lower.endswith("/") or url_lower.count("/") <= 3:
            return ContentType.LANDING
        
        # Title-based categorization
        if any(word in title_lower for word in ["blog", "post", "article", "news"]):
            return ContentType.BLOG
        if any(word in title_lower for word in ["pricing", "price", "plans", "subscribe"]):
            return ContentType.PRICING
        
        return ContentType.OTHER
    
    def calculate_readability(self, text: str) -> float:
        """Calculate Flesch-Kincaid readability score."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        words = text.split()
        
        if not sentences or not words:
            return 0.0
        
        total_words = len(words)
        total_sentences = len(sentences)
        
        # Count syllables (simple approximation)
        def count_syllables(word: str) -> int:
            vowels = 'aeiouy'
            word = word.lower()
            count = 0
            prev_vowel = False
            for char in word:
                is_vowel = char in vowels
                if is_vowel and not prev_vowel:
                    count += 1
                prev_vowel = is_vowel
            if word.endswith('e') and count > 1:
                count -= 1
            return max(1, count)
        
        total_syllables = sum(count_syllables(w) for w in words)
        
        # Flesch-Kincaid Reading Ease
        score = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
        
        return max(0, min(100, score))
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract top keywords from text."""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'it',
            'its', 'you', 'your', 'we', 'our', 'they', 'their', 'he', 'she', 'his', 'her'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Count frequencies
        freq = {}
        for word in words:
            if word not in stop_words:
                freq[word] = freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, _ in sorted_words[:top_n]]
    
    async def process_page(
        self,
        competitor_id: UUID,
        url: str,
        html: str,
        title: str,
        db
    ) -> dict:
        """Process a page and detect content changes."""
        from sqlalchemy import select
        
        # Extract and analyze content
        text_content = self.extract_main_content(html)
        
        if len(text_content) < self.min_content_length:
            return {"status": "skipped", "reason": "content too short"}
        
        content_hash = self.calculate_hash(text_content)
        content_type = self.categorize_content(url, title, text_content)
        readability = self.calculate_readability(text_content)
        keywords = self.extract_keywords(text_content)
        word_count = len(text_content.split())
        
        # Check if content already exists
        result = await db.execute(
            select(Content).where(
                Content.competitor_id == competitor_id,
                Content.url == url
            )
        )
        existing = result.scalar_one_or_none()
        
        import json
        
        if existing:
            # Check for changes
            if existing.content_hash != content_hash:
                # Content has changed
                previous_hash = existing.content_hash
                
                # Create change record
                change = ContentChange(
                    content_id=existing.id,
                    change_type="modified",
                    field_changed="content",
                    old_value=existing.text_content[:1000] if existing.text_content else None,
                    new_value=text_content[:1000]
                )
                db.add(change)
                
                # Update content record
                existing.content_hash = content_hash
                existing.previous_hash = previous_hash
                existing.has_changed = True
                existing.text_content = text_content[:50000]
                existing.word_count = word_count
                existing.readability_score = readability
                existing.keywords = json.dumps(keywords)
                existing.last_checked = datetime.utcnow()
                
                # Create alert
                alert = Alert(
                    competitor_id=competitor_id,
                    alert_type=AlertType.CONTENT_UPDATE,
                    severity=AlertSeverity.MEDIUM,
                    title=f"Content Updated: {title[:50]}",
                    message=f"The page at {url} has been modified",
                    related_url=url,
                    related_entity_id=str(existing.id),
                    related_entity_type="content"
                )
                db.add(alert)
                
                await db.commit()
                
                return {
                    "status": "updated",
                    "content_id": str(existing.id),
                    "change_id": str(change.id)
                }
            else:
                # No changes, just update last_checked
                existing.has_changed = False
                existing.last_checked = datetime.utcnow()
                await db.commit()
                
                return {"status": "unchanged", "content_id": str(existing.id)}
        else:
            # New content
            content = Content(
                competitor_id=competitor_id,
                url=url,
                title=title,
                content_type=content_type,
                word_count=word_count,
                readability_score=readability,
                text_content=text_content[:50000],
                content_hash=content_hash,
                has_changed=False,
                keywords=json.dumps(keywords),
                first_seen=datetime.utcnow(),
                last_checked=datetime.utcnow()
            )
            db.add(content)
            
            # Create alert for new page
            alert = Alert(
                competitor_id=competitor_id,
                alert_type=AlertType.NEW_PAGE,
                severity=AlertSeverity.LOW,
                title=f"New Page Discovered: {title[:50]}",
                message=f"A new page has been found at {url}",
                related_url=url
            )
            db.add(alert)
            
            await db.commit()
            await db.refresh(content)
            
            return {"status": "new", "content_id": str(content.id)}
    
    async def get_content_gaps(
        self,
        competitor_ids: List[UUID],
        db
    ) -> List[dict]:
        """Analyze content gaps between competitors."""
        from sqlalchemy import select
        
        # Get all content topics/keywords per competitor
        topic_coverage = {}
        
        for comp_id in competitor_ids:
            result = await db.execute(
                select(Content.keywords, Content.content_type)
                .where(Content.competitor_id == comp_id)
            )
            
            topics = set()
            for keywords_json, content_type in result.all():
                if keywords_json:
                    import json
                    try:
                        keywords = json.loads(keywords_json)
                        topics.update(keywords[:5])
                    except:
                        pass
            
            topic_coverage[str(comp_id)] = topics
        
        # Find topics that some competitors have but others don't
        all_topics = set()
        for topics in topic_coverage.values():
            all_topics.update(topics)
        
        gaps = []
        for topic in all_topics:
            coverage = {
                comp_id: topic in topics 
                for comp_id, topics in topic_coverage.items()
            }
            
            # It's a gap if not all competitors cover it
            if not all(coverage.values()):
                gaps.append({
                    "topic": topic,
                    "coverage": coverage
                })
        
        return gaps
