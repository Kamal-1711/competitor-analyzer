"""
Crawl queue management for Web-Spy.
Handles URL prioritization, deduplication, and state management.
"""

import asyncio
from typing import Optional, List, Dict, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID
import heapq

from loguru import logger


class CrawlPriority(Enum):
    """URL crawl priority levels."""
    CRITICAL = 0    # Homepage, main pages
    HIGH = 1        # Pricing, products
    MEDIUM = 2      # Blog posts, content pages
    LOW = 3         # Documentation, about pages
    DEFERRED = 4    # Low-value pages


@dataclass(order=True)
class CrawlItem:
    """Represents a URL to be crawled with priority."""
    priority: int
    url: str = field(compare=False)
    depth: int = field(compare=False, default=0)
    referrer: Optional[str] = field(compare=False, default=None)
    added_at: datetime = field(compare=False, default_factory=datetime.utcnow)
    retries: int = field(compare=False, default=0)
    metadata: Dict = field(compare=False, default_factory=dict)


class CrawlQueue:
    """
    Priority-based crawl queue with smart URL management.
    Features:
    - Priority-based ordering
    - URL deduplication
    - Depth limiting
    - Retry management
    - Domain-based rate limiting
    """
    
    def __init__(
        self,
        max_depth: int = 5,
        max_retries: int = 3,
        max_urls: int = 1000
    ):
        self._queue: List[CrawlItem] = []
        self._seen: Set[str] = set()
        self._in_progress: Set[str] = set()
        self._completed: Set[str] = set()
        self._failed: Dict[str, str] = {}  # url -> error message
        
        self.max_depth = max_depth
        self.max_retries = max_retries
        self.max_urls = max_urls
        
        self._lock = asyncio.Lock()
        
    @property
    def pending_count(self) -> int:
        return len(self._queue)
    
    @property
    def completed_count(self) -> int:
        return len(self._completed)
    
    @property
    def failed_count(self) -> int:
        return len(self._failed)
    
    @property
    def in_progress_count(self) -> int:
        return len(self._in_progress)
    
    @property
    def total_seen(self) -> int:
        return len(self._seen)
    
    async def add(
        self,
        url: str,
        priority: CrawlPriority = CrawlPriority.MEDIUM,
        depth: int = 0,
        referrer: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Add a URL to the queue."""
        async with self._lock:
            # Check limits
            if len(self._seen) >= self.max_urls:
                return False
            
            # Check depth
            if depth > self.max_depth:
                return False
            
            # Check if already seen
            if url in self._seen:
                return False
            
            self._seen.add(url)
            
            item = CrawlItem(
                priority=priority.value,
                url=url,
                depth=depth,
                referrer=referrer,
                metadata=metadata or {}
            )
            
            heapq.heappush(self._queue, item)
            return True
    
    async def add_many(
        self,
        urls: List[str],
        priority: CrawlPriority = CrawlPriority.MEDIUM,
        depth: int = 0,
        referrer: Optional[str] = None
    ) -> int:
        """Add multiple URLs to the queue."""
        added = 0
        for url in urls:
            if await self.add(url, priority, depth, referrer):
                added += 1
        return added
    
    async def get(self) -> Optional[CrawlItem]:
        """Get the next URL to crawl."""
        async with self._lock:
            while self._queue:
                item = heapq.heappop(self._queue)
                
                # Skip if completed or in progress
                if item.url in self._completed or item.url in self._in_progress:
                    continue
                
                self._in_progress.add(item.url)
                return item
            
            return None
    
    async def get_batch(self, size: int = 10) -> List[CrawlItem]:
        """Get a batch of URLs to crawl."""
        items = []
        for _ in range(size):
            item = await self.get()
            if item:
                items.append(item)
            else:
                break
        return items
    
    async def complete(self, url: str):
        """Mark a URL as completed."""
        async with self._lock:
            self._in_progress.discard(url)
            self._completed.add(url)
    
    async def fail(self, url: str, error: str, item: Optional[CrawlItem] = None):
        """Mark a URL as failed."""
        async with self._lock:
            self._in_progress.discard(url)
            
            # Check for retries
            if item and item.retries < self.max_retries:
                # Re-queue with lower priority
                new_item = CrawlItem(
                    priority=min(item.priority + 1, CrawlPriority.DEFERRED.value),
                    url=url,
                    depth=item.depth,
                    referrer=item.referrer,
                    retries=item.retries + 1,
                    metadata=item.metadata
                )
                heapq.heappush(self._queue, new_item)
            else:
                self._failed[url] = error
    
    async def release(self, url: str):
        """Release a URL from in-progress (for cleanup)."""
        async with self._lock:
            self._in_progress.discard(url)
    
    def is_empty(self) -> bool:
        """Check if queue is empty and no URLs in progress."""
        return len(self._queue) == 0 and len(self._in_progress) == 0
    
    def get_stats(self) -> Dict:
        """Get queue statistics."""
        return {
            "pending": self.pending_count,
            "in_progress": self.in_progress_count,
            "completed": self.completed_count,
            "failed": self.failed_count,
            "total_seen": self.total_seen,
            "max_urls": self.max_urls
        }
    
    async def clear(self):
        """Clear all queue state."""
        async with self._lock:
            self._queue.clear()
            self._seen.clear()
            self._in_progress.clear()
            self._completed.clear()
            self._failed.clear()


class URLPrioritizer:
    """
    Intelligent URL prioritization based on patterns and context.
    """
    
    # URL patterns and their priorities
    PRIORITY_PATTERNS = {
        CrawlPriority.CRITICAL: [
            r'^/$',  # Homepage
            r'^/home/?$',
            r'^/index\.html?$',
        ],
        CrawlPriority.HIGH: [
            r'/pricing',
            r'/plans',
            r'/products?/',
            r'/features',
            r'/shop',
            r'/store',
            r'/buy',
        ],
        CrawlPriority.MEDIUM: [
            r'/blog/',
            r'/posts?/',
            r'/articles?/',
            r'/news/',
            r'/case-study',
            r'/solutions',
        ],
        CrawlPriority.LOW: [
            r'/about',
            r'/team',
            r'/careers',
            r'/contact',
            r'/privacy',
            r'/terms',
            r'/legal',
            r'/docs/',
            r'/help/',
            r'/support/',
            r'/faq',
        ],
        CrawlPriority.DEFERRED: [
            r'/tag/',
            r'/category/',
            r'/author/',
            r'/page/\d+',
            r'\?.*page=',
            r'/archive/',
        ]
    }
    
    @classmethod
    def get_priority(cls, url: str, link_type: Optional[str] = None) -> CrawlPriority:
        """Determine priority for a URL based on patterns."""
        import re
        from urllib.parse import urlparse
        
        path = urlparse(url).path.lower()
        
        for priority, patterns in cls.PRIORITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, path):
                    return priority
        
        # Use link type if available
        if link_type:
            type_priorities = {
                'pricing': CrawlPriority.HIGH,
                'product': CrawlPriority.HIGH,
                'content': CrawlPriority.MEDIUM,
                'documentation': CrawlPriority.LOW,
                'navigation': CrawlPriority.LOW,
                'auth': CrawlPriority.DEFERRED,
            }
            return type_priorities.get(link_type, CrawlPriority.MEDIUM)
        
        return CrawlPriority.MEDIUM


class CrawlStateManager:
    """
    Manages crawl state for resumable crawling.
    Supports saving and loading crawl state.
    """
    
    def __init__(self):
        self._states: Dict[UUID, Dict] = {}
    
    def save_state(self, scan_id: UUID, queue: CrawlQueue) -> Dict:
        """Save current crawl state."""
        state = {
            "scan_id": str(scan_id),
            "timestamp": datetime.utcnow().isoformat(),
            "queue": [
                {
                    "url": item.url,
                    "priority": item.priority,
                    "depth": item.depth,
                    "retries": item.retries
                }
                for item in queue._queue
            ],
            "completed": list(queue._completed),
            "failed": queue._failed.copy(),
            "stats": queue.get_stats()
        }
        
        self._states[scan_id] = state
        return state
    
    async def restore_state(self, scan_id: UUID, queue: CrawlQueue) -> bool:
        """Restore crawl state from saved data."""
        if scan_id not in self._states:
            return False
        
        state = self._states[scan_id]
        
        await queue.clear()
        
        # Restore completed URLs
        for url in state.get("completed", []):
            queue._seen.add(url)
            queue._completed.add(url)
        
        # Restore failed URLs
        queue._failed = state.get("failed", {}).copy()
        for url in queue._failed:
            queue._seen.add(url)
        
        # Restore queue
        for item_data in state.get("queue", []):
            item = CrawlItem(
                priority=item_data["priority"],
                url=item_data["url"],
                depth=item_data["depth"],
                retries=item_data["retries"]
            )
            queue._seen.add(item.url)
            heapq.heappush(queue._queue, item)
        
        return True
    
    def clear_state(self, scan_id: UUID):
        """Clear saved state for a scan."""
        self._states.pop(scan_id, None)
