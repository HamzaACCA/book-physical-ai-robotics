"""FastAPI application initialization."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.src.api.routes.health import router as health_router
from backend.src.api.routes.query import router as query_router
from backend.src.core.config import settings
from backend.src.core.logging import get_logger, setup_logging
from backend.src.db.postgres import close_pool, get_pool
from backend.src.db.qdrant import close_qdrant_client, ensure_collection_exists
from backend.src.models.domain import ErrorResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    setup_logging()
    logger.info("Starting RAG Chatbot API")

    # Initialize database connections
    logger.info("Initializing PostgreSQL connection pool")
    await get_pool()

    # Initialize Qdrant collection
    logger.info("Ensuring Qdrant collection exists")
    await ensure_collection_exists()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down RAG Chatbot API")
    await close_pool()
    await close_qdrant_client()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="RAG Chatbot API",
    description="Integrated RAG chatbot for querying book content",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(query_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    from datetime import datetime

    logger.warning(f"Validation error: {exc.errors()}")
    error_response = ErrorResponse(
        error="ValidationError",
        message="Request validation failed",
        timestamp=datetime.now(),
        details={"errors": exc.errors()},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    from datetime import datetime

    logger.error(f"Unexpected error: {exc}", exc_info=True)
    error_response = ErrorResponse(
        error="InternalServerError",
        message="An unexpected error occurred",
        timestamp=datetime.now(),
        details={"type": type(exc).__name__, "message": str(exc)},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode="json"),
    )
