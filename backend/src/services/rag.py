"""RAG orchestration service combining retrieval, generation, and validation."""

import time
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from openai import AsyncOpenAI
from psycopg_pool import AsyncConnectionPool
from qdrant_client import QdrantClient

from backend.src.core.config import settings
from backend.src.core.logging import get_logger, log_query_metrics
from backend.src.models.domain import Citation, Message, MessageRole, QueryResponse
from backend.src.services.retrieval import retrieve_full_book, store_retrieval_audit
from backend.src.services.session import (
    create_session,
    get_conversation_context,
    load_session,
    update_session,
)
from backend.src.services.validation import (
    handle_out_of_scope_query,
    validate_response_grounding,
)

logger = get_logger(__name__)


async def process_query(
    query_text: str,
    session_id: Optional[UUID],
    user_id: Optional[str],
    openai_client: AsyncOpenAI,
    qdrant_client: QdrantClient,
    db_pool: AsyncConnectionPool,
) -> QueryResponse:
    """Process a full book query through the RAG pipeline.

    Pipeline steps:
    1. Create or load session
    2. Retrieve relevant chunks
    3. Check for out-of-scope queries
    4. Generate response with LLM
    5. Validate response grounding
    6. Store query, response, and audit trail
    7. Update session

    Args:
        query_text: User's question
        session_id: Optional existing session ID
        user_id: Optional user identifier
        openai_client: OpenAI async client
        qdrant_client: Qdrant client
        db_pool: PostgreSQL connection pool

    Returns:
        QueryResponse with answer and citations
    """
    start_time = time.time()
    logger.info(f"Processing query: {query_text[:100]}...")

    # 1. Create or load session
    if session_id is None:
        session_id = await create_session(db_pool, user_id)
    else:
        session = await load_session(session_id, db_pool)
        if session is None:
            logger.warning(f"Session {session_id} not found, creating new session")
            session_id = await create_session(db_pool, user_id)

    # 2. Retrieve relevant chunks
    retrieved_chunks = await retrieve_full_book(
        query_text=query_text,
        openai_client=openai_client,
        qdrant_client=qdrant_client,
        db_pool=db_pool,
        top_k=settings.rag_top_k,
    )

    # 3. Check for out-of-scope queries
    is_out_of_scope, out_of_scope_response = await handle_out_of_scope_query(
        retrieved_chunks
    )

    if is_out_of_scope:
        logger.info("Returning out-of-scope response")
        response_id = uuid4()
        query_id = uuid4()

        # Store query and response
        await _store_query(query_id, session_id, query_text, "FULL_BOOK", None, db_pool)
        await _store_response(
            response_id=response_id,
            query_id=query_id,
            response_text=out_of_scope_response,
            citations=[],
            retrieval_quality=0.0,
            validation_passed=True,
            validation_notes="Out-of-scope query",
            db_pool=db_pool,
        )

        # Update session
        await update_session(
            session_id,
            db_pool,
            new_message=Message(
                role=MessageRole.USER,
                content=query_text,
                timestamp=datetime.now(),
            ),
        )
        await update_session(
            session_id,
            db_pool,
            new_message=Message(
                role=MessageRole.ASSISTANT,
                content=out_of_scope_response,
                timestamp=datetime.now(),
            ),
        )

        latency_ms = int((time.time() - start_time) * 1000)
        return QueryResponse(
            response_id=response_id,
            query_id=query_id,
            session_id=session_id,
            response_text=out_of_scope_response,
            citations=[],
            retrieval_quality=0.0,
            latency_ms=latency_ms,
        )

    # 4. Generate response with LLM
    query_id = uuid4()
    conversation_history = await get_conversation_context(session_id, db_pool)

    response_text, citations = await _generate_response(
        query_text=query_text,
        retrieved_chunks=retrieved_chunks,
        conversation_history=conversation_history,
        openai_client=openai_client,
    )

    # 5. Validate response grounding
    validation_passed, retrieval_quality, validation_notes = (
        await validate_response_grounding(
            response_text=response_text,
            retrieved_chunks=retrieved_chunks,
            openai_client=openai_client,
        )
    )

    # 6. Store query, response, and audit trail
    response_id = uuid4()
    await _store_query(query_id, session_id, query_text, "FULL_BOOK", None, db_pool)
    await store_retrieval_audit(query_id, retrieved_chunks, db_pool)
    await _store_response(
        response_id=response_id,
        query_id=query_id,
        response_text=response_text,
        citations=[c.model_dump() for c in citations],
        retrieval_quality=retrieval_quality,
        validation_passed=validation_passed,
        validation_notes=validation_notes,
        db_pool=db_pool,
    )

    # 7. Update session
    await update_session(
        session_id,
        db_pool,
        new_message=Message(
            role=MessageRole.USER,
            content=query_text,
            timestamp=datetime.now(),
        ),
    )
    await update_session(
        session_id,
        db_pool,
        new_message=Message(
            role=MessageRole.ASSISTANT,
            content=response_text,
            timestamp=datetime.now(),
            citations=[c.chunk_id for c in citations],
        ),
    )

    # Log metrics
    latency_ms = int((time.time() - start_time) * 1000)
    log_query_metrics(
        query_id=str(query_id),
        retrieval_quality=retrieval_quality,
        latency_ms=latency_ms,
        validation_passed=validation_passed,
        extra={"session_id": str(session_id), "num_citations": len(citations)},
    )

    return QueryResponse(
        response_id=response_id,
        query_id=query_id,
        session_id=session_id,
        response_text=response_text,
        citations=citations,
        retrieval_quality=retrieval_quality,
        latency_ms=latency_ms,
    )


