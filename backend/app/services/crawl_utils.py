"""
Advanced crawling utilities for Web-Spy.
Includes: URL normalization, link extraction, robots.txt parsing, sitemap handling.
"""

import re
import hashlib
from typing import Optional, List, Set, Dict, Tuple
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

import httpx
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class RobotsRule:
    """Represents a robots.txt rule."""
    user_agent: str
    allowed: List[str] = field(default_factory=list)
    disallowed: List[str] = field(default_factory=list)
    crawl_delay: Optional[float] = None
    sitemaps: List[str] = field(default_factory=list)


class RobotsParser:
    """
    Advanced robots.txt parser with caching.
    Supports wildcard patterns, crawl-delay, and sitemap discovery.
    """
    
    def __init__(self):
        self._cache: Dict[str, RobotsRule] = {}
        self._cache_ttl = 3600  # 1 hour
        self._cache_timestamps: Dict[str, datetime] = {}
    
    async def fetch_and_parse(self, base_url: str) -> RobotsRule:
        """Fetch and parse robots.txt for a domain."""
        # Check cache
        if base_url in self._cache:
            cached_at = self._cache_timestamps.get(base_url, datetime.min)
            if (datetime.utcnow() - cached_at).seconds < self._cache_ttl:
                return self._cache[base_url]
        
        robots_url = f"{base_url}/robots.txt"
        rule = RobotsRule(user_agent="*")
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(robots_url, follow_redirects=True)
                
                if response.status_code == 200:
                    rule = self._parse(response.text)
        except Exception as e:
            logger.debug(f"Could not fetch robots.txt from {base_url}: {e}")
        
        self._cache[base_url] = rule
        self._cache_timestamps[base_url] = datetime.utcnow()
        
        return rule
    
    def _parse(self, content: str) -> RobotsRule:
        """Parse robots.txt content."""
        rule = RobotsRule(user_agent="*")
        current_agents = []
        
        for line in content.split("\n"):
            line = line.strip()
            
            # Remove comments
            if "#" in line:
                line = line.split("#")[0].strip()
            
            if not line:
                continue
            
            if ":" not in line:
                continue
            
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == "user-agent":
                current_agents.append(value.lower())
            elif key == "disallow" and ("*" in current_agents or "googlebot" in current_agents):
                if value:
                    rule.disallowed.append(value)
            elif key == "allow" and ("*" in current_agents or "googlebot" in current_agents):
                if value:
                    rule.allowed.append(value)
            elif key == "crawl-delay" and ("*" in current_agents or "googlebot" in current_agents):
                try:
                    rule.crawl_delay = float(value)
                except ValueError:
                    pass
            elif key == "sitemap":
                rule.sitemaps.append(value)
        
        return rule
    
    def is_allowed(self, rule: RobotsRule, path: str) -> bool:
        """Check if a path is allowed by the robots rules."""
        # Check allow rules first (they take precedence)
        for pattern in rule.allowed:
            if self._matches(pattern, path):
                return True
        
        # Then check disallow rules
        for pattern in rule.disallowed:
            if self._matches(pattern, path):
                return False
        
        return True
    
    def _matches(self, pattern: str, path: str) -> bool:
        """Check if a path matches a robots.txt pattern."""
        # Handle wildcards
        if "*" in pattern:
            regex = re.escape(pattern).replace("\\*", ".*")
            if pattern.endswith("$"):
                regex = regex[:-2] + "$"
            return bool(re.match(regex, path))
        
        # Handle $ anchor
        if pattern.endswith("$"):
            return path == pattern[:-1]
        
        return path.startswith(pattern)


