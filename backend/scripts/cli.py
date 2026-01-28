#!/usr/bin/env python
"""
Web-Spy CLI utility for common operations.
Usage: python scripts/cli.py <command>
"""

import asyncio
import sys
import argparse
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, '.')


async def init_database():
    """Initialize the database with tables."""
    from app.database import init_db
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully!")


async def add_competitor(name: str, url: str, competitor_type: str = "direct"):
    """Add a new competitor to monitor."""
    from app.database import async_session_maker
    from app.models.competitor import Competitor, CompetitorType
    import tldextract
    
    extracted = tldextract.extract(url)
    domain = f"{extracted.domain}.{extracted.suffix}"
    
    async with async_session_maker() as db:
        comp = Competitor(
            name=name,
            url=url,
            domain=domain,
            competitor_type=CompetitorType(competitor_type),
            favicon_url=f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
        )
        db.add(comp)
        await db.commit()
        await db.refresh(comp)
        print(f"Added competitor: {comp.name} (ID: {comp.id})")
        return comp


async def list_competitors():
    """List all competitors."""
    from app.database import async_session_maker
    from app.models.competitor import Competitor
    from sqlalchemy import select
    
    async with async_session_maker() as db:
        result = await db.execute(
            select(Competitor).where(Competitor.is_active == True)
        )
        competitors = result.scalars().all()
        
        if not competitors:
            print("No competitors found.")
            return
        
        print(f"\n{'ID':<40} {'Name':<25} {'Domain':<25} {'Health':<8}")
        print("-" * 100)
        for c in competitors:
            print(f"{str(c.id):<40} {c.name:<25} {c.domain:<25} {c.health_score:<8}")
        print(f"\nTotal: {len(competitors)} competitors")


async def trigger_scan(competitor_id: str):
    """Trigger a scan for a competitor."""
    from app.database import async_session_maker
    from app.models.competitor import Competitor
    from app.models.scan import Scan, ScanStatus
    from app.tasks.crawl_tasks import crawl_competitor
    from sqlalchemy import select
    
    async with async_session_maker() as db:
        result = await db.execute(
            select(Competitor).where(Competitor.id == UUID(competitor_id))
        )
        competitor = result.scalar_one_or_none()
        
        if not competitor:
            print(f"Competitor not found: {competitor_id}")
            return
        
        scan = Scan(competitor_id=competitor.id, status=ScanStatus.PENDING)
        db.add(scan)
        await db.commit()
        await db.refresh(scan)
        
        # Trigger Celery task
        crawl_competitor.delay(competitor_id, str(scan.id))
        print(f"Scan triggered for {competitor.name} (Scan ID: {scan.id})")


async def run_quick_scan(url: str):
    """Run a quick scan on a URL."""
    from app.services.crawler import PlaywrightCrawler
    
    print(f"Quick scanning: {url}")
    crawler = PlaywrightCrawler()
    result = await crawler.quick_scan(url)
    
    print(f"\nResults:")
    print(f"  Title: {result.get('title', 'N/A')}")
    print(f"  Load time: {result.get('load_time', 0):.2f}s")
    print(f"  Content length: {len(result.get('text', ''))} chars")
    if result.get('screenshot'):
        print(f"  Screenshot: {result['screenshot']}")


async def analyze_seo(url: str, competitor_id: str = None):
    """Analyze SEO for a URL."""
    from app.services.seo_analyzer import SeoAnalyzer
    
    print(f"Analyzing SEO for: {url}")
    analyzer = SeoAnalyzer()
    
    try:
        result = await analyzer.analyze(url, UUID(competitor_id) if competitor_id else None)
        print(f"\nSEO Analysis Results:")
        print(f"  Overall Score: {result.get('overall_score', 0)}/100")
        print(f"  Title Score: {result.get('title_score', 0)}/100")
        print(f"  Meta Description Score: {result.get('meta_description_score', 0)}/100")
        print(f"  Headers Score: {result.get('headers_score', 0)}/100")
        print(f"  Content Score: {result.get('content_score', 0)}/100")
        print(f"  Technical Score: {result.get('technical_score', 0)}/100")
    except Exception as e:
        print(f"Error: {e}")


async def show_stats():
    """Show overall statistics."""
    from app.database import async_session_maker
    from app.models.competitor import Competitor
    from app.models.scan import Scan
    from app.models.content import Content
    from app.models.alert import Alert
    from sqlalchemy import select, func
    
    async with async_session_maker() as db:
        # Count competitors
        comp_result = await db.execute(
            select(func.count(Competitor.id)).where(Competitor.is_active == True)
        )
        comp_count = comp_result.scalar()
        
        # Count scans
        scan_result = await db.execute(select(func.count(Scan.id)))
        scan_count = scan_result.scalar()
        
        # Count content
        content_result = await db.execute(select(func.count(Content.id)))
        content_count = content_result.scalar()
        
        # Count unread alerts
        alert_result = await db.execute(
            select(func.count(Alert.id)).where(Alert.is_read == False)
        )
        alert_count = alert_result.scalar()
        
        print("\n=== Web-Spy Statistics ===")
        print(f"  Competitors: {comp_count}")
        print(f"  Total Scans: {scan_count}")
        print(f"  Tracked Content: {content_count}")
        print(f"  Unread Alerts: {alert_count}")


def main():
    parser = argparse.ArgumentParser(description='Web-Spy CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # init command
    subparsers.add_parser('init', help='Initialize database')
    
    # add command
    add_parser = subparsers.add_parser('add', help='Add a competitor')
    add_parser.add_argument('name', help='Competitor name')
    add_parser.add_argument('url', help='Competitor URL')
    add_parser.add_argument('--type', default='direct', choices=['direct', 'indirect'])
    
    # list command
    subparsers.add_parser('list', help='List competitors')
    
    # scan command
    scan_parser = subparsers.add_parser('scan', help='Scan a competitor')
    scan_parser.add_argument('competitor_id', help='Competitor ID')
    
    # quick command
    quick_parser = subparsers.add_parser('quick', help='Quick scan a URL')
    quick_parser.add_argument('url', help='URL to scan')
    
    # seo command
    seo_parser = subparsers.add_parser('seo', help='Analyze SEO')
    seo_parser.add_argument('url', help='URL to analyze')
    seo_parser.add_argument('--competitor-id', help='Optional competitor ID')
    
    # stats command
    subparsers.add_parser('stats', help='Show statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'init':
        asyncio.run(init_database())
    elif args.command == 'add':
        asyncio.run(add_competitor(args.name, args.url, args.type))
    elif args.command == 'list':
        asyncio.run(list_competitors())
    elif args.command == 'scan':
        asyncio.run(trigger_scan(args.competitor_id))
    elif args.command == 'quick':
        asyncio.run(run_quick_scan(args.url))
    elif args.command == 'seo':
        asyncio.run(analyze_seo(args.url, args.competitor_id))
    elif args.command == 'stats':
        asyncio.run(show_stats())


if __name__ == '__main__':
    main()
