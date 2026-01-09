"""Retrieval service for vector search and context retrieval."""

from typing import Any
from uuid import UUID

from openai import AsyncOpenAI
from psycopg_pool import AsyncConnectionPool
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, PointStruct, ScoredPoint

from backend.src.core.config import settings
from backend.src.core.logging import get_logger
from backend.src.models.database import BookChunk

logger = get_logger(__name__)


async def retrieve_full_book(
    query_text: str,
    openai_client: AsyncOpenAI,
    qdrant_client: QdrantClient,
    db_pool: AsyncConnectionPool,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve relevant chunks from the full book using vector search.

    Args:
        query_text: User's query
        openai_client: OpenAI async client
        qdrant_client: Qdrant client
        db_pool: PostgreSQL connection pool
        top_k: Number of top results to return

    Returns:
        List of retrieved chunks with metadata and scores
    """
    logger.info(f"Retrieving full book context for query: {query_text[:100]}...")

    # Generate query embedding
    response = await openai_client.embeddings.create(
        model=settings.openai_embedding_model, input=[query_text]
    )
    query_embedding = response.data[0].embedding

    # Search in Qdrant (no filters for full book search)
    search_results: list[ScoredPoint] = qdrant_client.search(
        collection_name=settings.qdrant_collection_name,
        query_vector=query_embedding,
        limit=top_k,
    )

    logger.info(f"Found {len(search_results)} results from Qdrant")

    # Enrich with PostgreSQL metadata if needed
    results = []
    for scored_point in search_results:
        payload = scored_point.payload
        results.append(
            {
                "chunk_id": UUID(payload["chunk_id"]),
                "text_content": payload["text_content"],
                "similarity_score": scored_point.score,
                "chapter_title": payload.get("chapter_title"),
                "section_title": payload.get("section_title"),
                "page_number": payload.get("page_number"),
                "start_char_offset": payload["start_char_offset"],
                "end_char_offset": payload["end_char_offset"],
            }
        )

    logger.info(f"Retrieved {len(results)} chunks for query")
    return results


async def retrieve_selected_text(
    query_text: str,
    start_char_offset: int,
    end_char_offset: int,
    openai_client: AsyncOpenAI,
    qdrant_client: QdrantClient,
    db_pool: AsyncConnectionPool,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve relevant chunks only from selected text using filtered vector search.

    Args:
        query_text: User's query
        start_char_offset: Start of selected text range
        end_char_offset: End of selected text range
        openai_client: OpenAI async client
        qdrant_client: Qdrant client
        db_pool: PostgreSQL connection pool
        top_k: Number of top results to return

    Returns:
        List of retrieved chunks with metadata and scores
    """
    logger.info(
        f"Retrieving selected text context for query: {query_text[:100]}... (offsets: {start_char_offset}-{end_char_offset})"
    )

    # Generate query embedding
    response = await openai_client.embeddings.create(
        model=settings.openai_embedding_model, input=[query_text]
    )
    query_embedding = response.data[0].embedding

    # Create filter for selected text range
    # Chunks overlap with selection if:
    # chunk.start < selection.end AND chunk.end > selection.start
    filter_condition = Filter(
        must=[
            {"key": "start_char_offset", "range": {"lt": end_char_offset}},
            {"key": "end_char_offset", "range": {"gt": start_char_offset}},
        ]
    )

    # Search in Qdrant with filter
    search_results: list[ScoredPoint] = qdrant_client.search(
        collection_name=settings.qdrant_collection_name,
        query_vector=query_embedding,
        query_filter=filter_condition,
        limit=top_k,
    )

    logger.info(f"Found {len(search_results)} results from Qdrant (filtered)")

    # Enrich with metadata
    results = []
    for scored_point in search_results:
        payload = scored_point.payload
        results.append(
            {
                "chunk_id": UUID(payload["chunk_id"]),
                "text_content": payload["text_content"],
                "similarity_score": scored_point.score,
                "chapter_title": payload.get("chapter_title"),
                "section_title": payload.get("section_title"),
                "page_number": payload.get("page_number"),
                "start_char_offset": payload["start_char_offset"],
                "end_char_offset": payload["end_char_offset"],
            }
        )

    logger.info(f"Retrieved {len(results)} chunks from selected text")
    return results


async def store_retrieval_audit(
    query_id: UUID,
    retrieved_chunks: list[dict[str, Any]],
    db_pool: AsyncConnectionPool,
) -> None:
    """Store retrieval audit trail in PostgreSQL.

    Args:
        query_id: Query identifier
        retrieved_chunks: List of retrieved chunks with scores
        db_pool: PostgreSQL connection pool
    """
    logger.debug(f"Storing retrieval audit for query {query_id}")

    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            for rank, chunk in enumerate(retrieved_chunks, start=1):
                await cur.execute(
                    """
                    INSERT INTO retrieved_passages (
                        query_id, chunk_id, similarity_score, rank
                    ) VALUES (%s, %s, %s, %s)
                    """,
                    (query_id, chunk["chunk_id"], chunk["similarity_score"], rank),
                )
            await conn.commit()

    logger.debug(f"Stored {len(retrieved_chunks)} retrieval records")
