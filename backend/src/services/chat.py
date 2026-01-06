"""Chat service with RAG integration and session management."""

import json
import re
from typing import Optional
from uuid import UUID, uuid4

import google.generativeai as genai
from psycopg_pool import AsyncConnectionPool

from backend.src.core.config import settings
from backend.src.core.logging import get_logger
from backend.src.db.qdrant import get_qdrant_client
from backend.src.services.ingestion import generate_embeddings_gemini

logger = get_logger(__name__)

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


async def create_chat_session(db_pool: AsyncConnectionPool) -> UUID:
    """Create a new chat session.

    Args:
        db_pool: PostgreSQL connection pool

    Returns:
        Session ID
    """
    logger.info("Creating new chat session")

    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO sessions (messages) VALUES (%s) RETURNING session_id",
                (json.dumps([]),)
            )
            result = await cur.fetchone()
            await conn.commit()

            session_id = result[0]
            logger.info(f"Created session: {session_id}")
            return session_id


async def get_chat_history(
    session_id: UUID,
    db_pool: AsyncConnectionPool
) -> list[dict]:
    """Get chat history for a session.

    Args:
        session_id: Session ID
        db_pool: PostgreSQL connection pool

    Returns:
        List of messages
    """
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT messages FROM sessions WHERE session_id = %s",
                (session_id,)
            )
            result = await cur.fetchone()

            if result:
                messages = result[0]
                # JSONB columns return Python objects directly
                if isinstance(messages, str):
                    return json.loads(messages)
                return messages
            return []


async def save_message(
    session_id: UUID,
    role: str,
    content: str,
    db_pool: AsyncConnectionPool
) -> None:
    """Save a message to session history.

    Args:
        session_id: Session ID
        role: Message role (user/assistant)
        content: Message content
        db_pool: PostgreSQL connection pool
    """
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            # Get current messages
            await cur.execute(
                "SELECT messages FROM sessions WHERE session_id = %s",
                (session_id,)
            )
            result = await cur.fetchone()

            if result:
                messages = result[0]
                # JSONB columns return Python objects directly
                if isinstance(messages, str):
                    messages = json.loads(messages)
            else:
                messages = []

            # Add new message
            messages.append({
                "role": role,
                "content": content
            })

            # Update session
            await cur.execute(
                "UPDATE sessions SET messages = %s WHERE session_id = %s",
                (json.dumps(messages), session_id)
            )
            await conn.commit()


