"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.src.api.routes import chat
from backend.src.core.config import settings
from backend.src.core.logging import get_logger, setup_logging
from backend.src.db.postgres import get_pool, close_pool

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting up - initializing database pool")
    await get_pool()  # Initialize pool on startup
    yield
    # Shutdown
    logger.info("Shutting down - closing database pool")
    await close_pool()


# Create FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="API for chatbot with RAG (Retrieval-Augmented Generation)",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RAG Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/v1/chat",
            "docs": "/docs",
            "health": "/api/v1/chat/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
