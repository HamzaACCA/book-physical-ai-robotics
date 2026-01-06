"""Chat API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.src.core.logging import get_logger
from backend.src.db.postgres import get_pool
from backend.src.services.chat import (
    chat_with_rag,
    create_chat_session,
    get_chat_history,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat message request."""

    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(None, description="Session ID (optional, creates new if not provided)")
    selected_text: str | None = Field(None, max_length=10000, description="Selected text to restrict context (optional)")


class ChatResponse(BaseModel):
    """Chat message response."""

    answer: str
    session_id: str
    sources: list[dict]


class SessionResponse(BaseModel):
    """Session creation response."""

    session_id: str


class HistoryResponse(BaseModel):
    """Chat history response."""

    messages: list[dict]
    session_id: str


@router.post("/session", response_model=SessionResponse)
async def new_session():
    """Create a new chat session."""
    try:
        pool = await get_pool()
        session_id = await create_chat_session(pool)
        return {"session_id": str(session_id)}
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat session")


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a chat message and get AI response."""
    try:
        pool = await get_pool()

        # Create new session if not provided
        if request.session_id:
            try:
                session_id = UUID(request.session_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid session ID format")
        else:
            session_id = await create_chat_session(pool)

        # Process chat message
        response = await chat_with_rag(
            query=request.message,
            session_id=session_id,
            db_pool=pool,
            selected_text=request.selected_text
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    """Get chat history for a session."""
    try:
        pool = await get_pool()

        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        messages = await get_chat_history(session_uuid, pool)

        return {
            "messages": messages,
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chat"}
