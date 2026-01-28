from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData, text
from sqlalchemy.pool import NullPool
from loguru import logger
import sys

from app.config import settings

# Naming convention for migrations
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    metadata = metadata


def _create_engine():
    """Create database engine - using NullPool for Supabase compatibility."""
    # Use NullPool to avoid connection pooling issues with Supabase
    # Each request gets a fresh connection that's properly closed after
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        poolclass=NullPool,  # No pooling - new connection per request
    )
    
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )
    
    return engine, session_maker


# Create global engine and session maker
_engine = None
_session_maker = None


def get_engine():
    """Get or create the engine."""
    global _engine, _session_maker
    if _engine is None:
        _engine, _session_maker = _create_engine()
    return _engine, _session_maker


async def get_db():
    """Dependency for getting database sessions."""
    _, session_maker = get_engine()
    
    async with session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise


async def init_db():
    """Initialize and verify database connection."""
    try:
        eng, _ = get_engine()
        
        # Test connection
        async with eng.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
            
        logger.info("Database connection established successfully")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Database connection failed: {error_msg}")
        
        if "Tenant or user not found" in error_msg:
            logger.error("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  DATABASE CONNECTION ERROR                                                    ║
║                                                                              ║
║  The database password appears to be incorrect.                              ║
║                                                                              ║
║  To fix this:                                                                ║
║  1. Go to: https://supabase.com/dashboard/project/vbjbywbuiwnqjdftbdfb/settings/database  ║
║  2. Click "Reset database password" or view the current password            ║
║  3. Update DATABASE_URL in backend/.env with the correct password           ║
║                                                                              ║
║  Format: postgresql+asyncpg://postgres.vbjbywbuiwnqjdftbdfb:PASSWORD@...     ║
╚══════════════════════════════════════════════════════════════════════════════╝
            """)
        
        raise


async def close_db():
    """Close database connections."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")


def get_session_maker():
    """Get the async session maker (for backward compatibility)."""
    _, session_maker = get_engine()
    return session_maker


# Export async_session_maker for backward compatibility
# This is a function that returns a session when called
class _SessionMakerProxy:
    """Proxy class to lazily get session maker."""
    def __call__(self):
        _, session_maker = get_engine()
        return session_maker()


async_session_maker = _SessionMakerProxy()
