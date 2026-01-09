"""Query API routes for RAG chatbot."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from openai import AsyncOpenAI
from psycopg_pool import AsyncConnectionPool
from qdrant_client import QdrantClient

from backend.src.api.dependencies import get_db, get_qdrant
from backend.src.core.config import settings
from backend.src.core.logging import get_logger
from backend.src.models.domain import (
    Message,
    MessageRole,
    QueryRequest,
    QueryResponse,
    SessionResponse,
)
from backend.src.services.rag import process_query
from backend.src.services.session import expire_session, load_session

router = APIRouter(prefix="/api/v1", tags=["query"])
logger = get_logger(__name__)


@router.post("/query", response_model=QueryResponse)
async def submit_query(
    request: QueryRequest,
    db: AsyncConnectionPool = Depends(get_db),
    qdrant: QdrantClient = Depends(get_qdrant),
) -> QueryResponse:
    """Submit a query for full book search.

    Args:
        request: Query request with query text and optional session ID
        db: PostgreSQL connection pool
        qdrant: Qdrant client

    Returns:
        QueryResponse with answer and citations
    """
    logger.info(f"Received query: {request.query_text[:100]}...")

    try:
        openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

        response = await process_query(
            query_text=request.query_text,
            session_id=request.session_id,
            user_id=request.user_id,
            openai_client=openai_client,
            qdrant_client=qdrant,
            db_pool=db,
        )

        return response

    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}",
        )


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncConnectionPool = Depends(get_db),
) -> SessionResponse:
    """Retrieve session conversation history.

    Args:
        session_id: Session identifier
        db: PostgreSQL connection pool

    Returns:
        SessionResponse with conversation history
    """
    logger.info(f"Retrieving session {session_id}")

    session = await load_session(session_id, db)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found or expired",
        )

    # Convert JSONB messages to Message objects
    messages = []
    for msg in session.messages:
        messages.append(
            Message(
                role=MessageRole(msg["role"]),
                content=msg["content"],
                timestamp=msg["timestamp"],
                citations=(
                    [UUID(c) for c in msg["citations"]] if msg.get("citations") else None
                ),
            )
        )

    return SessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        messages=messages,
        active_retrieval_mode=session.active_retrieval_mode,
        created_at=session.created_at,
        updated_at=session.updated_at,
        expires_at=session.expires_at,
    )


@router.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    db: AsyncConnectionPool = Depends(get_db),
) -> None:
    """Delete a session.

    Args:
        session_id: Session identifier
        db: PostgreSQL connection pool
    """
    logger.info(f"Deleting session {session_id}")

    try:
        await expire_session(session_id, db)
    except Exception as e:
        logger.error(f"Session deletion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session deletion failed: {str(e)}",
        )
