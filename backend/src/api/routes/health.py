"""Health check endpoint."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from openai import AsyncOpenAI
from psycopg_pool import AsyncConnectionPool
from qdrant_client import QdrantClient

from backend.src.api.dependencies import get_db, get_qdrant
from backend.src.core.config import settings
from backend.src.core.logging import get_logger
from backend.src.models.domain import HealthResponse

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncConnectionPool = Depends(get_db),
    qdrant: QdrantClient = Depends(get_qdrant),
) -> HealthResponse:
    """Check health of all dependencies.

    Verifies connectivity to:
    - PostgreSQL database
    - Qdrant vector database
    - OpenAI API

    Returns:
        HealthResponse with status and details
    """
    details = {}

    # Check PostgreSQL
    try:
        async with db.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()
        details["postgresql"] = "healthy"
        logger.debug("PostgreSQL health check passed")
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        details["postgresql"] = f"unhealthy: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL connection failed",
        )

    # Check Qdrant
    try:
        collection_info = qdrant.get_collection(settings.qdrant_collection_name)
        details["qdrant"] = {
            "status": "healthy",
            "collection": settings.qdrant_collection_name,
            "vectors_count": collection_info.vectors_count,
        }
        logger.debug("Qdrant health check passed")
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        details["qdrant"] = f"unhealthy: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Qdrant connection failed",
        )

    # Check OpenAI API
    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        # Simple API test - list models
        models = await client.models.list()
        details["openai"] = {
            "status": "healthy",
            "models_available": len(models.data),
        }
        logger.debug("OpenAI API health check passed")
    except Exception as e:
        logger.error(f"OpenAI API health check failed: {e}")
        details["openai"] = f"unhealthy: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API connection failed",
        )

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        details=details,
    )
