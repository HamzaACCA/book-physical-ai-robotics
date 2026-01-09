"""Domain models using Pydantic for validation and serialization."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RetrievalMode(str, Enum):
    """Retrieval mode for queries."""

    FULL_BOOK = "FULL_BOOK"
    SELECTED_TEXT = "SELECTED_TEXT"


class MessageRole(str, Enum):
    """Role of a message in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"


class TextSelection(BaseModel):
    """Text selection for scoped queries."""

    selected_text: str = Field(..., min_length=1, max_length=50000)
    start_char_offset: int = Field(..., ge=0)
    end_char_offset: int = Field(..., gt=0)
    chapter_id: Optional[str] = None
    page_range_start: Optional[int] = Field(None, ge=1)
    page_range_end: Optional[int] = Field(None, ge=1)

    @field_validator("end_char_offset")
    @classmethod
    def validate_offsets(cls, v: int, info) -> int:
        if "start_char_offset" in info.data and v <= info.data["start_char_offset"]:
            raise ValueError("end_char_offset must be greater than start_char_offset")
        return v


class QueryRequest(BaseModel):
    """Request model for submitting a query."""

    query_text: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[UUID] = None
    user_id: Optional[str] = Field(None, max_length=255)


class QueryWithSelectionRequest(BaseModel):
    """Request model for submitting a query with text selection."""

    query_text: str = Field(..., min_length=1, max_length=1000)
    selection: TextSelection
    session_id: Optional[UUID] = None
    user_id: Optional[str] = Field(None, max_length=255)


class Citation(BaseModel):
    """Source citation for a response."""

    chunk_id: UUID
    reference: str
    chapter_title: Optional[str] = None
    section_title: Optional[str] = None
    page_number: Optional[int] = Field(None, ge=1)
    text_preview: str = Field(..., max_length=200)


class QueryResponse(BaseModel):
    """Response model for a query."""

    response_id: UUID
    query_id: UUID
    session_id: UUID
    response_text: str
    citations: List[Citation]
    retrieval_quality: float = Field(..., ge=0.0, le=1.0)
    latency_ms: int = Field(..., ge=0)


class Message(BaseModel):
    """Message in a conversation."""

    role: MessageRole
    content: str
    timestamp: datetime
    citations: Optional[List[UUID]] = None


class SessionResponse(BaseModel):
    """Response model for session data."""

    session_id: UUID
    user_id: Optional[str] = None
    messages: List[Message]
    active_retrieval_mode: RetrievalMode
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    details: Optional[dict] = None


class IngestionRequest(BaseModel):
    """Request model for book ingestion."""

    book_file_url: str
    book_id: UUID
    book_title: str = Field(..., max_length=500)
    metadata: Optional[dict] = None


class IngestionResponse(BaseModel):
    """Response model for ingestion job."""

    job_id: UUID
    status: str
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    message: str
    timestamp: datetime
    details: Optional[dict] = None
