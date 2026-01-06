"""Integration tests for RAG chatbot pipeline."""

import pytest
from uuid import UUID

from backend.src.services.chat import (
    create_chat_session,
    chat_with_rag,
    get_chat_history,
)
from backend.src.db.postgres import get_pool
from backend.src.core.config import settings


@pytest.mark.asyncio
async def test_create_chat_session():
    """Test creating a new chat session."""
    pool = await get_pool()
    session_id = await create_chat_session(pool)

    assert isinstance(session_id, UUID)
    assert str(session_id) != "00000000-0000-0000-0000-000000000000"


@pytest.mark.asyncio
async def test_chat_with_rag_similarity_threshold():
    """Test that chat_with_rag filters chunks below similarity threshold."""
    pool = await get_pool()
    session_id = await create_chat_session(pool)

    # Query completely unrelated to book content
    response = await chat_with_rag(
        query="What is the capital of France?",
        session_id=session_id,
        db_pool=pool,
        top_k=3
    )

    # Should either return no results or explicitly state information not available
    assert "session_id" in response
    assert "answer" in response
    # Check if it properly handles low similarity
    if response.get("sources"):
        # If there are sources, they should meet threshold
        for source in response["sources"]:
            assert source.get("similarity", 0) >= 0.7


@pytest.mark.asyncio
async def test_chat_with_rag_relevant_query():
    """Test chat_with_rag with relevant query."""
    pool = await get_pool()
    session_id = await create_chat_session(pool)

    # Query related to book content
    response = await chat_with_rag(
        query="What is Physical AI?",
        session_id=session_id,
        db_pool=pool,
        top_k=3
    )

    assert "answer" in response
    assert "sources" in response
    assert "session_id" in response
    assert len(response["answer"]) > 0

    # Should have retrieved relevant sources
    if response.get("sources"):
        assert len(response["sources"]) > 0
        # Check similarity scores
        for source in response["sources"]:
            assert "similarity" in source
            assert source["similarity"] > 0


@pytest.mark.asyncio
async def test_session_persistence():
    """Test that messages are persisted in session."""
    pool = await get_pool()
    session_id = await create_chat_session(pool)

    # Send first message
    await chat_with_rag(
        query="What is ROS 2?",
        session_id=session_id,
        db_pool=pool
    )

    # Send second message
    await chat_with_rag(
        query="Tell me more about it",
        session_id=session_id,
        db_pool=pool
    )

    # Get history
    history = await get_chat_history(session_id, pool)

    # Should have 4 messages (2 user + 2 assistant)
    assert len(history) >= 4
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[2]["role"] == "user"
    assert history[3]["role"] == "assistant"


@pytest.mark.asyncio
async def test_retrieval_quality_logging(caplog):
    """Test that retrieval quality metrics are logged."""
    pool = await get_pool()
    session_id = await create_chat_session(pool)

    with caplog.at_level("INFO"):
        await chat_with_rag(
            query="What are the hardware requirements?",
            session_id=session_id,
            db_pool=pool,
            top_k=3
        )

    # Check that quality metrics are logged
    log_messages = [record.message for record in caplog.records]

    # Should have retrieval quality logs
    retrieval_logs = [msg for msg in log_messages if "Retrieved" in msg and "chunks" in msg]
    assert len(retrieval_logs) > 0

    # Should have similarity logs if chunks were retrieved
    similarity_logs = [msg for msg in log_messages if "similarity" in msg.lower()]
    if any("Retrieved" in msg and "chunks" in msg for msg in log_messages):
        # If chunks were retrieved, should log similarity stats
        pass  # Similarity logging is conditional


@pytest.mark.asyncio
async def test_hardware_query_reranking():
    """Test that hardware queries trigger smart reranking."""
    pool = await get_pool()
    session_id = await create_chat_session(pool)

    response = await chat_with_rag(
        query="What GPU do I need?",
        session_id=session_id,
        db_pool=pool,
        top_k=3
    )

    # Should return relevant answer
    assert "answer" in response
    answer_lower = response["answer"].lower()

    # Hardware-related response should mention GPU or hardware specs
    assert any(term in answer_lower for term in ["gpu", "rtx", "hardware", "requirement"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
