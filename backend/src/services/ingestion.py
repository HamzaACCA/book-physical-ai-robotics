"""Book ingestion service for chunking, embedding, and storage."""

import re
from typing import Any
from uuid import UUID

import google.generativeai as genai
from openai import AsyncOpenAI
from psycopg_pool import AsyncConnectionPool
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from backend.src.core.config import settings
from backend.src.core.logging import get_logger
from backend.src.models.vector import create_chunk_payload

logger = get_logger(__name__)

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


def extract_markdown_structure(content: str) -> dict[str, Any]:
    """Parse markdown headers to extract document structure.

    Args:
        content: Full markdown content

    Returns:
        Dictionary with chapters and sections hierarchy:
        {
            'chapters': [
                {
                    'id': 'chapter-01',
                    'title': 'Introduction',
                    'start_offset': 0,
                    'end_offset': 1500,
                    'level': 1,  # H1
                    'sections': [
                        {
                            'id': 'section-01-01',
                            'title': 'Background',
                            'start_offset': 150,
                            'end_offset': 800,
                            'level': 2  # H2
                        }
                    ]
                }
            ]
        }
    """
    logger.info("Extracting markdown structure")

    # Regex to match markdown headers: # Title, ## Title, etc.
    header_pattern = re.compile(r'^(#+)\s+(.+)$', re.MULTILINE)

    chapters = []
    current_chapter = None
    chapter_counter = 0
    section_counter = 0

    # Find all headers with their positions
    for match in header_pattern.finditer(content):
        level = len(match.group(1))  # Number of # symbols
        title = match.group(2).strip()
        start_offset = match.start()

        if level == 1:  # H1 = Chapter
            # Close previous chapter
            if current_chapter:
                current_chapter['end_offset'] = start_offset
                chapters.append(current_chapter)

            # Start new chapter
            chapter_counter += 1
            section_counter = 0  # Reset section counter for new chapter
            current_chapter = {
                'id': f'chapter-{chapter_counter:02d}',
                'title': title,
                'start_offset': start_offset,
                'end_offset': len(content),  # Will be updated
                'level': 1,
                'sections': []
            }

        elif level == 2 and current_chapter:  # H2 = Section (only if in a chapter)
            # Close previous section if exists
            if current_chapter['sections']:
                current_chapter['sections'][-1]['end_offset'] = start_offset

            # Add new section
            section_counter += 1
            current_chapter['sections'].append({
                'id': f'section-{chapter_counter:02d}-{section_counter:02d}',
                'title': title,
                'start_offset': start_offset,
                'end_offset': current_chapter['end_offset'],  # Will be updated
                'level': 2
            })

    # Close final chapter
    if current_chapter:
        current_chapter['end_offset'] = len(content)
        chapters.append(current_chapter)

    # If no chapters found, create a default one
    if not chapters:
        logger.info("No markdown headers found, treating as single chapter")
        chapters = [{
            'id': 'chapter-01',
            'title': 'Content',
            'start_offset': 0,
            'end_offset': len(content),
            'level': 1,
            'sections': []
        }]

    logger.info(f"Extracted {len(chapters)} chapters with {sum(len(ch['sections']) for ch in chapters)} sections")
    return {'chapters': chapters}


def find_chunk_metadata(
    start_offset: int,
    end_offset: int,
    structure: dict[str, Any]
) -> dict[str, Any]:
    """Find which chapter/section a chunk belongs to based on char offsets.

    Args:
        start_offset: Chunk start character position
        end_offset: Chunk end character position
        structure: Document structure from extract_markdown_structure()

    Returns:
        Dictionary with chapter_id, chapter_title, section_id, section_title, hierarchy
    """
    metadata = {
        'chapter_id': None,
        'chapter_title': None,
        'section_id': None,
        'section_title': None,
        'hierarchy': []
    }

    # Use chunk's midpoint for classification
    chunk_midpoint = (start_offset + end_offset) // 2

    # Find which chapter contains this chunk
    for chapter in structure.get('chapters', []):
        if chapter['start_offset'] <= chunk_midpoint < chapter['end_offset']:
            metadata['chapter_id'] = chapter['id']
            metadata['chapter_title'] = chapter['title']
            metadata['hierarchy'] = [chapter['title']]

            # Find which section within this chapter
            for section in chapter.get('sections', []):
                if section['start_offset'] <= chunk_midpoint < section['end_offset']:
                    metadata['section_id'] = section['id']
                    metadata['section_title'] = section['title']
                    metadata['hierarchy'].append(section['title'])
                    break

            break

    return metadata