class URLNormalizer:
    """
    URL normalization and canonicalization.
    Handles trailing slashes, query params, fragments, etc.
    """
    
    # Parameters to strip (tracking, session, etc.)
    STRIP_PARAMS = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'msclkid', 'ref', 'source', 'mc_cid', 'mc_eid',
        'sessionid', 'sid', 'jsessionid', '_ga', '_gid'
    }
    
    @classmethod
    def normalize(cls, url: str, base_url: Optional[str] = None) -> str:
        """Normalize a URL for consistent comparison."""
        # Handle relative URLs
        if base_url and not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        parsed = urlparse(url)
        
        # Lowercase scheme and netloc
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        # Remove default ports
        if netloc.endswith(':80') and scheme == 'http':
            netloc = netloc[:-3]
        elif netloc.endswith(':443') and scheme == 'https':
            netloc = netloc[:-4]
        
        # Normalize path
        path = parsed.path
        if not path:
            path = '/'
        
        # Remove trailing slash (except for root)
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')
        
        # Remove fragments
        fragment = ''
        
        # Filter query parameters
        query_params = parse_qs(parsed.query)
        filtered_params = {
            k: v for k, v in query_params.items()
            if k.lower() not in cls.STRIP_PARAMS
        }
        
        # Sort query params for consistent ordering
        query = urlencode(sorted(filtered_params.items()), doseq=True) if filtered_params else ''
        
        return urlunparse((scheme, netloc, path, '', query, fragment))
    
    @classmethod
    def get_domain(cls, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc.lower()
    
    @classmethod
    def is_same_domain(cls, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain."""
        return cls.get_domain(url1) == cls.get_domain(url2)
    
    @classmethod
    def get_url_depth(cls, url: str) -> int:
        """Get the depth of a URL path."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if not path:
            return 0
        return len(path.split('/'))


class LinkExtractor:
    """
    Intelligent link extraction from HTML content.
    Identifies different types of links and their context.
    """
    
    # File extensions to skip
    SKIP_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.rar', '.tar', '.gz', '.7z',
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
        '.css', '.js', '.json', '.xml',
        '.exe', '.dmg', '.apk'
    }
    
    @classmethod
    def extract_links(
        cls,
        html: str,
        base_url: str,
        same_domain_only: bool = True
    ) -> List[Dict]:
        """Extract and categorize links from HTML."""
        soup = BeautifulSoup(html, "lxml")
        links = []
        seen = set()
        base_domain = URLNormalizer.get_domain(base_url)
        
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            
            # Skip empty, javascript, mailto, tel links
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue
            
            # Normalize URL
            normalized = URLNormalizer.normalize(href, base_url)
            
            # Skip if already seen or has skip extension
            if normalized in seen:
                continue
            
            lower_normalized = normalized.lower()
            if any(lower_normalized.endswith(ext) for ext in cls.SKIP_EXTENSIONS):
                continue
            
            # Check domain
            link_domain = URLNormalizer.get_domain(normalized)
            if same_domain_only and link_domain != base_domain:
                continue
            
            seen.add(normalized)
            
            # Categorize link
            link_type = cls._categorize_link(normalized, a)
            
            links.append({
                'url': normalized,
                'text': a.get_text(strip=True)[:200],
                'type': link_type,
                'is_internal': link_domain == base_domain,
                'depth': URLNormalizer.get_url_depth(normalized),
                'nofollow': 'nofollow' in a.get('rel', [])
            })
        
        return links
    
    @classmethod
    def _categorize_link(cls, url: str, element) -> str:
        """Categorize a link based on URL patterns and context."""
        url_lower = url.lower()
        text = element.get_text(strip=True).lower()
        
        # Navigation links
        if any(x in url_lower for x in ['/about', '/contact', '/team', '/careers']):
            return 'navigation'
        
        # Product/Shop links
        if any(x in url_lower for x in ['/product', '/shop', '/store', '/item', '/buy']):
            return 'product'
        
        # Blog/Content links
        if any(x in url_lower for x in ['/blog', '/post', '/article', '/news']):
            return 'content'
        
        # Pricing links
        if any(x in url_lower for x in ['/pricing', '/plans', '/subscribe']):
            return 'pricing'
        
        # Documentation links
        if any(x in url_lower for x in ['/docs', '/help', '/support', '/faq']):
            return 'documentation'
        
        # Auth links
        if any(x in url_lower for x in ['/login', '/signup', '/register', '/signin']):
            return 'auth'
        
        return 'general'


class SitemapParser:
    """
    Advanced sitemap parser with support for:
    - Sitemap index files
    - Gzipped sitemaps
    - Priority and lastmod handling
    """
    
    @classmethod
    async def parse(cls, sitemap_url: str, max_urls: int = 1000) -> List[Dict]:
        """Parse a sitemap and return URLs with metadata."""
        urls = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(sitemap_url, follow_redirects=True)
                
                if response.status_code != 200:
                    return urls
                
                content = response.text
                soup = BeautifulSoup(content, "lxml-xml")
                
                # Check if it's a sitemap index
                sitemaps = soup.find_all('sitemap')
                if sitemaps:
                    # Parse nested sitemaps
                    for sitemap in sitemaps[:10]:  # Limit nested sitemaps
                        loc = sitemap.find('loc')
                        if loc:
                            nested = await cls.parse(loc.text, max_urls - len(urls))
                            urls.extend(nested)
                            if len(urls) >= max_urls:
                                break
                else:
                    # Regular sitemap
                    for url_tag in soup.find_all('url'):
                        if len(urls) >= max_urls:
                            break
                        
                        loc = url_tag.find('loc')
                        if not loc:
                            continue
                        
                        url_data = {
                            'url': loc.text,
                            'lastmod': None,
                            'priority': 0.5,
                            'changefreq': None
                        }
                        
                        lastmod = url_tag.find('lastmod')
                        if lastmod:
                            url_data['lastmod'] = lastmod.text
                        
                        priority = url_tag.find('priority')
                        if priority:
                            try:
                                url_data['priority'] = float(priority.text)
                            except ValueError:
                                pass
                        
                        changefreq = url_tag.find('changefreq')
                        if changefreq:
                            url_data['changefreq'] = changefreq.text
                        
                        urls.append(url_data)
        
        except Exception as e:
            logger.warning(f"Failed to parse sitemap {sitemap_url}: {e}")
        
        return urls
    
    @classmethod
    async def discover_sitemaps(cls, base_url: str) -> List[str]:
        """Discover sitemaps from common locations and robots.txt."""
        sitemaps = set()
        
        # Common sitemap locations
        common_locations = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemap-index.xml',
            '/sitemaps.xml',
            '/sitemap1.xml',
            '/post-sitemap.xml',
            '/page-sitemap.xml',
            '/product-sitemap.xml'
        ]
        
        # Check common locations
        async with httpx.AsyncClient(timeout=10) as client:
            for location in common_locations:
                try:
                    url = f"{base_url}{location}"
                    response = await client.head(url, follow_redirects=True)
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'xml' in content_type or 'text' in content_type:
                            sitemaps.add(url)
                except Exception:
                    pass
        
        # Parse robots.txt for sitemaps
        robots_parser = RobotsParser()
        robots = await robots_parser.fetch_and_parse(base_url)
        sitemaps.update(robots.sitemaps)
        
        return list(sitemaps)


