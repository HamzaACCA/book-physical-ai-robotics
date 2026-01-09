# Quickstart Guide: Integrated RAG Chatbot

**Feature**: 001-rag-chatbot
**Date**: 2026-01-03
**Audience**: Developers

## Overview

This guide walks you through setting up the Integrated RAG Chatbot development environment, ingesting a sample book, and testing the API locally.

**Prerequisites**:
- Docker & Docker Compose installed
- Python 3.11+ installed
- Git repository cloned
- OpenAI API key (for embeddings and LLM)
- Qdrant Cloud account (free tier)
- Neon Serverless PostgreSQL database created

---

## Step 1: Environment Setup

### 1.1 Clone and Navigate to Project

```bash
git clone <repository-url>
cd <repository-directory>
git checkout 001-rag-chatbot
```

### 1.2 Create Environment File

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-4-turbo

# Qdrant Configuration
QDRANT_URL=https://your-cluster-url.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key-here
QDRANT_COLLECTION_NAME=book_chunks

# PostgreSQL Configuration (Neon Serverless)
DATABASE_URL=postgresql://user:password@your-neon-host.neon.tech/database_name?sslmode=require
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=5

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true  # Development only
API_WORKERS=1    # Development only

# Admin Configuration
ADMIN_API_KEY=your-secret-admin-key-here

# Application Settings
LOG_LEVEL=INFO
CHUNK_SIZE_TOKENS=800
CHUNK_OVERLAP_TOKENS=128
MIN_SIMILARITY_THRESHOLD=0.7
SESSION_EXPIRATION_MINUTES=30
MAX_CONVERSATION_MESSAGES=10
```

### 1.3 Start Development Environment

Using Docker Compose (recommended):

```bash
cd backend
docker-compose up -d
```

This starts:
- FastAPI application (http://localhost:8000)
- API documentation (http://localhost:8000/docs)

**Verify services are running**:

```bash
docker-compose ps
```

Expected output:

```
NAME                STATUS              PORTS
rag-chatbot-api     running            0.0.0.0:8000->8000/tcp
```

---

## Step 2: Database Initialization

### 2.1 Run Migrations

Initialize PostgreSQL schema:

```bash
# From backend/ directory
docker-compose exec api python -m alembic upgrade head
```

This creates tables:
- `book_chunks`
- `user_queries`
- `text_selections`
- `retrieved_passages`
- `chatbot_responses`
- `sessions`

### 2.2 Verify Qdrant Collection

The API will auto-create the Qdrant collection on first run. Verify it exists:

```bash
# Using Qdrant Cloud dashboard or API
curl -X GET "${QDRANT_URL}/collections/${QDRANT_COLLECTION_NAME}" \
  -H "api-key: ${QDRANT_API_KEY}"
```

Expected: Collection exists with 1536-dimensional vectors.

---

## Step 3: Ingest Sample Book

### 3.1 Prepare Book File

Place a sample book file (TXT, PDF, or EPUB) in `backend/data/books/`:

```bash
mkdir -p backend/data/books
# Copy your book file, e.g.:
cp ~/Downloads/sample-book.txt backend/data/books/sample-book.txt
```

### 3.2 Run Ingestion CLI

Use the CLI tool to chunk, embed, and index the book:

```bash
docker-compose exec api python -m src.cli.ingest \
  --file /app/data/books/sample-book.txt \
  --book-id "7c9e6679-7425-40de-944b-e07fc1f90ae7" \
  --book-title "Sample Book Title" \
  --format txt
