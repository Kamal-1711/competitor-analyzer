import asyncio
import random
import hashlib
from typing import Optional, List, Callable, Set
from urllib.parse import urljoin, urlparse
from datetime import datetime
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor
import functools

from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
from bs4 import BeautifulSoup
from loguru import logger
import httpx

from app.config import settings


# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Thread pool for running Playwright
_executor = ThreadPoolExecutor(max_workers=3)


class PlaywrightCrawler:
    """
    High-performance web crawler using Playwright (sync API in thread pool).
    Features:
    - Runs in thread pool to avoid Windows asyncio issues
    - Concurrent browser contexts
    - Resource blocking for speed
    - Stealth mode
    - Rate limiting with exponential backoff
    - Robots.txt compliance
    """
    
    def __init__(self):
        self.max_contexts = settings.crawler_concurrent_contexts
        self.page_timeout = settings.crawler_page_timeout
        self.max_retries = settings.crawler_max_retries
        self.retry_delay = settings.crawler_retry_delay
        self.visited_urls: Set[str] = set()
        self.robots_cache: dict = {}

    def _quick_scan_sync(self, url: str) -> dict:
        """Synchronous quick scan that runs in thread pool."""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ]
            )
            
            try:
                user_agent = random.choice(USER_AGENTS)
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                )
                
                page = context.new_page()
                
                start_time = datetime.utcnow()
                response = page.goto(url, timeout=self.page_timeout)
                load_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                page.wait_for_timeout(1000)
                
                html = page.content()
                soup = BeautifulSoup(html, "lxml")
                
                # Take screenshot
                screenshot = page.screenshot(type="png")
                
                title = soup.title.string if soup.title else ""
                
                # Get text
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text(separator=" ", strip=True)
                
                content_hash = hashlib.sha256(text.encode()).hexdigest()
                
                context.close()
                
                return {
                    "url": url,
                    "title": title,
                    "html": html,  # Add HTML for price extraction
                    "word_count": len(text.split()),
                    "load_time_ms": int(load_time),
                    "status_code": response.status if response else None,
                    "content_hash": content_hash,
                    "screenshot": screenshot
                }
                
            finally:
                browser.close()

    async def quick_scan(self, url: str) -> dict:
        """Quick single-page scan without full crawl - runs in thread pool."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            functools.partial(self._quick_scan_sync, url)
        )
        return result

    def _crawl_page_sync(self, url: str) -> dict:
        """Synchronous page crawl that runs in thread pool."""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ]
            )
            
            try:
                user_agent = random.choice(USER_AGENTS)
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1920, "height": 1080},
                )
                
                page = context.new_page()
                
                for attempt in range(self.max_retries):
                    try:
                        start_time = datetime.utcnow()
                        response = page.goto(
                            url,
                            timeout=self.page_timeout,
                            wait_until="domcontentloaded"
                        )
                        load_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                        
                        page.wait_for_timeout(1000)
                        
                        html = page.content()
                        soup = BeautifulSoup(html, "lxml")
                        
                        # Extract data
                        title = soup.title.string if soup.title else ""
                        
                        # Get text content
                        for script in soup(["script", "style"]):
                            script.decompose()
                        text = soup.get_text(separator=" ", strip=True)
                        word_count = len(text.split())
                        
                        # Calculate content hash
                        content_hash = hashlib.sha256(text.encode()).hexdigest()
                        
                        # Extract links
                        links = []
                        for a in soup.find_all("a", href=True):
                            href = a["href"]
                            if href.startswith("/"):
                                href = urljoin(url, href)
                            if href.startswith("http"):
                                links.append(href)
                        
                        context.close()
                        
                        return {
                            "url": url,
                            "title": title,
                            "word_count": word_count,
                            "load_time_ms": int(load_time),
                            "status_code": response.status if response else None,
                            "content_hash": content_hash,
                            "content_type": "text/html",
                            "html_content": html[:100000],
                            "links": links[:100]
                        }
                        
                    except Exception as e:
                        logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                        if attempt < self.max_retries - 1:
                            import time
                            time.sleep(self.retry_delay * (2 ** attempt))
                        else:
                            return {"url": url, "error": str(e)}
                            
            finally:
                browser.close()
        
        return {"url": url, "error": "Unknown error"}

    async def crawl(
        self,
        url: str,
        scan_id: UUID,
        db,
        progress_callback: Optional[Callable] = None,
        max_pages: int = 100
    ):
        """
        Crawl a website starting from the given URL.
        """
        from app.models.scan import ScanPage
        
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Get URLs from sitemap
        sitemap_urls = await self._get_sitemap_urls(base_url)
        
        # Initialize queue with sitemap URLs and starting URL
        queue = [url] + sitemap_urls
        self.visited_urls = set()
        
        pages_crawled = 0
        total_pages = min(len(queue), max_pages)
        
        loop = asyncio.get_event_loop()
        
        while queue and pages_crawled < max_pages:
            next_url = queue.pop(0)
            if next_url in self.visited_urls:
                continue
                
            # Check robots.txt
            path = urlparse(next_url).path or "/"
            if not await self._check_robots_txt(base_url, path):
                continue
                
            self.visited_urls.add(next_url)
            
            # Crawl page in thread pool
            result = await loop.run_in_executor(
                _executor,
                functools.partial(self._crawl_page_sync, next_url)
            )
            
            if "error" not in result:
                # Save to database
                scan_page = ScanPage(
                    scan_id=scan_id,
                    url=result["url"],
                    status_code=result.get("status_code"),
                    title=result.get("title", "")[:500] if result.get("title") else None,
                    content_type=result.get("content_type", "text/html"),
                    content_hash=result.get("content_hash"),
                    word_count=result.get("word_count", 0),
                    load_time_ms=result.get("load_time_ms"),
                    html_content=result.get("html_content"),
                )
                db.add(scan_page)
                await db.commit()
                
                # Add new links to queue
                for link in result.get("links", []):
                    if link.startswith(base_url) and link not in self.visited_urls:
                        queue.append(link)
            
            pages_crawled += 1
            
            # Update progress
            if progress_callback:
                progress = int((pages_crawled / total_pages) * 100)
                await progress_callback(progress, next_url)
            
            # Rate limiting
            await asyncio.sleep(
                random.uniform(
                    settings.request_delay_min,
                    settings.request_delay_max
                )
            )
        
        return {"pages_crawled": pages_crawled}
    
    async def _check_robots_txt(self, base_url: str, path: str) -> bool:
        """Check if a path is allowed by robots.txt."""
        if not settings.crawler_respect_robots_txt:
            return True
            
        if base_url not in self.robots_cache:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{base_url}/robots.txt",
                        timeout=10,
                        follow_redirects=True
                    )
                    if response.status_code == 200:
                        self.robots_cache[base_url] = response.text
                    else:
                        self.robots_cache[base_url] = ""
            except Exception:
                self.robots_cache[base_url] = ""
                
        robots_txt = self.robots_cache[base_url]
        
        # Simple robots.txt parsing
        if not robots_txt:
            return True
            
        disallowed = []
        current_agent = None
        
        for line in robots_txt.split("\n"):
            line = line.strip().lower()
            if line.startswith("user-agent:"):
                current_agent = line.split(":", 1)[1].strip()
            elif line.startswith("disallow:") and current_agent in ["*", "googlebot"]:
                disallow_path = line.split(":", 1)[1].strip()
                if disallow_path:
                    disallowed.append(disallow_path)
                    
        for disallow_path in disallowed:
            if path.startswith(disallow_path):
                return False
                
        return True
        
    async def _get_sitemap_urls(self, base_url: str) -> List[str]:
        """Parse sitemap.xml for URL discovery."""
        urls = []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/sitemap.xml",
                    timeout=10,
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml-xml")
                    
                    # Check for sitemap index
                    sitemaps = soup.find_all("sitemap")
                    if sitemaps:
                        for sitemap in sitemaps[:5]:  # Limit nested sitemaps
                            loc = sitemap.find("loc")
                            if loc:
                                nested_urls = await self._parse_sitemap(loc.text)
                                urls.extend(nested_urls)
                    else:
                        # Regular sitemap
                        for url_tag in soup.find_all("url"):
                            loc = url_tag.find("loc")
                            if loc:
                                urls.append(loc.text)
        except Exception as e:
            logger.warning(f"Failed to parse sitemap: {e}")
            
        return urls[:500]  # Limit URLs
        
    async def _parse_sitemap(self, sitemap_url: str) -> List[str]:
        """Parse a single sitemap file."""
        urls = []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(sitemap_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml-xml")
                    for url_tag in soup.find_all("url"):
                        loc = url_tag.find("loc")
                        if loc:
                            urls.append(loc.text)
        except Exception:
            pass
            
        return urls[:100]
