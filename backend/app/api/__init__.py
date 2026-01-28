from app.api.dashboard import router as dashboard_router
from app.api.competitors import router as competitors_router
from app.api.seo import router as seo_router
from app.api.content import router as content_router
from app.api.prices import router as prices_router
from app.api.products import router as products_router
from app.api.gaps import router as gaps_router
from app.api.alerts import router as alerts_router
from app.api.crawl import router as crawl_router

__all__ = [
    "dashboard_router",
    "competitors_router", 
    "seo_router",
    "content_router",
    "prices_router",
    "products_router",
    "gaps_router",
    "alerts_router",
    "crawl_router"
]
