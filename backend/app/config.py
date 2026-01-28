from pydantic_settings import BaseSettings
from pydantic import computed_field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "Web-Spy"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database - individual components (Supabase web-spy)
    db_host: str = "aws-0-ap-south-1.pooler.supabase.com"
    db_port: int = 5432
    db_name: str = "postgres"
    db_user: str = "postgres.vbjbywbuiwnqjdftbdfb"
    db_password: str
    
    @computed_field
    @property
    def database_url(self) -> str:
        """Construct database URL from components with proper URL encoding."""
        from urllib.parse import quote_plus
        # URL-encode password to handle special characters like @, #, %, etc.
        encoded_password = quote_plus(self.db_password)
        return f"postgresql+asyncpg://{self.db_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # Redis (Optional/Removed)
    redis_url: Optional[str] = None
    
    # Celery (Optional/Removed)
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    
    # Crawler Settings
    crawler_concurrent_contexts: int = 5
    crawler_page_timeout: int = 30000  # milliseconds
    crawler_navigation_timeout: int = 30000
    crawler_max_retries: int = 3
    crawler_retry_delay: float = 1.0  # seconds
    crawler_respect_robots_txt: bool = True
    
    # Resource blocking for speed
    block_images: bool = True
    block_fonts: bool = True
    block_media: bool = True
    block_css: bool = False  # Keep CSS for accurate rendering
    
    # Rate limiting
    request_delay_min: float = 0.5  # seconds
    request_delay_max: float = 2.0
    
    # CORS
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
