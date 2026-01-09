"""Initialize books table schema."""
import asyncio
from pathlib import Path

from backend.src.db.postgres import get_pool


async def init_books_schema():
    """Initialize books table schema."""
    schema_path = Path("backend/src/db/books_schema.sql")
    schema_sql = schema_path.read_text()

    pool = await get_pool()
    async with pool.connection() as conn:
        await conn.execute(schema_sql)
        print("✓ Books table schema initialized successfully")


if __name__ == "__main__":
    asyncio.run(init_books_schema())
