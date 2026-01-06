"""Session management service for conversation tracking."""

import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from psycopg_pool import AsyncConnectionPool

from backend.src.core.logging import get_logger
from backend.src.models.database import Session
from backend.src.models.domain import Message, MessageRole, RetrievalMode

logger = get_logger(__name__)


async def create_session(
    db_pool: AsyncConnectionPool,
    user_id: Optional[str] = None,
    retrieval_mode: RetrievalMode = RetrievalMode.FULL_BOOK,
) -> UUID:
    """Create a new conversation session.

    Args:
        db_pool: PostgreSQL connection pool
        user_id: Optional user identifier
        retrieval_mode: Initial retrieval mode

    Returns:
        UUID of the created session
    """
    session_id = uuid4()
    logger.info(f"Creating new session {session_id} for user {user_id}")

    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO sessions (
                    session_id, user_id, messages, active_retrieval_mode
                ) VALUES (%s, %s, %s, %s)
                """,
                (session_id, user_id, json.dumps([]), retrieval_mode.value),
            )
            await conn.commit()

    logger.info(f"Created session {session_id}")
    return session_id


async def load_session(
    session_id: UUID,
    db_pool: AsyncConnectionPool,
) -> Optional[Session]:
    """Load a session from the database.

    Args:
        session_id: Session identifier
        db_pool: PostgreSQL connection pool

    Returns:
        Session object if found, None otherwise
    """
    logger.debug(f"Loading session {session_id}")

    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT session_id, user_id, messages, active_retrieval_mode,
                       current_selection_id, created_at, updated_at, expires_at
                FROM sessions
                WHERE session_id = %s AND expires_at > NOW()
                """,
                (session_id,),
            )
            row = await cur.fetchone()

    if not row:
        logger.warning(f"Session {session_id} not found or expired")
        return None

    session = Session(
        session_id=row[0],
        user_id=row[1],
        messages=row[2],  # JSONB already parsed
        active_retrieval_mode=row[3],
        current_selection_id=row[4],
        created_at=row[5],
        updated_at=row[6],
        expires_at=row[7],
    )

    logger.debug(f"Loaded session {session_id} with {len(session.messages)} messages")
    return session


async def update_session(
    session_id: UUID,
    db_pool: AsyncConnectionPool,
    new_message: Optional[Message] = None,
    retrieval_mode: Optional[RetrievalMode] = None,
    selection_id: Optional[UUID] = None,
) -> None:
    """Update a session with new messages or settings.

    Args:
        session_id: Session identifier
        db_pool: PostgreSQL connection pool
        new_message: Optional new message to append
        retrieval_mode: Optional new retrieval mode
        selection_id: Optional text selection ID
    """
    logger.debug(f"Updating session {session_id}")

    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            # Load current session
            session = await load_session(session_id, db_pool)
            if not session:
                raise ValueError(f"Session {session_id} not found or expired")

            # Append new message if provided
            messages = session.messages
            if new_message:
                message_dict = {
                    "role": new_message.role.value,
                    "content": new_message.content,
                    "timestamp": new_message.timestamp.isoformat(),
                    "citations": (
                        [str(c) for c in new_message.citations]
                        if new_message.citations
                        else None
                    ),
                }
                messages.append(message_dict)

                # Keep only last 5 Q&A pairs (10 messages)
                if len(messages) > 10:
                    messages = messages[-10:]

            # Update session
            update_mode = retrieval_mode.value if retrieval_mode else session.active_retrieval_mode
            update_selection = selection_id if selection_id is not None else session.current_selection_id

            await cur.execute(
                """
                UPDATE sessions
                SET messages = %s,
                    active_retrieval_mode = %s,
                    current_selection_id = %s
                WHERE session_id = %s
                """,
                (json.dumps(messages), update_mode, update_selection, session_id),
            )
            await conn.commit()

    logger.debug(f"Updated session {session_id}")


async def expire_session(
    session_id: UUID,
    db_pool: AsyncConnectionPool,
) -> None:
    """Manually expire a session (delete).

    Args:
        session_id: Session identifier
        db_pool: PostgreSQL connection pool
    """
    logger.info(f"Expiring session {session_id}")

    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM sessions WHERE session_id = %s",
                (session_id,),
            )
            await conn.commit()

    logger.info(f"Expired session {session_id}")


async def get_conversation_context(
    session_id: UUID,
    db_pool: AsyncConnectionPool,
    max_messages: int = 10,
) -> list[dict[str, str]]:
    """Get conversation history formatted for LLM context.

    Args:
        session_id: Session identifier
        db_pool: PostgreSQL connection pool
        max_messages: Maximum number of recent messages to include

    Returns:
        List of message dictionaries with role and content
    """
    session = await load_session(session_id, db_pool)
    if not session:
        return []

    # Format messages for LLM (last N messages)
    messages = session.messages[-max_messages:]
    formatted = []
    for msg in messages:
        formatted.append(
            {
                "role": msg["role"],
                "content": msg["content"],
            }
        )

    logger.debug(f"Retrieved {len(formatted)} context messages for session {session_id}")
    return formatted