class ContentFingerprinter:
    """
    Generate fingerprints for content comparison and deduplication.
    Uses multiple techniques for robust comparison.
    """
    
    @classmethod
    def generate(cls, text: str) -> Dict:
        """Generate multiple fingerprints for content."""
        # Normalize text
        normalized = cls._normalize_text(text)
        
        # Full hash
        full_hash = hashlib.sha256(normalized.encode()).hexdigest()
        
        # Simhash for similarity detection
        simhash = cls._simhash(normalized)
        
        # Extract key phrases
        phrases = cls._extract_phrases(normalized)
        phrase_hash = hashlib.md5(' '.join(phrases).encode()).hexdigest()
        
        return {
            'full_hash': full_hash,
            'simhash': simhash,
            'phrase_hash': phrase_hash,
            'word_count': len(normalized.split()),
            'char_count': len(normalized)
        }
    
    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """Normalize text for fingerprinting."""
        # Lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        return text.strip()
    
    @classmethod
    def _simhash(cls, text: str, bits: int = 64) -> str:
        """Calculate simhash for similarity detection."""
        features = text.split()
        v = [0] * bits
        
        for feature in features:
            h = int(hashlib.md5(feature.encode()).hexdigest(), 16)
            for i in range(bits):
                if h & (1 << i):
                    v[i] += 1
                else:
                    v[i] -= 1
        
        fingerprint = 0
        for i in range(bits):
            if v[i] >= 0:
                fingerprint |= (1 << i)
        
        return format(fingerprint, f'0{bits // 4}x')
    
    @classmethod
    def _extract_phrases(cls, text: str, n: int = 10) -> List[str]:
        """Extract key phrases using n-grams."""
        words = text.split()
        if len(words) < 3:
            return words
        
        # Generate 3-grams
        ngrams = []
        for i in range(len(words) - 2):
            ngrams.append(' '.join(words[i:i+3]))
        
        # Return most common
        from collections import Counter
        return [phrase for phrase, _ in Counter(ngrams).most_common(n)]
    
    @classmethod
    def compare(cls, fp1: Dict, fp2: Dict) -> float:
        """Compare two fingerprints and return similarity (0-1)."""
        if fp1['full_hash'] == fp2['full_hash']:
            return 1.0
        
        # Compare simhash using Hamming distance
        h1 = int(fp1['simhash'], 16)
        h2 = int(fp2['simhash'], 16)
        distance = bin(h1 ^ h2).count('1')
        similarity = 1 - (distance / 64)
        
        return similarity
