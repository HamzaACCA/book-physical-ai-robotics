"""Initialize Qdrant collection for book chunks."""

import asyncio
from backend.src.db.qdrant import ensure_collection_exists
from backend.src.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


async def main() -> None:
    """Initialize Qdrant collection."""
    setup_logging()
    logger.info("Starting Qdrant collection initialization")
    await ensure_collection_exists()
    logger.info("Qdrant collection initialization complete")


if __name__ == "__main__":
    asyncio.run(main())
