"""Web-Spy Services Module"""

from app.services.crawler import PlaywrightCrawler
from app.services.seo_analyzer import SeoAnalyzer
from app.services.content_tracker import ContentTracker
from app.services.price_monitor import PriceMonitor
from app.services.product_watcher import ProductWatcher
from app.services.gap_finder import GapFinder
from app.services.screenshot_manager import ScreenshotManager, VisualDiffGenerator
from app.services.crawl_utils import (
    RobotsParser,
    URLNormalizer,
    LinkExtractor,
    SitemapParser,
    ContentFingerprinter
)
from app.services.crawl_queue import CrawlQueue, CrawlPriority, URLPrioritizer
from app.services.seo_utils import (
    SchemaAnalyzer,
    OpenGraphAnalyzer,
    KeywordAnalyzer,
    PageSpeedEstimator
)
from app.services.seo_comparator import (
    SeoComparator,
    SeoTrendAnalyzer,
    SeoAuditReporter
)

__all__ = [
    # Core services
    "PlaywrightCrawler",
    "SeoAnalyzer",
    "ContentTracker",
    "PriceMonitor",
    "ProductWatcher",
    "GapFinder",
    
    # Screenshot
    "ScreenshotManager",
    "VisualDiffGenerator",
    
    # Crawl utilities
    "RobotsParser",
    "URLNormalizer",
    "LinkExtractor",
    "SitemapParser",
    "ContentFingerprinter",
    "CrawlQueue",
    "CrawlPriority",
    "URLPrioritizer",
    
    # SEO utilities
    "SchemaAnalyzer",
    "OpenGraphAnalyzer",
    "KeywordAnalyzer",
    "PageSpeedEstimator",
    "SeoComparator",
    "SeoTrendAnalyzer",
    "SeoAuditReporter",
]
