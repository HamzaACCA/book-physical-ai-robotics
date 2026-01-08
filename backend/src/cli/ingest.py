"""CLI tool for ingesting books into the RAG system."""

import argparse
import asyncio
from pathlib import Path
from uuid import UUID, uuid4

from openai import AsyncOpenAI

from backend.src.core.config import settings
from backend.src.core.logging import get_logger, setup_logging
from backend.src.db.postgres import get_pool
from backend.src.db.qdrant import get_qdrant_client
from backend.src.services.ingestion import (
    chunk_book_content,
    generate_embeddings,
    store_chunks_postgres,
    store_embeddings_qdrant,
)

logger = get_logger(__name__)


async def ingest_book(
    file_path: str,
    book_id: UUID,
    book_title: str,
    chunk_size: int = 800,
    overlap: int = 128,
) -> None:
    """Ingest a book into the RAG system with metadata extraction.

    Supports plain text and markdown files. Markdown headers (# H1, ## H2) are
    automatically extracted to provide chapter and section metadata for enhanced
    source attribution in chat responses.

    Args:
        file_path: Path to book file (txt or md). Markdown headers recommended.
        book_id: Unique identifier for the book
        book_title: Title of the book
        chunk_size: Target chunk size in tokens
        overlap: Overlap between chunks in tokens

    Markdown Structure:
        - H1 headers (#) → Chapters (e.g., "# Chapter 1: Introduction")
        - H2 headers (##) → Sections (e.g., "## Background")
        - Files without headers are treated as single-chapter content
    """
    logger.info(f"Starting ingestion for book: {book_title} (ID: {book_id})")

    # Read book content
    book_path = Path(file_path)
    if not book_path.exists():
        raise FileNotFoundError(f"Book file not found: {file_path}")

    with book_path.open("r", encoding="utf-8") as f:
        book_content = f.read()

    logger.info(f"Read {len(book_content)} characters from {file_path}")

    # Chunk the book
    chunks = chunk_book_content(
        book_content=book_content,
        book_id=book_id,
        target_tokens=chunk_size,
        overlap_tokens=overlap,
    )

    # Generate embeddings
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    chunk_texts = [chunk["text_content"] for chunk in chunks]
    embeddings = await generate_embeddings(chunk_texts, openai_client)

    # Store chunks in PostgreSQL
    db_pool = await get_pool()
    chunk_ids = await store_chunks_postgres(chunks, book_id, db_pool)

    # Store embeddings in Qdrant
    qdrant_client = get_qdrant_client()
    await store_embeddings_qdrant(chunks, chunk_ids, embeddings, book_id, qdrant_client)

    logger.info(
        f"Successfully ingested book {book_title}: {len(chunks)} chunks, {len(embeddings)} embeddings"
    )


def main() -> None:
    """CLI entry point for book ingestion."""
    parser = argparse.ArgumentParser(description="Ingest a book into the RAG system")
    parser.add_argument("file_path", type=str, help="Path to the book text file")
    parser.add_argument(
        "--book-id",
        type=str,
        default=None,
        help="Book ID (UUID). If not provided, a new UUID will be generated",
    )
    parser.add_argument("--book-title", type=str, required=True, help="Title of the book")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="Target chunk size in tokens (default: 800)",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=128,
        help="Overlap between chunks in tokens (default: 128)",
    )

    args = parser.parse_args()

    # Generate or parse book ID
    if args.book_id:
        book_id = UUID(args.book_id)
    else:
        book_id = uuid4()
        logger.info(f"Generated new book ID: {book_id}")

    # Setup logging
    setup_logging()

    # Run ingestion
    try:
        asyncio.run(
            ingest_book(
                file_path=args.file_path,
                book_id=book_id,
                book_title=args.book_title,
                chunk_size=args.chunk_size,
                overlap=args.overlap,
            )
        )
        print(f"✓ Successfully ingested book: {args.book_title}")
        print(f"  Book ID: {book_id}")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        print(f"✗ Ingestion failed: {e}")
        raise


if __name__ == "__main__":
    main()
