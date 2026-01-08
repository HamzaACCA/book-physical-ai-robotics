"""Simple chatbot health check - no LLM needed."""
import asyncio

from backend.src.core.config import settings
from backend.src.db.postgres import get_pool
from backend.src.db.qdrant import get_qdrant_client
from backend.src.services.ingestion import generate_embeddings_gemini


async def check_chatbot_health():
    """Check if all chatbot components are working."""

    print("\n" + "="*70)
    print("CHATBOT HEALTH CHECK")
    print("="*70 + "\n")

    checks_passed = 0
    total_checks = 5

    # Check 1: PostgreSQL Connection
    print("1️⃣  Checking PostgreSQL connection...")
    try:
        pool = await get_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM book_chunks")
                count = await cur.fetchone()
                print(f"   ✅ Connected! Found {count[0]} book chunks in database")
                checks_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Check 2: Qdrant Connection
    print("\n2️⃣  Checking Qdrant vector database...")
    try:
        client = get_qdrant_client()
        collection_info = client.get_collection(settings.qdrant_collection_name)
        print(f"   ✅ Connected! Collection '{settings.qdrant_collection_name}' has {collection_info.points_count} vectors")
        print(f"   Vector dimension: {collection_info.config.params.vectors.size}")
        checks_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Check 3: Gemini Embeddings
    print("\n3️⃣  Checking Gemini embedding generation...")
    try:
        test_text = "What is robotics?"
        embedding = generate_embeddings_gemini([test_text])[0]
        print(f"   ✅ Working! Generated {len(embedding)}-dimensional embedding")
        checks_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Check 4: Vector Search
    print("\n4️⃣  Checking vector search...")
    try:
        query = "robotics"
        query_embedding = generate_embeddings_gemini([query])[0]
        client = get_qdrant_client()
        results = client.query_points(
            collection_name=settings.qdrant_collection_name,
            query=query_embedding,
            limit=1
        ).points

        if results:
            print(f"   ✅ Working! Found relevant chunks (similarity: {results[0].score:.3f})")
            checks_passed += 1
        else:
            print(f"   ⚠️  No results found")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Check 5: End-to-End Retrieval
    print("\n5️⃣  Checking end-to-end retrieval pipeline...")
    try:
        test_query = "What is Physical AI?"

        # Generate embedding
        query_embedding = generate_embeddings_gemini([test_query])[0]

        # Search Qdrant
        search_results = client.query_points(
            collection_name=settings.qdrant_collection_name,
            query=query_embedding,
            limit=2
        ).points

        # Get from PostgreSQL
        pool = await get_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                chunk_id = search_results[0].id
                await cur.execute(
                    "SELECT text_content FROM book_chunks WHERE chunk_id = %s",
                    (chunk_id,)
                )
                row = await cur.fetchone()

                if row:
                    print(f"   ✅ Working! Retrieved relevant chunk:")
                    print(f"   Similarity: {search_results[0].score:.3f}")
                    print(f"   Content preview: {row[0][:100]}...")
                    checks_passed += 1
                else:
                    print(f"   ⚠️  Chunk not found in database")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Summary
    print("\n" + "="*70)
    print(f"HEALTH CHECK COMPLETE: {checks_passed}/{total_checks} checks passed")
    print("="*70)

    if checks_passed == total_checks:
        print("\n🎉 Your chatbot is FULLY OPERATIONAL!")
        print("   All components working correctly.")
        print("   Only waiting for Gemini LLM quota to reset for text generation.")
    elif checks_passed >= 3:
        print("\n⚠️  Chatbot is PARTIALLY working")
        print(f"   {checks_passed}/{total_checks} components operational")
    else:
        print("\n❌ Chatbot has issues - some components not working")

    print()

    return checks_passed == total_checks


if __name__ == "__main__":
    asyncio.run(check_chatbot_health())
