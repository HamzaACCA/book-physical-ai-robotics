"""PostgreSQL connection pool management using psycopg3 async."""

import psycopg
from psycopg_pool import AsyncConnectionPool
from typing import AsyncGenerator

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)

# Global connection pool
_pool: AsyncConnectionPool | None = None


async def get_pool() -> AsyncConnectionPool:
    """Get or create the global connection pool."""
    global _pool
    if _pool is None:
        logger.info("Creating PostgreSQL connection pool")
        _pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            min_size=settings.database_pool_min_size,
            max_size=settings.database_pool_max_size,
            timeout=30.0,
        )
        await _pool.open()
    return _pool


async def close_pool() -> None:
    """Close the global connection pool."""
    global _pool
    if _pool is not None:
        logger.info("Closing PostgreSQL connection pool")
        await _pool.close()
        _pool = None


async def get_db() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    """Dependency to get a database connection from the pool."""
    pool = await get_pool()
    async with pool.connection() as conn:
        yield conn
