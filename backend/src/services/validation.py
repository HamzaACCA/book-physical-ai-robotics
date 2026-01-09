"""Response validation service for hallucination detection."""

import re
from typing import Any

from openai import AsyncOpenAI

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


async def validate_response_grounding(
    response_text: str,
    retrieved_chunks: list[dict[str, Any]],
    openai_client: AsyncOpenAI,
) -> tuple[bool, float, str]:
    """Validate that the response is grounded in retrieved context.

    Uses two validation methods:
    1. Citation check: Ensure response references retrieved chunks
    2. Semantic similarity: Check response embedding similarity to context

    Args:
        response_text: Generated LLM response
        retrieved_chunks: List of retrieved context chunks
        openai_client: OpenAI async client

    Returns:
        Tuple of (validation_passed, retrieval_quality_score, validation_notes)
    """
    logger.debug("Validating response grounding")

    validation_notes = []

    # 1. Citation Check: Response should contain citations like [1], [2], etc.
    citation_pattern = r"\[\d+\]"
    citations = re.findall(citation_pattern, response_text)
    has_citations = len(citations) > 0

    if has_citations:
        validation_notes.append(f"Found {len(citations)} citations")
    else:
        validation_notes.append("No citations found - potential hallucination risk")

    # 2. Out-of-scope detection: Check for phrases indicating no information
    out_of_scope_phrases = [
        "information is not available",
        "not found in the book",
        "cannot answer based on",
        "no information about",
        "not mentioned in",
    ]
    is_out_of_scope = any(
        phrase.lower() in response_text.lower() for phrase in out_of_scope_phrases
    )

    if is_out_of_scope:
        validation_notes.append("Out-of-scope query detected")
        # Out-of-scope responses are valid (they correctly indicate no info)
        return True, 0.0, " | ".join(validation_notes)

    # 3. Semantic Similarity Check
    # Combine all retrieved chunks
    combined_context = " ".join([chunk["text_content"] for chunk in retrieved_chunks])

    # Generate embeddings
    response_embed = await openai_client.embeddings.create(
        model=settings.openai_embedding_model, input=[response_text]
    )
    context_embed = await openai_client.embeddings.create(
        model=settings.openai_embedding_model, input=[combined_context[:8000]]  # Limit context length
    )

    response_vec = response_embed.data[0].embedding
    context_vec = context_embed.data[0].embedding

    # Cosine similarity
    similarity = _cosine_similarity(response_vec, context_vec)
    validation_notes.append(f"Semantic similarity: {similarity:.3f}")

    # 4. Combined validation
    # Pass if: has citations AND similarity > 0.7
    retrieval_quality = max(
        chunk["similarity_score"] for chunk in retrieved_chunks
    ) if retrieved_chunks else 0.0

    validation_passed = has_citations and similarity > 0.7

    if not validation_passed:
        if not has_citations:
            validation_notes.append("FAIL: Missing citations")
        if similarity <= 0.7:
            validation_notes.append(f"FAIL: Low semantic similarity ({similarity:.3f} <= 0.7)")

    logger.debug(
        f"Validation result: {validation_passed}, quality: {retrieval_quality:.3f}"
    )
    return validation_passed, retrieval_quality, " | ".join(validation_notes)


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (0-1)
    """
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


async def handle_out_of_scope_query(
    retrieved_chunks: list[dict[str, Any]],
) -> tuple[bool, str]:
    """Detect if a query is out of scope based on retrieval quality.

    Args:
        retrieved_chunks: List of retrieved context chunks

    Returns:
        Tuple of (is_out_of_scope, suggested_response)
    """
    if not retrieved_chunks:
        return True, "I couldn't find any relevant information in the book to answer your question."

    # Check if best match is below threshold
    best_score = max(chunk["similarity_score"] for chunk in retrieved_chunks)

    if best_score < settings.rag_retrieval_threshold:
        logger.info(f"Out-of-scope query detected (best score: {best_score:.3f})")
        return (
            True,
            f"I couldn't find information directly related to your question in the book. The most relevant content I found has low relevance (score: {best_score:.2f}).",
        )

    return False, ""
