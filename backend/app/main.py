import sys
import asyncio

# Fix for Windows asyncio + Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.config import settings
from app.database import init_db, close_db
from app.api import dashboard, competitors, seo, content, prices, products, gaps, alerts, crawl
from app.websocket import manager, websocket_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Web-Spy application...")
    await init_db()
    logger.info("Database initialized")
    yield
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Competitive Analysis Platform - Monitor, analyze, and stay ahead of your competition",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(competitors.router, prefix="/api/competitors", tags=["Competitors"])
app.include_router(seo.router, prefix="/api/seo", tags=["SEO Analysis"])
app.include_router(content.router, prefix="/api/content", tags=["Content Tracking"])
app.include_router(prices.router, prefix="/api/prices", tags=["Price Monitoring"])
app.include_router(products.router, prefix="/api/products", tags=["Product Watching"])
app.include_router(gaps.router, prefix="/api/gaps", tags=["Gap Analysis"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(crawl.router, prefix="/api/crawl", tags=["Crawling"])


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# WebSocket endpoints
@app.websocket("/ws")
async def websocket_default(websocket: WebSocket):
    """Default WebSocket endpoint for all updates."""
    await websocket_endpoint(websocket, "default")


@app.websocket("/ws/scans")
async def websocket_scans(websocket: WebSocket):
    """WebSocket endpoint for scan progress updates."""
    await websocket_endpoint(websocket, "scans")


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts."""
    await websocket_endpoint(websocket, "alerts")


@app.websocket("/ws/competitors")
async def websocket_competitors(websocket: WebSocket):
    """WebSocket endpoint for competitor updates."""
    await websocket_endpoint(websocket, "competitors")
