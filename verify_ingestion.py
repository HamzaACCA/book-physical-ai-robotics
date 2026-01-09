"""Verify book ingestion."""
import asyncio

from backend.src.db.postgres import get_pool
from backend.src.db.qdrant import get_qdrant_client
from backend.src.core.config import settings


async def verify():
    """Verify the book was ingested correctly."""
    # Check PostgreSQL
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM book_chunks")
            result = await cur.fetchone()
            print(f"✓ PostgreSQL: {result[0]} chunks stored")

            await cur.execute("SELECT book_id, text_content FROM book_chunks LIMIT 1")
            chunk = await cur.fetchone()
            if chunk:
                print(f"  Sample chunk preview: {chunk[1][:100]}...")

    # Check Qdrant
    client = get_qdrant_client()
    collection_info = client.get_collection(settings.qdrant_collection_name)
    print(f"✓ Qdrant: {collection_info.points_count} vectors stored")
    print(f"  Vector size: {collection_info.config.params.vectors.size} dimensions")


if __name__ == "__main__":
    asyncio.run(verify())
