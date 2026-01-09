"""FastAPI dependency injection functions."""

from typing import AsyncGenerator

from psycopg_pool import AsyncConnectionPool
from qdrant_client import QdrantClient

from backend.src.db.postgres import get_pool
from backend.src.db.qdrant import get_qdrant_client


async def get_db() -> AsyncGenerator[AsyncConnectionPool, None]:
    """Get PostgreSQL connection pool dependency.

    Yields:
        AsyncConnectionPool for database operations
    """
    pool = await get_pool()
    yield pool


async def get_qdrant() -> QdrantClient:
    """Get Qdrant client dependency.

    Returns:
        QdrantClient for vector operations
    """
    return get_qdrant_client()
