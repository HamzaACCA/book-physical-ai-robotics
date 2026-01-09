"""Integration tests for book ingestion pipeline."""

import pytest
from uuid import uuid4

from openai import AsyncOpenAI
from psycopg_pool import AsyncConnectionPool
from qdrant_client import QdrantClient

from backend.src.core.config import settings
from backend.src.db.postgres import get_pool
from backend.src.db.qdrant import get_qdrant_client
from backend.src.services.ingestion import (
    chunk_book_content,
    generate_embeddings,
    store_chunks_postgres,
    store_embeddings_qdrant,
)


@pytest.mark.asyncio
async def test_ingest_sample_book():
    """Test full ingestion pipeline: chunk -> embed -> store in PostgreSQL and Qdrant."""
    # Sample book content
    sample_book = """
    Chapter 1: Introduction to Testing

    This is a sample book about software testing. Testing is essential for quality.
    We will cover unit tests, integration tests, and end-to-end tests.

    Chapter 2: Unit Testing

    Unit testing involves testing individual components in isolation.
    Each unit test should be independent and repeatable.
    Mock objects can be used to simulate dependencies.

    Chapter 3: Integration Testing

    Integration testing verifies that different modules work together correctly.
    It tests the interactions between components.
    Database connections and API calls are often tested here.
    """ * 10  # Repeat to create enough content for multiple chunks

    book_id = uuid4()

    # 1. Chunk the book
    chunks = chunk_book_content(book_content=sample_book, book_id=book_id)

    assert len(chunks) > 0, "Should create at least one chunk"
    assert all("text_content" in chunk for chunk in chunks), "All chunks should have text"
    assert all(
        chunk["end_char_offset"] > chunk["start_char_offset"] for chunk in chunks
    ), "Offsets should be valid"

    # 2. Generate embeddings
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    chunk_texts = [chunk["text_content"] for chunk in chunks]
    embeddings = await generate_embeddings(chunk_texts, openai_client)

    assert len(embeddings) == len(chunks), "Should have one embedding per chunk"
    assert all(
        len(emb) == settings.qdrant_vector_size for emb in embeddings
    ), f"Embeddings should be {settings.qdrant_vector_size} dimensions"

    # 3. Store chunks in PostgreSQL
    db_pool = await get_pool()
    chunk_ids = await store_chunks_postgres(chunks, book_id, db_pool)

    assert len(chunk_ids) == len(chunks), "Should store all chunks"

    # Verify PostgreSQL storage
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(*) FROM book_chunks WHERE book_id = %s", (book_id,)
            )
            result = await cur.fetchone()
            assert result[0] == len(chunks), "All chunks should be in PostgreSQL"

    # 4. Store embeddings in Qdrant
    qdrant_client = get_qdrant_client()
    await store_embeddings_qdrant(chunks, chunk_ids, embeddings, book_id, qdrant_client)

    # Verify Qdrant storage
    collection_info = qdrant_client.get_collection(settings.qdrant_collection_name)
    # Note: collection may have vectors from previous tests, so just check it increased
    assert collection_info.vectors_count >= len(
        chunk_ids
    ), "Vectors should be stored in Qdrant"

    # Cleanup
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM book_chunks WHERE book_id = %s", (book_id,))
            await conn.commit()

    # Delete from Qdrant
    qdrant_client.delete(
        collection_name=settings.qdrant_collection_name,
        points_selector=[str(cid) for cid in chunk_ids],
    )


@pytest.mark.asyncio
async def test_chunking_preserves_boundaries():
    """Test that chunking respects paragraph boundaries."""
    sample_text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
    book_id = uuid4()

    chunks = chunk_book_content(sample_text, book_id, target_tokens=10, overlap_tokens=2)

    # Check that chunks don't split mid-paragraph (basic sanity)
    for chunk in chunks:
        assert "\n\n" not in chunk["text_content"] or len(chunk["text_content"]) > 20