async def chat_with_rag(
    query: str,
    session_id: UUID,
    db_pool: AsyncConnectionPool,
    top_k: int = 3,
    selected_text: str | None = None
) -> dict:
    """Process chat message with RAG and return response.

    Args:
        query: User question
        session_id: Session ID for history
        db_pool: PostgreSQL connection pool
        top_k: Number of chunks to retrieve
        selected_text: User-selected text to restrict context (optional)

    Returns:
        Response dict with answer and sources
    """
    logger.info(f"Processing chat query for session {session_id}: {query}")

    try:
        # Step 1: Save user message
        await save_message(session_id, "user", query, db_pool)

        # Step 2 & 3: Retrieve context - either from selected text or vector search
        if selected_text:
            # Selection-only mode: Use only user-selected text as context
            logger.info(f"Using selection-only mode with {len(selected_text)} characters")
            retrieved_chunks = [{
                "text": selected_text,
                "similarity": 1.0  # Perfect match since user selected it
            }]
        else:
            # Full book retrieval mode: Use vector search
            logger.info("Using full book retrieval mode")

            # Generate query embedding
            query_embedding = generate_embeddings_gemini([query])[0]

            # Search Qdrant for similar chunks
            qdrant_client = get_qdrant_client()
            search_results = qdrant_client.query_points(
                collection_name=settings.qdrant_collection_name,
                query=query_embedding,
                limit=top_k
            ).points

            # Step 4: Retrieve chunk details from PostgreSQL with similarity threshold
            # Adjusted from Constitution's 0.7 to 0.6 for Gemini embeddings
            # (Gemini text-embedding-004 has different similarity distribution than OpenAI)
            SIMILARITY_THRESHOLD = 0.6
            retrieved_chunks = []
            filtered_count = 0

            async with db_pool.connection() as conn:
                async with conn.cursor() as cur:
                    for result in search_results:
                        chunk_id = result.id
                        similarity = result.score

                        # Filter by similarity threshold
                        if similarity < SIMILARITY_THRESHOLD:
                            filtered_count += 1
                            logger.info(f"Filtered chunk with low similarity: {similarity:.3f}")
                            continue

                        await cur.execute(
                            "SELECT text_content FROM book_chunks WHERE chunk_id = %s",
                            (chunk_id,)
                        )
                        row = await cur.fetchone()

                        if row:
                            retrieved_chunks.append({
                                "text": row[0],
                                "similarity": similarity
                            })

            # Log retrieval quality metrics
            logger.info(f"Retrieved {len(retrieved_chunks)} chunks (filtered {filtered_count} below threshold {SIMILARITY_THRESHOLD})")
            if retrieved_chunks:
                avg_similarity = sum(c['similarity'] for c in retrieved_chunks) / len(retrieved_chunks)
                logger.info(f"Average similarity: {avg_similarity:.3f}, Top similarity: {retrieved_chunks[0]['similarity']:.3f}")
            else:
                # No chunks met the similarity threshold
                logger.warning(f"No chunks met similarity threshold {SIMILARITY_THRESHOLD} for query: {query}")
                no_match_msg = "I couldn't find relevant information in the book to answer your question. The content might not cover this topic, or try rephrasing your question."
                await save_message(session_id, "user", query, db_pool)
                await save_message(session_id, "assistant", no_match_msg, db_pool)
                return {
                    "answer": no_match_msg,
                    "sources": [],
                    "session_id": str(session_id)
                }

        # Step 5: Get chat history for context
        history = await get_chat_history(session_id, db_pool)
        conversation_context = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in history[-6:]  # Last 3 exchanges (6 messages)
        ])

        # Step 6: Build context for LLM
        context = "\n\n---\n\n".join([
            f"[Context {i+1}]\n{c['text']}"
            for i, c in enumerate(retrieved_chunks)
        ])

        # Step 7: Build prompt with history
        prompt = f"""You are a helpful AI assistant for a book on Physical AI & Humanoid Robotics.

Use the following context from the book and conversation history to answer the user's question.

CONTEXT FROM BOOK:
{context}

CONVERSATION HISTORY:
{conversation_context}

USER QUESTION: {query}

INSTRUCTIONS:
- Answer based on the context provided
- Reference specific information from the context
- Be conversational and remember previous messages
- If the context doesn't have enough information, say so
- Keep answers concise (2-3 paragraphs max)

ANSWER:"""

        # Step 8: Generate response (skip if quota issues, return context only)
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            answer = response.text

            # Validate response against hallucination
            # Extract key terms from retrieved chunks (nouns, technical terms)
            context_terms = set()
            for chunk in retrieved_chunks:
                # Extract capitalized words (likely proper nouns/technical terms)
                words = chunk['text'].split()
                context_terms.update(word.strip('.,!?;:') for word in words
                                    if len(word) > 3 and (word[0].isupper() or word.isupper()))

            # Check if response contains terms from context
            answer_words = set(word.strip('.,!?;:') for word in answer.split()
                             if len(word) > 3 and (word[0].isupper() or word.isupper()))

            overlap = len(context_terms & answer_words)
            hallucination_score = overlap / max(len(answer_words), 1)

            logger.info(f"Hallucination check: {overlap} terms overlap, score: {hallucination_score:.2f}")

            # If very low overlap, warn that response might not be grounded
            if hallucination_score < 0.1 and len(answer_words) > 5:
                logger.warning(f"Low hallucination score ({hallucination_score:.2f}), response may not be well-grounded in context")
                answer += "\n\n[Note: This response may not be fully based on the book content. Please verify.]"

        except Exception as e:
            logger.warning(f"LLM generation failed: {e}")
            # Fallback: Return formatted context with smart chunk selection

            # Detect query intent for better chunk selection
            query_lower = query.lower()
            hardware_keywords = ['hardware', 'system', 'requirement', 'gpu', 'cpu', 'ram', 'vram', 'rtx', 'memory', 'processor', 'specs']
            is_hardware_query = any(keyword in query_lower for keyword in hardware_keywords)

            # Detect "why" questions (explanatory queries)
            is_why_question = query_lower.startswith('why') or ' why ' in query_lower

            # Rerank chunks based on query intent
            if is_why_question:
                # For "why" questions, prioritize chunks with explanatory content
                scored_chunks = []
                for chunk in retrieved_chunks:
                    chunk_lower = chunk['text'].lower()
                    # Boost chunks with intro/overview keywords
                    explanation_score = 0
                    explanation_keywords = ['why', 'because', 'matters', 'important', 'poised to', 'represents', 'goal:', 'focus:', 'theme:', 'introduction', 'overview']
                    explanation_score = sum(2 for keyword in explanation_keywords if keyword in chunk_lower)

                    # Penalize chunks with technical/setup keywords
                    if any(word in chunk_lower for word in ['aws', 'instance', 'cost calculation', '~$', 'setup']):
                        explanation_score -= 3

                    # Combine explanation score with similarity
                    scored_chunks.append((explanation_score, chunk['similarity'], chunk))
                # Sort by explanation score first, then similarity
                scored_chunks.sort(key=lambda x: (x[0], x[1]), reverse=True)
                selected_chunks = [chunk for score, similarity, chunk in scored_chunks[:2]]

            elif is_hardware_query:
                # Score chunks by hardware keyword presence with similarity as tie-breaker
                scored_chunks = []
                for chunk in retrieved_chunks:
                    chunk_lower = chunk['text'].lower()
                    keyword_score = sum(1 for keyword in ['gpu', 'cpu', 'ram', 'vram', 'rtx', 'intel', 'amd', 'nvidia', 'workstation', 'aws', 'cloud'] if keyword in chunk_lower)
                    # Use tuple (keyword_score, similarity) for sorting - higher is better for both
                    scored_chunks.append((keyword_score, chunk['similarity'], chunk))
                # Sort by keyword score first, then similarity (both descending)
                scored_chunks.sort(key=lambda x: (x[0], x[1]), reverse=True)
                selected_chunks = [chunk for keyword_score, similarity, chunk in scored_chunks[:2]]
            else:
                selected_chunks = retrieved_chunks[:2]

            # Combine selected chunks with better formatting
            combined_text = ""
            for chunk in selected_chunks:
                chunk_text = chunk['text']
                # Remove markdown frontmatter
                chunk_text = re.sub(r'^---.*?---', '', chunk_text, flags=re.DOTALL)
                # Remove markdown formatting symbols
                chunk_text = re.sub(r'[#*_`]', '', chunk_text)
                # Remove Docusaurus admonitions
                chunk_text = re.sub(r':::.*?:::', '', chunk_text, flags=re.DOTALL)
                chunk_text = re.sub(r':::\w+', '', chunk_text)
                # Remove table pipes and format as sentences
                chunk_text = re.sub(r'\|', '', chunk_text)
                # Clean up extra whitespace
                chunk_text = re.sub(r'\s+', ' ', chunk_text).strip()
                combined_text += chunk_text + "\n\n"

            # For hardware queries, try to extract and format key specs
            if is_hardware_query and any(keyword in combined_text.lower() for keyword in ['gpu', 'cpu', 'ram']):
                # Extract key hardware info and format nicely
                formatted_answer = "Here are the hardware requirements:\n\n"

                # Look for GPU info
                gpu_match = re.search(r'(RTX.*?\d+.*?VRAM\))', combined_text, re.IGNORECASE)
                if gpu_match:
                    formatted_answer += f"• GPU: {gpu_match.group(1).strip()}\n"

                # Look for CPU info
                cpu_match = re.search(r'(Intel Core i\d.*?|AMD Ryzen \d+[^|]*)', combined_text, re.IGNORECASE)
                if cpu_match:
                    formatted_answer += f"• CPU: {cpu_match.group(1).strip()}\n"

                # Look for RAM info
                ram_match = re.search(r'(\d+ GB.*?(?:DDR\d+|RAM).*?(?:minimum)?)', combined_text, re.IGNORECASE)
                if ram_match:
                    formatted_answer += f"• RAM: {ram_match.group(1).strip()}\n"

                # Look for OS info
                os_match = re.search(r'(Ubuntu \d+\.\d+.*?LTS)', combined_text, re.IGNORECASE)
                if os_match:
                    formatted_answer += f"• OS: {os_match.group(1).strip()}\n"

                # Add context if found
                if 'high vram' in combined_text.lower():
                    formatted_answer += "\nWhy these specs? High VRAM is needed for robot and environment assets, RTX GPU for realistic rendering.\n"

                answer = formatted_answer
            else:
                # Limit to reasonable length for non-hardware queries
                combined_text = combined_text[:800].rsplit(' ', 1)[0]
                answer = f"Based on the book content:\n\n{combined_text}"

            answer += "\n\n[Note: AI response generation temporarily limited. Full conversational responses will be available when API quota resets.]"

        # Step 9: Save assistant response
        await save_message(session_id, "assistant", answer, db_pool)

        # Step 10: Return response with sources
        return {
            "answer": answer,
            "sources": [
                {
                    "text": c["text"][:200] + "...",
                    "similarity": c["similarity"]
                }
                for c in retrieved_chunks
            ],
            "session_id": str(session_id)
        }

    except Exception as e:
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        error_msg = "Sorry, I encountered an error processing your question. Please try again."
        await save_message(session_id, "assistant", error_msg, db_pool)
        return {
            "answer": error_msg,
            "sources": [],
            "session_id": str(session_id),
            "error": str(e)
        }
