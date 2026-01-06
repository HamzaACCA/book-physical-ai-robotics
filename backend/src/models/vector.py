"""Qdrant payload schemas for vector storage metadata."""

from typing import Optional, TypedDict
from uuid import UUID


class ChunkPayload(TypedDict, total=False):
    """Payload schema for book chunk vectors in Qdrant.

    This payload is stored alongside each vector embedding in Qdrant
    and is used for metadata filtering during retrieval.
    """

    chunk_id: str  # UUID as string
    book_id: str  # UUID as string
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


def create_chunk_payload(
    chunk_id: UUID,
    book_id: UUID,
    text_content: str,
    token_count: int,
    start_char_offset: int,
    end_char_offset: int,
    chapter_id: Optional[str] = None,
    chapter_title: Optional[str] = None,
    section_id: Optional[str] = None,
    section_title: Optional[str] = None,
    page_number: Optional[int] = None,
    heading_hierarchy: Optional[list[str]] = None,
) -> ChunkPayload:
    """Create a Qdrant payload for a book chunk.

    Args:
        chunk_id: Unique chunk identifier
        book_id: Book identifier
        text_content: The chunk text content
        token_count: Number of tokens in chunk
        start_char_offset: Start position in original book
        end_char_offset: End position in original book
        chapter_id: Optional chapter identifier
        chapter_title: Optional chapter title
        section_id: Optional section identifier
        section_title: Optional section title
        page_number: Optional page number
        heading_hierarchy: Optional list of heading levels

    Returns:
        ChunkPayload ready for Qdrant storage
    """
    payload: ChunkPayload = {
        "chunk_id": str(chunk_id),
        "book_id": str(book_id),
        "text_content": text_content,
        "token_count": token_count,
        "start_char_offset": start_char_offset,
        "end_char_offset": end_char_offset,
    }

    if chapter_id is not None:
        payload["chapter_id"] = chapter_id
    if chapter_title is not None:
        payload["chapter_title"] = chapter_title
    if section_id is not None:
        payload["section_id"] = section_id
    if section_title is not None:
        payload["section_title"] = section_title
    if page_number is not None:
        payload["page_number"] = page_number
    if heading_hierarchy is not None:
        payload["heading_hierarchy"] = heading_hierarchy

    return payload
