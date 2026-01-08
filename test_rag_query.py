"""Test RAG query system."""
import asyncio

import google.generativeai as genai

from backend.src.core.config import settings
from backend.src.db.postgres import get_pool
from backend.src.db.qdrant import get_qdrant_client
from backend.src.services.ingestion import generate_embeddings_gemini

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


async def query_rag(query: str, top_k: int = 3):
    """Query the RAG system and generate response.

    Args:
        query: User question
        top_k: Number of chunks to retrieve
    """
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}\n")

    # Step 1: Generate query embedding
    print("📊 Step 1: Generating query embedding...")
    query_embedding = generate_embeddings_gemini([query])[0]
    print(f"   ✓ Generated {len(query_embedding)}-dimensional embedding")

    # Step 2: Search Qdrant for similar chunks
    print("\n🔍 Step 2: Searching for similar chunks in Qdrant...")
    qdrant_client = get_qdrant_client()
    from qdrant_client.models import SearchRequest
    search_results = qdrant_client.query_points(
        collection_name=settings.qdrant_collection_name,
        query=query_embedding,
        limit=top_k
    ).points
    print(f"   ✓ Found {len(search_results)} relevant chunks")

    # Step 3: Retrieve chunk details from PostgreSQL
    print("\n📚 Step 3: Retrieving chunk details from PostgreSQL...")
    pool = await get_pool()
    retrieved_chunks = []

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            for idx, result in enumerate(search_results, 1):
                chunk_id = result.id
                similarity = result.score

                await cur.execute(
                    "SELECT text_content FROM book_chunks WHERE chunk_id = %s",
                    (chunk_id,)
                )
                row = await cur.fetchone()

                if row:
                    text = row[0]
                    retrieved_chunks.append({
                        "rank": idx,
                        "similarity": similarity,
                        "text": text
                    })
                    print(f"\n   Chunk #{idx} (similarity: {similarity:.3f})")
                    print(f"   Preview: {text[:150]}...")

    # Step 4: Build context for LLM
    print("\n🤖 Step 4: Building context for LLM...")
    context = "\n\n---\n\n".join([
        f"[Chunk {c['rank']}]\n{c['text']}"
        for c in retrieved_chunks
    ])

    prompt = f"""You are a helpful AI assistant answering questions about a book on Physical AI & Humanoid Robotics.

Use the following context from the book to answer the user's question. If the context doesn't contain enough information, say so.

CONTEXT:
{context}

USER QUESTION: {query}

ANSWER (be concise and cite specific information from the context):"""

    # Step 5: Generate response with Gemini
    print("\n💬 Step 5: Generating response with Gemini...")
    print(f"   Using model: {settings.gemini_llm_model}")
    model = genai.GenerativeModel(settings.gemini_llm_model)
    response = model.generate_content(prompt)

    print(f"\n{'='*60}")
    print("RESPONSE:")
    print(f"{'='*60}")
    print(response.text)
    print(f"{'='*60}\n")

    # Summary
    print("\n📊 SUMMARY:")
    print(f"   • Query: {query}")
    print(f"   • Chunks retrieved: {len(retrieved_chunks)}")
    print(f"   • Top similarity: {retrieved_chunks[0]['similarity']:.3f}")
    print(f"   • Response length: {len(response.text)} characters")
    print()


async def main():
    """Run multiple test queries."""

    test_queries = [
        "What is Physical AI?",
        "What tools and frameworks are used in this course?",
        "What are the hardware requirements?",
    ]

    for query in test_queries:
        await query_rag(query)
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
