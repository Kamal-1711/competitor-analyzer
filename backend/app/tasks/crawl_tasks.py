from uuid import UUID
from datetime import datetime
from loguru import logger


async def crawl_competitor(competitor_id: str, scan_id: str):
    """Main task to crawl a competitor's website with full analysis."""
    logger.info(f"Starting crawl for competitor {competitor_id}, scan {scan_id}")
    
    try:
        result = await _run_full_crawl(UUID(competitor_id), UUID(scan_id))
        return result
    except Exception as e:
        logger.error(f"Crawl failed for competitor {competitor_id}: {e}")
        # In-memory background tasks don't have built-in retry like Celery,
        # but the scan status will be marked as FAILED in _run_full_crawl.
        return None


async def _run_full_crawl(competitor_id: UUID, scan_id: UUID):
    """Full async crawl with content, price, product analysis."""
    from app.services.crawler import PlaywrightCrawler
    from app.services.seo_analyzer import SeoAnalyzer
    from app.services.content_tracker import ContentTracker
    from app.services.price_monitor import PriceMonitor
    from app.services.product_watcher import ProductWatcher
    from app.database import get_engine
    from app.models.scan import Scan
    from app.models.competitor import Competitor
    from sqlalchemy import select
    
    _, session_maker = get_engine()
    async with session_maker() as db:
        # Get competitor
        result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
        competitor = result.scalar_one_or_none()
        
        if not competitor:
            raise ValueError(f"Competitor not found: {competitor_id}")
        
        # Update scan status
        scan_result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = scan_result.scalar_one()
        scan.status = "running"
        scan.started_at = datetime.utcnow()
        await db.commit()
        
        try:
            # Initialize services
            crawler = PlaywrightCrawler()
            seo_analyzer = SeoAnalyzer()
            content_tracker = ContentTracker()
            price_monitor = PriceMonitor()
            product_watcher = ProductWatcher()
            
            # Crawl website
            crawl_result = await crawler.crawl(
                url=competitor.url,
                scan_id=scan_id,
                db=db,
                progress_callback=lambda p, u: _update_progress(db, scan_id, p, u)
            )
            
            # Get crawled pages for analysis
            from app.models.scan import ScanPage
            pages_result = await db.execute(
                select(ScanPage).where(ScanPage.scan_id == scan_id)
            )
            pages = pages_result.scalars().all()
            
            # Analyze each page
            seo_score_sum = 0
            content_score_sum = 0
            analyzed_count = 0
            
            for page in pages[:50]:  # Limit analysis
                if page.html_content:
                    # SEO Analysis (only for main pages)
                    if page.url == competitor.url or analyzed_count < 5:
                        try:
                            await seo_analyzer.analyze(page.url, competitor_id)
                            seo_score_sum += 70  # Placeholder
                            analyzed_count += 1
                        except Exception as e:
                            logger.warning(f"SEO analysis failed for {page.url}: {e}")
                    
                    # Content tracking
                    try:
                        await content_tracker.process_page(
                            competitor_id, page.url, page.html_content, page.title or "", db
                        )
                    except Exception as e:
                        logger.warning(f"Content tracking failed for {page.url}: {e}")
                    
                    # Price monitoring
                    try:
                        await price_monitor.process_prices(competitor_id, page.url, page.html_content, db)
                    except Exception as e:
                        logger.warning(f"Price monitoring failed for {page.url}: {e}")
                    
                    # Product watching
                    try:
                        await product_watcher.process_products(competitor_id, page.url, page.html_content, db)
                    except Exception as e:
                        logger.warning(f"Product watching failed for {page.url}: {e}")
            
            # Update competitor scores
            if analyzed_count > 0:
                competitor.seo_score = min(100, seo_score_sum // analyzed_count)
            competitor.health_score = _calculate_health_score(competitor)
            competitor.last_scanned = datetime.utcnow()
            
            # Mark scan complete
            scan.status = "completed"
            scan.completed_at = datetime.utcnow()
            scan.progress = 100
            scan.pages_crawled = len(pages)
            
            await db.commit()
            
            return {"status": "completed", "scan_id": str(scan_id), "pages": len(pages)}
            
        except Exception as e:
            scan.status = "failed"
            scan.error_message = str(e)
            await db.commit()
            raise


def _calculate_health_score(competitor) -> int:
    """Calculate overall health score from component scores."""
    weights = {'seo': 0.4, 'content': 0.3, 'activity': 0.3}
    
    seo_contrib = (competitor.seo_score or 0) * weights['seo']
    content_contrib = (competitor.content_score or 0) * weights['content']
    activity_contrib = 70 * weights['activity']  # Default activity score
    
    return int(seo_contrib + content_contrib + activity_contrib)


async def _update_progress(db, scan_id: UUID, progress: int, current_url: str):
    """Update scan progress in database."""
    from sqlalchemy import select
    from app.models.scan import Scan
    
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one()
    scan.progress = progress
    scan.current_url = current_url
    await db.commit()


async def quick_scan(url: str):
    """Quick single-page analysis."""
    logger.info(f"Quick scanning {url}")
    
    try:
        from app.services.crawler import PlaywrightCrawler
        crawler = PlaywrightCrawler()
        result = await crawler.quick_scan(url)
        return result
    except Exception as e:
        logger.error(f"Quick scan failed for {url}: {e}")
        return None


async def analyze_seo(competitor_id: str, url: str):
    """Run SEO analysis on a URL."""
    logger.info(f"Analyzing SEO for {url}")
    
    try:
        from app.services.seo_analyzer import SeoAnalyzer
        analyzer = SeoAnalyzer()
        result = await analyzer.analyze(url, UUID(competitor_id))
        return result
    except Exception as e:
        logger.error(f"SEO analysis failed for {url}: {e}")
        return None


async def monitor_prices(competitor_id: str, url: str, html: str):
    """Extract and track prices from a page."""
    logger.info(f"Monitoring prices for {url}")
    
    try:
        from app.services.price_monitor import PriceMonitor
        from app.database import async_session_maker
        
        monitor = PriceMonitor()
        async with async_session_maker() as db:
            return await monitor.process_prices(UUID(competitor_id), url, html, db)
    except Exception as e:
        logger.error(f"Price monitoring failed for {url}: {e}")
        return None


async def track_content(competitor_id: str, url: str, html: str, title: str):
    """Track content changes on a page."""
    logger.info(f"Tracking content for {url}")
    
    try:
        from app.services.content_tracker import ContentTracker
        from app.database import async_session_maker
        
        tracker = ContentTracker()
        async with async_session_maker() as db:
            return await tracker.process_page(UUID(competitor_id), url, html, title, db)
    except Exception as e:
        logger.error(f"Content tracking failed for {url}: {e}")
        return None


async def monitor_all_competitors():
    """Periodic task to monitor all active competitors."""
    logger.info("Starting periodic monitoring of all competitors")
    
    try:
        result = await _monitor_all()
        return result
    except Exception as e:
        logger.error(f"Periodic monitoring failed: {e}")
        return None


async def _monitor_all():
    """Monitor all competitors for changes."""
    from app.database import get_engine
    from app.models.competitor import Competitor
    from app.models.scan import Scan
    from sqlalchemy import select
    
    _, session_maker = get_engine()
    async with session_maker() as db:
        result = await db.execute(
            select(Competitor).where(
                Competitor.is_active == True,
                Competitor.is_monitoring == True
            )
        )
        competitors = result.scalars().all()
        
        monitored = 0
        for comp in competitors:
            try:
                # Create a scan record
                scan = Scan(competitor_id=comp.id, status="pending")
                db.add(scan)
                await db.commit()
                await db.refresh(scan)
                
                # In a real app we'd trigger this via BackgroundTasks from an endpoint
                # Since this is a standalone function formerly a Celery task,
                # we call it directly here.
                await crawl_competitor(str(comp.id), str(scan.id))
                monitored += 1
            except Exception as e:
                logger.error(f"Failed to queue monitoring for {comp.name}: {e}")
        
        return {"monitored": monitored}


async def cleanup_old_scans(days: int = 30):
    """Clean up old scan data."""
    logger.info(f"Cleaning up scans older than {days} days")
    
    try:
        result = await _cleanup_scans(days)
        return result
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return None


async def _cleanup_scans(days: int):
    """Delete old scan records."""
    from datetime import timedelta
    from app.database import async_session_maker
    from app.models.scan import Scan
    from sqlalchemy import delete
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    async with async_session_maker() as db:
        result = await db.execute(delete(Scan).where(Scan.created_at < cutoff))
        await db.commit()
        return {"deleted": result.rowcount}


async def recalculate_scores(competitor_id: str):
    """Recalculate all scores for a competitor."""
    logger.info(f"Recalculating scores for {competitor_id}")
    
    try:
        result = await _recalculate_scores(UUID(competitor_id))
        return result
    except Exception as e:
        logger.error(f"Score recalculation failed for {competitor_id}: {e}")
        return None


async def _recalculate_scores(competitor_id: UUID):
    """Recalculate SEO, content, and health scores."""
    from app.database import async_session_maker
    from app.models.competitor import Competitor
    from app.models.seo import SeoAnalysis
    from app.models.content import Content
    from sqlalchemy import select, func
    
    async with async_session_maker() as db:
        # Get competitor
        result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
        competitor = result.scalar_one_or_none()
        
        if not competitor:
            return {"error": "Competitor not found"}
        
        # Calculate average SEO score
        seo_result = await db.execute(
            select(func.avg(SeoAnalysis.overall_score))
            .where(SeoAnalysis.competitor_id == competitor_id)
        )
        avg_seo = seo_result.scalar() or 0
        competitor.seo_score = int(avg_seo)
        
        # Calculate content score based on content health
        content_result = await db.execute(
            select(
                func.count(Content.id),
                func.avg(Content.readability_score)
            )
            .where(Content.competitor_id == competitor_id)
        )
        content_count, avg_readability = content_result.one()
        
        if content_count > 0 and avg_readability:
            competitor.content_score = min(100, int((avg_readability + content_count) / 2))
        
        # Calculate overall health score
        competitor.health_score = _calculate_health_score(competitor)
        
        await db.commit()
        
        return {
            "seo_score": competitor.seo_score,
            "content_score": competitor.content_score,
            "health_score": competitor.health_score
        }
