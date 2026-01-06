"""Qdrant client setup and utilities."""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)

# Global Qdrant client
_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """Get or create the global Qdrant client."""
    global _client
    if _client is None:
        logger.info(f"Creating Qdrant client for {settings.qdrant_url}")
        _client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=60.0,
        )
    return _client


async def close_qdrant_client() -> None:
    """Close the global Qdrant client."""
    global _client
    if _client is not None:
        logger.info("Closing Qdrant client")
        _client.close()
        _client = None


async def ensure_collection_exists() -> None:
    """Ensure the Qdrant collection exists with correct configuration."""
    client = get_qdrant_client()
    collection_name = settings.qdrant_collection_name

    # Check if collection exists
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if collection_name not in collection_names:
        logger.info(f"Creating Qdrant collection: {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.qdrant_vector_size, distance=Distance.COSINE
            ),
        )
        logger.info(f"Collection {collection_name} created successfully")
    else:
        logger.info(f"Collection {collection_name} already exists")
