"""Database models for PostgreSQL tables using dataclasses."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID


@dataclass
class BookChunk:
    """Book chunk metadata stored in PostgreSQL."""

    chunk_id: UUID
    book_id: UUID
    text_content: str
    token_count: int
    chapter_id: Optional[str]
    chapter_title: Optional[str]
    section_id: Optional[str]
    section_title: Optional[str]
    page_number: Optional[int]
    start_char_offset: int
    end_char_offset: int
    heading_hierarchy: Optional[list[str]]
    created_at: datetime


@dataclass
class Session:
    """User session for conversation tracking."""

    session_id: UUID
    user_id: Optional[str]
    messages: list[dict[str, Any]]  # JSONB stored as list of dicts
    active_retrieval_mode: str
    current_selection_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


@dataclass
class UserQuery:
    """User query record."""

    query_id: UUID
    session_id: UUID
    query_text: str
    retrieval_mode: str
    text_selection_id: Optional[UUID]
    created_at: datetime


@dataclass
class TextSelection:
    """Text selection for scoped queries."""

    selection_id: UUID
    selected_text: str
    start_char_offset: int
    end_char_offset: int
    chapter_id: Optional[str]
    page_range_start: Optional[int]
    page_range_end: Optional[int]
    created_at: datetime


@dataclass
class RetrievedPassage:
    """Retrieved passage audit trail."""

    retrieval_id: UUID
    query_id: UUID
    chunk_id: UUID
    similarity_score: float
    rank: int
    retrieved_at: datetime


@dataclass
class ChatbotResponse:
    """Chatbot response record."""

    response_id: UUID
    query_id: UUID
    response_text: str
    citations: list[dict[str, Any]]  # JSONB stored as list of citation dicts
    retrieval_quality: float
    validation_passed: bool
    validation_notes: Optional[str]
    llm_model: str
    llm_tokens_used: Optional[int]
    latency_ms: Optional[int]
    created_at: datetime