def chunk_book_content(
    book_content: str,
    book_id: UUID,
    target_tokens: int = 800,
    overlap_tokens: int = 128,
) -> list[dict[str, Any]]:
    """Chunk book content preserving paragraph boundaries with metadata extraction.

    Args:
        book_content: Full text of the book (supports plain text and markdown)
        book_id: Unique identifier for the book
        target_tokens: Target chunk size in tokens (default 800)
        overlap_tokens: Overlap between chunks in tokens (default 128)

    Returns:
        List of chunk dictionaries with text, offsets, and chapter/section metadata
    """
    logger.info(f"Starting chunking for book {book_id}")

    # Extract markdown structure for metadata
    structure = extract_markdown_structure(book_content)

    # Simple word-based approximation: ~0.75 tokens per word
    words_per_token = 0.75
    target_words = int(target_tokens * words_per_token)
    overlap_words = int(overlap_tokens * words_per_token)

    # Split by paragraph boundaries (double newline or more)
    paragraphs = re.split(r"\n\s*\n", book_content)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_chunk_words = []
    current_chunk_start = 0
    current_word_count = 0

    for para in paragraphs:
        words = para.split()
        word_count = len(words)

        # If adding this paragraph would exceed target, finalize current chunk
        if current_word_count + word_count > target_words and current_chunk_words:
            # Finalize current chunk
            chunk_text = " ".join(current_chunk_words)
            chunk_end = current_chunk_start + len(chunk_text)

            chunks.append(
                {
                    "text_content": chunk_text,
                    "token_count": int(current_word_count / words_per_token),
                    "start_char_offset": current_chunk_start,
                    "end_char_offset": chunk_end,
                }
            )

            # Start new chunk with overlap
            overlap_chunk = current_chunk_words[-overlap_words:]
            current_chunk_words = overlap_chunk + words
            current_word_count = len(current_chunk_words)
            # Adjust start offset to account for overlap
            current_chunk_start = chunk_end - len(" ".join(overlap_chunk))
        else:
            # Add paragraph to current chunk
            current_chunk_words.extend(words)
            current_word_count += word_count

    # Finalize last chunk
    if current_chunk_words:
        chunk_text = " ".join(current_chunk_words)
        chunk_end = current_chunk_start + len(chunk_text)
        chunks.append(
            {
                "text_content": chunk_text,
                "token_count": int(current_word_count / words_per_token),
                "start_char_offset": current_chunk_start,
                "end_char_offset": chunk_end,
            }
        )

    # Add chapter/section metadata to each chunk
    for chunk in chunks:
        metadata = find_chunk_metadata(
            chunk["start_char_offset"],
            chunk["end_char_offset"],
            structure
        )
        chunk.update(metadata)

    logger.info(f"Created {len(chunks)} chunks with metadata for book {book_id}")
    return chunks


def generate_embeddings_gemini(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using Google Gemini text-embedding-004.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (768 dimensions each)
    """
    logger.info(f"Generating embeddings for {len(texts)} texts using Gemini")

    embeddings = []
    for text in texts:
        result = genai.embed_content(
            model=settings.gemini_embedding_model,
            content=text,
            task_type="retrieval_document"
        )
        embeddings.append(result['embedding'])

    logger.info(f"Generated {len(embeddings)} embeddings")
    return embeddings


async def generate_embeddings(
    texts: list[str], openai_client: AsyncOpenAI = None
) -> list[list[float]]:
    """Generate embeddings using Google Gemini (wrapper for compatibility).

    Args:
        texts: List of text strings to embed
        openai_client: Unused, kept for compatibility

    Returns:
        List of embedding vectors (768 dimensions each)
    """
    return generate_embeddings_gemini(texts)


async def store_chunks_postgres(
    chunks: list[dict[str, Any]],
    book_id: UUID,
    db_pool: AsyncConnectionPool,
) -> list[UUID]:
    """Store chunk metadata in PostgreSQL.

    Args:
        chunks: List of chunk dictionaries with metadata
        book_id: Book identifier
        db_pool: PostgreSQL connection pool

    Returns:
        List of generated chunk IDs
    """
    logger.info(f"Storing {len(chunks)} chunks to PostgreSQL for book {book_id}")

    chunk_ids = []

    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            for chunk in chunks:
                await cur.execute(
                    """
                    INSERT INTO book_chunks (
                        book_id, text_content, token_count,
                        start_char_offset, end_char_offset,
                        chapter_id, chapter_title, section_id, section_title,
                        page_number, heading_hierarchy
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING chunk_id
                    """,
                    (
                        book_id,
                        chunk["text_content"],
                        chunk["token_count"],
                        chunk["start_char_offset"],
                        chunk["end_char_offset"],
                        chunk.get("chapter_id"),
                        chunk.get("chapter_title"),
                        chunk.get("section_id"),
                        chunk.get("section_title"),
                        chunk.get("page_number"),
                        chunk.get("heading_hierarchy"),
                    ),
                )
                result = await cur.fetchone()
                if result:
                    chunk_ids.append(result[0])

            await conn.commit()

    logger.info(f"Stored {len(chunk_ids)} chunks to PostgreSQL")
    return chunk_ids


async def store_embeddings_qdrant(
    chunks: list[dict[str, Any]],
    chunk_ids: list[UUID],
    embeddings: list[list[float]],
    book_id: UUID,
    qdrant_client: QdrantClient,
) -> None:
    """Store embeddings and payloads in Qdrant.

    Args:
        chunks: List of chunk dictionaries with metadata
        chunk_ids: List of PostgreSQL chunk IDs
        embeddings: List of embedding vectors
        book_id: Book identifier
        qdrant_client: Qdrant client instance
    """
    logger.info(f"Storing {len(embeddings)} embeddings to Qdrant for book {book_id}")

    points = []
    for chunk, chunk_id, embedding in zip(chunks, chunk_ids, embeddings):
        payload = create_chunk_payload(
            chunk_id=chunk_id,
            book_id=book_id,
            text_content=chunk["text_content"],
            token_count=chunk["token_count"],
            start_char_offset=chunk["start_char_offset"],
            end_char_offset=chunk["end_char_offset"],
            chapter_id=chunk.get("chapter_id"),
            chapter_title=chunk.get("chapter_title"),
            section_id=chunk.get("section_id"),
            section_title=chunk.get("section_title"),
            page_number=chunk.get("page_number"),
            heading_hierarchy=chunk.get("heading_hierarchy"),
        )

        points.append(
            PointStruct(id=str(chunk_id), vector=embedding, payload=payload)
        )

    qdrant_client.upsert(
        collection_name=settings.qdrant_collection_name,
        points=points,
    )

    logger.info(f"Stored {len(points)} points to Qdrant")