```

**Options**:
- `--file`: Path to book file (inside container)
- `--book-id`: UUID for the book
- `--book-title`: Human-readable title
- `--format`: File format (txt, pdf, epub)

**Expected output**:

```
[INFO] Starting book ingestion: Sample Book Title
[INFO] Parsing book file: /app/data/books/sample-book.txt
[INFO] Book parsed: 245 pages, 87,432 characters
[INFO] Chunking content (target: 800 tokens, overlap: 128 tokens)
[INFO] Created 1,247 chunks
[INFO] Generating embeddings (batch size: 100)
[INFO] Batch 1/13 embedded (100 chunks)
[INFO] Batch 2/13 embedded (100 chunks)
...
[INFO] All embeddings generated (1,247 chunks)
[INFO] Storing chunks in PostgreSQL...
[INFO] Storing embeddings in Qdrant...
[INFO] Ingestion complete! Book ID: 7c9e6679-7425-40de-944b-e07fc1f90ae7
[INFO] Total chunks: 1,247
[INFO] Processing time: 3m 42s
```

### 3.3 Verify Ingestion

Check that chunks are stored:

**PostgreSQL**:

```bash
docker-compose exec api python -c "
from src.db.postgres import get_db
db = next(get_db())
count = db.execute('SELECT COUNT(*) FROM book_chunks').scalar()
print(f'Chunks in PostgreSQL: {count}')
"
```

**Qdrant**:

```bash
curl -X GET "${QDRANT_URL}/collections/${QDRANT_COLLECTION_NAME}" \
  -H "api-key: ${QDRANT_API_KEY}" | jq '.result.points_count'
```

Expected: Same count (~1,247 chunks).

---

## Step 4: Test API Endpoints

### 4.1 Health Check

Verify the API is running:

```bash
curl http://localhost:8000/api/v1/health
```

**Expected response**:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-03T14:30:00Z",
  "details": {
    "database": "up",
    "vector_db": "up",
    "llm_service": "up"
  }
}
```

### 4.2 Submit a Query (Full Book Mode)

Ask a question about the entire book:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What does the author say about machine learning?",
    "user_id": "test_user_001"
  }'
```

**Expected response** (example):

```json
{
  "response_id": "e5f6g7h8-i9j0-k1l2-m3n4-o5p6q7r8s9t0",
  "query_id": "a3bb189e-8bf9-3888-9912-ace4e6543002",
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "response_text": "According to Chapter 4 [Source 1], the author defines machine learning as a subset of artificial intelligence that enables systems to learn from data without explicit programming. The author emphasizes [Source 2] that machine learning models improve through experience...",
  "citations": [
    {
      "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
      "reference": "[Source 1]",
      "chapter_title": "Machine Learning Fundamentals",
      "section_title": "Introduction to ML",
      "page_number": 52,
      "text_preview": "Machine learning is a subset of artificial intelligence that..."
    },
    {
      "chunk_id": "660f9511-f3ac-52e5-b827-557766551111",
      "reference": "[Source 2]",
      "chapter_title": "Machine Learning Fundamentals",
      "section_title": "Learning from Data",
      "page_number": 54,
      "text_preview": "ML models improve their performance through experience..."
    }
  ],
  "retrieval_quality": 0.87,
  "latency_ms": 2340
}
```

**Save the `session_id` for follow-up queries.**

### 4.3 Submit a Follow-Up Query

Continue the conversation using the session ID:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Can you explain that concept further?",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }'
```

The system maintains context from the previous question.

### 4.4 Submit a Query with Selected Text

Ask a question about a specific text selection:

```bash
curl -X POST http://localhost:8000/api/v1/query/selected \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What does this paragraph mean?",
    "selection": {
      "selected_text": "Machine learning is a subset of artificial intelligence that enables systems to learn from data without explicit programming. Models improve through experience, identifying patterns and making decisions with minimal human intervention.",
      "start_char_offset": 15000,
      "end_char_offset": 15250,
      "chapter_id": "chapter-04",
      "page_range_start": 52,
      "page_range_end": 52
    },
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }'
```

The response will only reference the selected text.

### 4.5 Retrieve Session History

Get conversation history:

```bash
curl http://localhost:8000/api/v1/session/f47ac10b-58cc-4372-a567-0e02b2c3d479
```

**Expected response**:

```json
{
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "user_id": "test_user_001",
  "messages": [
    {
      "role": "user",
      "content": "What does the author say about machine learning?",
      "timestamp": "2026-01-03T14:30:00Z"
    },
    {
      "role": "assistant",
      "content": "According to Chapter 4 [Source 1]...",
      "timestamp": "2026-01-03T14:30:03Z",
      "citations": ["550e8400-e29b-41d4-a716-446655440000", "660f9511-f3ac-52e5-b827-557766551111"]
    },
    {
      "role": "user",
      "content": "Can you explain that concept further?",
      "timestamp": "2026-01-03T14:32:15Z"
    },
    {
      "role": "assistant",
      "content": "Certainly! The concept of machine learning...",
      "timestamp": "2026-01-03T14:32:18Z",
      "citations": ["770g0622-g4bd-63f6-c938-668877662222"]
    }
  ],
  "active_retrieval_mode": "FULL_BOOK",
  "created_at": "2026-01-03T14:30:00Z",
  "updated_at": "2026-01-03T14:32:18Z",
  "expires_at": "2026-01-03T15:02:18Z"
}
```

