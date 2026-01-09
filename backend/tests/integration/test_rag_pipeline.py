"""Integration tests for RAG pipeline."""

import asyncio
import pytest
from uuid import uuid4

from openai import AsyncOpenAI

from backend.src.core.config import settings
from backend.src.db.postgres import get_pool
from backend.src.db.qdrant import get_qdrant_client
from backend.src.services.ingestion import (
    chunk_book_content,
    generate_embeddings,
    store_chunks_postgres,
    store_embeddings_qdrant,
)
from backend.src.services.rag import process_query


@pytest.fixture
async def sample_book_setup():
    """Setup: Ingest a sample book for testing."""
    sample_book = """
    Chapter 1: Python Programming

    Python is a high-level programming language. It was created by Guido van Rossum.
    Python emphasizes code readability and simplicity.

    Chapter 2: Data Types

    Python has several built-in data types including integers, floats, strings, and lists.
    Lists are mutable sequences that can hold multiple items.
    Dictionaries store key-value pairs for efficient lookups.

    Chapter 3: Functions

    Functions in Python are defined using the def keyword.
    Functions can accept parameters and return values.
    Lambda functions provide a concise way to create anonymous functions.
    """

    book_id = uuid4()
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Chunk and ingest
    chunks = chunk_book_content(sample_book, book_id)
    embeddings = await generate_embeddings(
        [c["text_content"] for c in chunks], openai_client
    )

    db_pool = await get_pool()
    chunk_ids = await store_chunks_postgres(chunks, book_id, db_pool)

    qdrant_client = get_qdrant_client()
    await store_embeddings_qdrant(chunks, chunk_ids, embeddings, book_id, qdrant_client)

    yield {"book_id": book_id, "chunk_ids": chunk_ids}

    # Cleanup
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM book_chunks WHERE book_id = %s", (book_id,))
            await conn.commit()

    qdrant_client.delete(
        collection_name=settings.qdrant_collection_name,
        points_selector=[str(cid) for cid in chunk_ids],
    )


@pytest.mark.asyncio
async def test_query_with_citations(sample_book_setup):
    """Test that queries return responses with citations."""
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    qdrant_client = get_qdrant_client()
    db_pool = await get_pool()

    # Submit a query
    response = await process_query(
        query_text="Who created Python?",
        session_id=None,
        user_id="test_user",
        openai_client=openai_client,
        qdrant_client=qdrant_client,
        db_pool=db_pool,
    )

    # Assertions
    assert response.response_text, "Response should have text"
    assert len(response.citations) > 0, "Response should have citations"
    assert response.session_id is not None, "Session should be created"
    assert response.retrieval_quality > 0, "Should have retrieval quality score"
    assert response.latency_ms > 0, "Should track latency"

    # Check that response mentions Guido (content check)
    assert (
        "guido" in response.response_text.lower()
    ), "Response should mention Guido van Rossum"

    # Cleanup session
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM sessions WHERE session_id = %s", (response.session_id,)
            )
            await conn.commit()


@pytest.mark.asyncio
async def test_out_of_scope_query(sample_book_setup):
    """Test that out-of-scope queries are properly rejected."""
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    qdrant_client = get_qdrant_client()
    db_pool = await get_pool()

    # Submit an out-of-scope query
    response = await process_query(
        query_text="What is the capital of France?",  # Not in book
        session_id=None,
        user_id="test_user",
        openai_client=openai_client,
        qdrant_client=qdrant_client,
        db_pool=db_pool,
    )

    # Assertions
    assert response.response_text, "Response should have text"
    assert (
        "not" in response.response_text.lower()
        or "couldn't" in response.response_text.lower()
    ), "Response should indicate information not available"
    assert len(response.citations) == 0, "Out-of-scope should have no citations"
    assert response.retrieval_quality == 0.0, "Out-of-scope should have 0 quality"

    # Cleanup session
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM sessions WHERE session_id = %s", (response.session_id,)
            )
            await conn.commit()


@pytest.mark.asyncio
async def test_concurrent_queries(sample_book_setup):
    """Test that the system can handle 10 concurrent queries."""
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    qdrant_client = get_qdrant_client()
    db_pool = await get_pool()

    queries = [
        "What is Python?",
        "Who created Python?",
        "What are Python data types?",
        "What are lists in Python?",
        "What are dictionaries?",
        "How do you define functions?",
        "What is the def keyword?",
        "What are lambda functions?",
        "Tell me about code readability",
        "What is Python used for?",
    ]

    # Run queries concurrently
    tasks = [
        process_query(
            query_text=q,
            session_id=None,
            user_id=f"user_{i}",
            openai_client=openai_client,
            qdrant_client=qdrant_client,
            db_pool=db_pool,
        )
        for i, q in enumerate(queries)
    ]

    responses = await asyncio.gather(*tasks)

    # Assertions
    assert len(responses) == 10, "Should handle all 10 queries"
    assert all(r.response_text for r in responses), "All responses should have text"
    assert all(r.latency_ms < 5000 for r in responses), "All queries should complete in <5s"

    # Cleanup sessions
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            for response in responses:
                await cur.execute(
                    "DELETE FROM sessions WHERE session_id = %s", (response.session_id,)
                )
            await conn.commit()


@pytest.mark.asyncio
async def test_session_continuity(sample_book_setup):
    """Test that conversation context is maintained across queries."""
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    qdrant_client = get_qdrant_client()
    db_pool = await get_pool()

    # First query
    response1 = await process_query(
        query_text="What is Python?",
        session_id=None,
        user_id="test_user",
        openai_client=openai_client,
        qdrant_client=qdrant_client,
        db_pool=db_pool,
    )

    session_id = response1.session_id

    # Second query in same session
    response2 = await process_query(
        query_text="Tell me more about it",  # Relies on context
        session_id=session_id,
        user_id="test_user",
        openai_client=openai_client,
        qdrant_client=qdrant_client,
        db_pool=db_pool,
    )

    # Assertions
    assert response2.session_id == session_id, "Should use same session"
    assert response2.response_text, "Should generate response with context"

    # Cleanup session
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM sessions WHERE session_id = %s", (session_id,)
            )
            await conn.commit()
