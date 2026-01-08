"""Initialize database schema."""
import asyncio
from pathlib import Path

from backend.src.db.postgres import get_pool


async def init_schema():
    """Initialize database schema from schema.sql."""
    schema_path = Path("backend/src/db/schema.sql")
    schema_sql = schema_path.read_text()

    pool = await get_pool()
    async with pool.connection() as conn:
        await conn.execute(schema_sql)
        print("✓ Database schema initialized successfully")


if __name__ == "__main__":
    asyncio.run(init_schema())