### 4.6 Delete Session

End the session manually:

```bash
curl -X DELETE http://localhost:8000/api/v1/session/f47ac10b-58cc-4372-a567-0e02b2c3d479
```

**Expected**: HTTP 204 No Content

---

## Step 5: Run Tests

### 5.1 Run All Tests

```bash
docker-compose exec api pytest tests/ -v
```

### 5.2 Run Specific Test Suites

**Contract tests** (API endpoint validation):

```bash
docker-compose exec api pytest tests/contract/ -v
```

**Integration tests** (RAG pipeline end-to-end):

```bash
docker-compose exec api pytest tests/integration/ -v
```

**Unit tests** (chunking, validation, models):

```bash
docker-compose exec api pytest tests/unit/ -v
```

### 5.3 Check Test Coverage

```bash
docker-compose exec api pytest --cov=src --cov-report=term-missing tests/
```

Target: Minimum 80% coverage for core logic.

---

## Step 6: API Documentation

### 6.1 Access Interactive Docs

Navigate to:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 6.2 Explore Endpoints

The interactive documentation allows you to:
- View all available endpoints
- See request/response schemas
- Test endpoints directly from the browser

---

## Troubleshooting

### Issue: "Qdrant connection failed"

**Symptom**: API health check shows `vector_db: down`

**Solution**:
1. Verify Qdrant URL and API key in `.env`
2. Check Qdrant Cloud dashboard for cluster status
3. Test connection manually:

```bash
curl -X GET "${QDRANT_URL}/collections" -H "api-key: ${QDRANT_API_KEY}"
```

### Issue: "PostgreSQL connection refused"

**Symptom**: API health check shows `database: down`

**Solution**:
1. Verify `DATABASE_URL` in `.env`
2. Check Neon dashboard for database status
3. Test connection:

```bash
docker-compose exec api python -c "from src.db.postgres import engine; engine.connect()"
```

### Issue: "OpenAI API rate limit exceeded"

**Symptom**: Queries fail with HTTP 429 error

**Solution**:
1. Reduce ingestion batch size (slower but respects rate limits)
2. Upgrade OpenAI API tier for higher limits
3. Add retry logic with exponential backoff (already implemented)

### Issue: "Chunks not appearing in Qdrant"

**Symptom**: Ingestion completes but queries return no results

**Solution**:
1. Check Qdrant collection configuration:

```bash
curl -X GET "${QDRANT_URL}/collections/${QDRANT_COLLECTION_NAME}" \
  -H "api-key: ${QDRANT_API_KEY}"
```

2. Verify vector dimensions match (should be 1536 for text-embedding-3-small)
3. Re-run ingestion with `--force` flag to recreate collection

### Issue: "Session expired too quickly"

**Symptom**: Session deleted before expected

**Solution**:
- Increase `SESSION_EXPIRATION_MINUTES` in `.env` (default: 30)
- Restart API: `docker-compose restart api`

---

## Next Steps

1. **Implement Tests**: Write acceptance tests for user stories (see `/sp.tasks`)
2. **Load Testing**: Test with concurrent users (target: 50+ simultaneous sessions)
3. **Production Deployment**: Deploy to cloud provider with environment-specific `.env`
4. **Monitoring**: Set up logging and metrics collection (Prometheus, Grafana)
5. **Book Platform Integration**: Connect API to digital book frontend

---

## Additional Resources

- **API Specification**: `specs/001-rag-chatbot/contracts/api.openapi.yaml`
- **Data Model**: `specs/001-rag-chatbot/data-model.md`
- **Implementation Plan**: `specs/001-rag-chatbot/plan.md`
- **Research Decisions**: `specs/001-rag-chatbot/research.md`
- **Feature Specification**: `specs/001-rag-chatbot/spec.md`

---

**Support**: For issues or questions, contact the development team or open an issue in the repository.
