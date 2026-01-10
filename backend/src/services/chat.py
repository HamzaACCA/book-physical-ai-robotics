"""Chat service with RAG integration and session management."""

import json
import re
from typing import Optional
from uuid import UUID, uuid4

from openai import OpenAI
from psycopg_pool import AsyncConnectionPool

from backend.src.core.config import settings
from backend.src.core.logging import get_logger
from backend.src.db.qdrant import get_qdrant_client

logger = get_logger(__name__)

# Configure OpenAI
openai_client = OpenAI(api_key=settings.openai_api_key)


def generate_embeddings_openai(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using OpenAI.

    Args:
        texts: List of texts to embed

    Returns:
        List of embedding vectors
    """
    response = openai_client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts
    )
    return [item.embedding for item in response.data]


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


def extract_topics_from_chunks(chunks: list[dict]) -> list[str]:
    """Extract key topics from retrieved chunks.

    Args:
        chunks: List of retrieved chunk dictionaries

    Returns:
        List of topic keywords
    """
    topics = set()
    for chunk in chunks:
        # Extract capitalized words as potential topics
        words = chunk.get('text', '').split()
        for word in words:
            clean_word = word.strip('.,!?;:')
            if len(clean_word) > 3 and (clean_word[0].isupper() or clean_word.isupper()):
                topics.add(clean_word)

    # Return top 10 topics
    return list(topics)[:10]


def generate_follow_up_questions(
    query: str,
    retrieved_chunks: list[dict],
    answer: str
) -> list[str]:
    """Generate 3 follow-up questions using Gemini.

    Args:
        query: Original user question
        retrieved_chunks: Retrieved context chunks
        answer: Generated answer

    Returns:
        List of up to 3 follow-up question strings
    """
    try:
        # Extract topics from chunks
        topics = extract_topics_from_chunks(retrieved_chunks)

        prompt = f"""Based on this Q&A about a book on Physical AI & Humanoid Robotics, suggest 3 relevant follow-up questions the reader might ask next.

USER QUESTION: {query}
ANSWER GIVEN: {answer[:200]}...
TOPICS IN CONTEXT: {', '.join(topics) if topics else 'general robotics content'}

Generate 3 concise follow-up questions (one per line) that:
- Explore related concepts from the context
- Dive deeper into mentioned topics
- Help the reader learn more

FOLLOW-UP QUESTIONS:"""

        response = openai_client.chat.completions.create(
            model=settings.openai_llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.openai_temperature,
            max_tokens=200
        )

        # Parse response into list (one question per line)
        questions = [q.strip() for q in response.choices[0].message.content.split('\n') if q.strip() and '?' in q]
        return questions[:3]  # Max 3

    except Exception as e:
        logger.warning(f"Failed to generate follow-up questions: {e}")
        return []


def suggest_query_refinements(
    query: str,
    retrieved_chunks: list[dict],
    avg_similarity: float
) -> list[str]:
    """Suggest refined queries when similarity is low (<0.65).

    Args:
        query: Original user question
        retrieved_chunks: Retrieved context chunks
        avg_similarity: Average similarity score

    Returns:
        List of suggested refined queries (max 3)
    """
    if avg_similarity >= 0.65 or not retrieved_chunks:
        return []  # Good results or no chunks, no need for suggestions

    try:
        # Extract keywords from chunks
        keywords = extract_topics_from_chunks(retrieved_chunks)

        prompt = f"""The user asked: "{query}"

But the search found limited relevant content (similarity: {avg_similarity:.2f}).

These topics are available in the book: {', '.join(keywords) if keywords else 'various robotics topics'}

Suggest 3 alternative phrasings or related questions that might get better results from the book content.

SUGGESTED QUERIES:"""

        response = openai_client.chat.completions.create(
            model=settings.openai_llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.openai_temperature,
            max_tokens=150
        )

        suggestions = [s.strip() for s in response.choices[0].message.content.split('\n') if s.strip() and len(s.strip()) > 10]
        return suggestions[:3]

    except Exception as e:
        logger.warning(f"Failed to generate query suggestions: {e}")
        return []


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
            query_embedding = generate_embeddings_openai([query])[0]

            # Search Qdrant for similar chunks
            qdrant_client = get_qdrant_client()
            search_results = qdrant_client.query_points(
                collection_name=settings.qdrant_collection_name,
                query=query_embedding,
                limit=top_k
            ).points

            # Step 4: Retrieve chunk details from PostgreSQL with similarity threshold
            # OpenAI text-embedding-3-small has lower similarity scores than Gemini
            # Using 0.25 threshold for technical queries (ROS 2, hardware, etc.)
            # Higher scores (0.5+) for general topics, lower (0.27-0.33) for specific technical terms
            SIMILARITY_THRESHOLD = 0.25
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
                            """SELECT
                                text_content,
                                chapter_title,
                                section_title,
                                chunk_id
                            FROM book_chunks
                            WHERE chunk_id = %s""",
                            (chunk_id,)
                        )
                        row = await cur.fetchone()

                        if row:
                            retrieved_chunks.append({
                                "chunk_id": str(chunk_id),
                                "text": row[0],
                                "chapter_title": row[1],
                                "section_title": row[2],
                                "similarity": similarity
                            })

            # Log retrieval quality metrics
            logger.info(f"Retrieved {len(retrieved_chunks)} chunks (filtered {filtered_count} below threshold {SIMILARITY_THRESHOLD})")
            suggestions = []
            avg_similarity = 0.0
            if retrieved_chunks:
                avg_similarity = sum(c['similarity'] for c in retrieved_chunks) / len(retrieved_chunks)
                logger.info(f"Average similarity: {avg_similarity:.3f}, Top similarity: {retrieved_chunks[0]['similarity']:.3f}")

                # Generate query suggestions if similarity is low
                if avg_similarity < 0.65:
                    suggestions = suggest_query_refinements(query, retrieved_chunks, avg_similarity)
                    if suggestions:
                        logger.info(f"Generated {len(suggestions)} query suggestions due to low similarity")
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
- ONLY use information from the CONTEXT above. Do NOT make up or invent any names, titles, or details.
- If listing modules, chapters, or items, use the EXACT names from the context - do not paraphrase or create new names.
- DO NOT start with "Based on the book content:" or similar phrases
- Write in a well-structured format with proper paragraphs
- For lists (like modules, steps, components): put each item on its own line with **bold heading** followed by description in normal text
  Example format:
  **Item Name**
  Description here.

  **Next Item Name**
  Description here.
- If the context doesn't have enough information, say so clearly
- Keep answers concise but well-formatted

ANSWER:"""

        # Step 8: Generate response with OpenAI
        try:
            response = openai_client.chat.completions.create(
                model=settings.openai_llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.openai_temperature,
                max_tokens=800
            )
            answer = response.choices[0].message.content

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

            # Generate follow-up questions
            follow_ups = generate_follow_up_questions(query, retrieved_chunks, answer)
            if follow_ups:
                logger.info(f"Generated {len(follow_ups)} follow-up questions")

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
                formatted_answer = "The hardware requirements for this course include:\n\n"

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
                    formatted_answer += "\nThese specifications are important because high VRAM is needed for robot and environment assets, and RTX GPU enables realistic rendering.\n"

                answer = formatted_answer
            else:
                # Limit to reasonable length for non-hardware queries
                # Format with proper paragraphs
                combined_text = combined_text[:800].rsplit(' ', 1)[0]
                # Remove line breaks and clean up
                combined_text = ' '.join(combined_text.split())
                answer = combined_text

            answer += "\n\n[Note: AI response generation temporarily limited. Full conversational responses will be available when API quota resets.]"

            # Generate follow-ups for fallback case too
            follow_ups = []  # No follow-ups in fallback mode

        # Step 9: Save assistant response
        await save_message(session_id, "assistant", answer, db_pool)

        # Step 10: Return response (clean format - just answer and session)
        return {
            "answer": answer,
            "sources": [],
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