async def _generate_response(
    query_text: str,
    retrieved_chunks: list[dict[str, Any]],
    conversation_history: list[dict[str, str]],
    openai_client: AsyncOpenAI,
) -> tuple[str, list[Citation]]:
    """Generate response using OpenAI Chat Completions.

    Args:
        query_text: User's question
        retrieved_chunks: Retrieved context chunks
        conversation_history: Previous conversation messages
        openai_client: OpenAI async client

    Returns:
        Tuple of (response_text, citations)
    """
    logger.debug("Generating LLM response")

    # Build context from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        context_parts.append(f"[{i}] {chunk['text_content']}")

    context = "\n\n".join(context_parts)

    # System prompt for content fidelity
    system_prompt = """You are a helpful assistant that answers questions strictly based on the provided book content.

CRITICAL RULES:
1. ONLY use information from the provided context passages
2. ALWAYS cite your sources using [1], [2], etc. for each claim
3. If information is not in the context, say "This information is not available in the book"
4. Do NOT add external knowledge or assumptions
5. Be concise and accurate"""

    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append(
        {
            "role": "user",
            "content": f"Context from book:\n\n{context}\n\nQuestion: {query_text}",
        }
    )

    # Generate response
    completion = await openai_client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=messages,
        temperature=settings.rag_temperature,
        max_tokens=settings.rag_max_tokens,
    )

    response_text = completion.choices[0].message.content or ""

    # Create citations
    citations = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        citation = Citation(
            chunk_id=chunk["chunk_id"],
            reference=f"[{i}]",
            chapter_title=chunk.get("chapter_title"),
            section_title=chunk.get("section_title"),
            page_number=chunk.get("page_number"),
            text_preview=chunk["text_content"][:200],
        )
        citations.append(citation)

    logger.debug(f"Generated response with {len(citations)} citations")
    return response_text, citations


async def _store_query(
    query_id: UUID,
    session_id: UUID,
    query_text: str,
    retrieval_mode: str,
    text_selection_id: Optional[UUID],
    db_pool: AsyncConnectionPool,
) -> None:
    """Store query in database."""
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO user_queries (
                    query_id, session_id, query_text, retrieval_mode, text_selection_id
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (query_id, session_id, query_text, retrieval_mode, text_selection_id),
            )
            await conn.commit()


async def _store_response(
    response_id: UUID,
    query_id: UUID,
    response_text: str,
    citations: list[dict[str, Any]],
    retrieval_quality: float,
    validation_passed: bool,
    validation_notes: str,
    db_pool: AsyncConnectionPool,
) -> None:
    """Store response in database."""
    import json

    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO chatbot_responses (
                    response_id, query_id, response_text, citations,
                    retrieval_quality, validation_passed, validation_notes,
                    llm_model, llm_tokens_used, latency_ms
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    response_id,
                    query_id,
                    response_text,
                    json.dumps(citations),
                    retrieval_quality,
                    validation_passed,
                    validation_notes,
                    settings.openai_chat_model,
                    None,  # tokens not tracked yet
                    None,  # latency tracked at higher level
                ),
            )
            await conn.commit()
