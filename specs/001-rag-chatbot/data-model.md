# Data Model: Integrated RAG Chatbot

**Feature**: 001-rag-chatbot
**Date**: 2026-01-03
**Phase**: 1 (Design & Contracts)

## Overview

This document defines all entities, their attributes, relationships, and validation rules for the Integrated RAG Chatbot system.

---

## Entity Diagram

```
┌─────────────────┐
│   Book Content  │
│     Chunk       │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────┐      N    ┌──────────────┐
│   Retrieved     ├───────────►│   Chatbot    │
│    Passage      │            │   Response   │
└────────┬────────┘            └──────┬───────┘
         │ N                          │ 1
         │                            │
         │ 1                          │ N
┌────────▼────────┐            ┌─────▼────────┐
│   User Query    │◄───────────┤   Session    │
└────────┬────────┘      1:N   └──────────────┘
         │
         │ 0..1
         │
┌────────▼────────┐
│  Text Selection │
└─────────────────┘
```

---

## Entities

### 1. Book Content Chunk

Represents a semantically coherent segment of the book, stored as both text and vector embedding for retrieval.

**Attributes**:

| Attribute | Type | Description | Constraints | Example |
|-----------|------|-------------|-------------|---------|
| `chunk_id` | UUID | Unique identifier | Primary key, auto-generated | `550e8400-e29b-41d4-a716-446655440000` |
| `book_id` | UUID | Identifier for the book (future multi-book support) | Foreign key | `7c9e6679-7425-40de-944b-e07fc1f90ae7` |
| `text_content` | String | Raw text of the chunk | Non-empty, max 5000 chars | `"In Chapter 3, we explore..."` |
| `token_count` | Integer | Number of tokens in chunk | Range: 512-1024 | `847` |
| `embedding` | Float[] | Vector embedding (1536 dimensions for text-embedding-3-small) | Dimensions: 1536 | `[0.023, -0.15, ...]` |
| `chapter_id` | String | Chapter identifier | Optional | `"chapter-03"` |
| `chapter_title` | String | Human-readable chapter title | Optional | `"Machine Learning Fundamentals"` |
| `section_id` | String | Section identifier within chapter | Optional | `"section-03-02"` |
| `section_title` | String | Human-readable section title | Optional | `"Supervised Learning"` |
| `page_number` | Integer | Page number where chunk starts | Optional, >= 1 | `47` |
| `start_char_offset` | Integer | Character offset from book start | >= 0 | `12450` |
| `end_char_offset` | Integer | Character offset from book start | > start_char_offset | `14230` |
| `heading_hierarchy` | String[] | Breadcrumb of headings | Optional | `["Part II", "Chapter 3", "Section 3.2"]` |
| `created_at` | Timestamp | Ingestion timestamp | Auto-set | `2026-01-03T10:30:00Z` |

**Validation Rules**:
- `token_count` must be between 512 and 1024
- `end_char_offset` > `start_char_offset`
- `embedding` must have exactly 1536 dimensions
- If `chapter_id` is set, `chapter_title` should also be set

**Storage**:
- Text, metadata → PostgreSQL `book_chunks` table
- Embedding, metadata → Qdrant `book_chunks` collection

**Relationships**:
- 1 Book Content Chunk → N Retrieved Passages (one chunk can appear in multiple query results)

---

### 2. User Query

Represents a reader's natural-language question about the book.

**Attributes**:

| Attribute | Type | Description | Constraints | Example |
|-----------|------|-------------|-------------|---------|
| `query_id` | UUID | Unique identifier | Primary key, auto-generated | `a3bb189e-8bf9-3888-9912-ace4e6543002` |
| `session_id` | UUID | Associated session | Foreign key to Session | `f47ac10b-58cc-4372-a567-0e02b2c3d479` |
| `query_text` | String | User's question | Non-empty, max 1000 chars | `"What does the author say about overfitting?"` |
| `retrieval_mode` | Enum | Full book or selected text | Values: `FULL_BOOK`, `SELECTED_TEXT` | `FULL_BOOK` |
| `text_selection_id` | UUID | Reference to selected text (if mode is SELECTED_TEXT) | Foreign key to TextSelection, nullable | `null` |
| `created_at` | Timestamp | Query submission time | Auto-set | `2026-01-03T14:22:15Z` |

**Validation Rules**:
- `query_text` must be non-empty after trimming whitespace
- If `retrieval_mode` is `SELECTED_TEXT`, `text_selection_id` must not be null
- If `retrieval_mode` is `FULL_BOOK`, `text_selection_id` must be null

**Storage**: PostgreSQL `user_queries` table

**Relationships**:
- N User Queries → 1 Session
- 1 User Query → 0..1 Text Selection
- 1 User Query → 1 Chatbot Response

---

### 3. Text Selection

Represents a specific portion of the book selected by the reader for focused querying.

**Attributes**:

| Attribute | Type | Description | Constraints | Example |
|-----------|------|-------------|-------------|---------|
| `selection_id` | UUID | Unique identifier | Primary key, auto-generated | `b8e7ae12-f0a2-4c8e-8b9e-5e3f6d7c8a9b` |
| `selected_text` | String | Actual text content selected by user | Non-empty, max 50000 chars | `"Machine learning is a subset of..."` |
| `start_char_offset` | Integer | Start position in book | >= 0 | `15000` |
| `end_char_offset` | Integer | End position in book | > start_char_offset | `18500` |
| `chapter_id` | String | Chapter containing selection | Optional | `"chapter-04"` |
| `page_range_start` | Integer | Starting page number | Optional, >= 1 | `52` |
| `page_range_end` | Integer | Ending page number | Optional, >= page_range_start | `58` |
| `created_at` | Timestamp | Selection timestamp | Auto-set | `2026-01-03T14:20:00Z` |

**Validation Rules**:
- `end_char_offset` > `start_char_offset`
- Selection length (`end - start`) must be <= 50000 characters (prevents excessive selections)
- If `page_range_start` is set, `page_range_end` must also be set

**Storage**: PostgreSQL `text_selections` table (may be transient - stored only for query duration)

**Relationships**:
- 1 Text Selection → N User Queries (same selection can be reused for multiple questions)

---

### 4. Retrieved Passage

Represents a chunk retrieved from the vector database for a specific query, ranked by relevance.

**Attributes**:

| Attribute | Type | Description | Constraints | Example |
|-----------|------|-------------|-------------|---------|
| `retrieval_id` | UUID | Unique identifier for this retrieval instance | Primary key, auto-generated | `d4c5f6g7-h8i9-j0k1-l2m3-n4o5p6q7r8s9` |
| `query_id` | UUID | Associated query | Foreign key to UserQuery | `a3bb189e-8bf9-3888-9912-ace4e6543002` |
| `chunk_id` | UUID | Retrieved chunk | Foreign key to BookContentChunk | `550e8400-e29b-41d4-a716-446655440000` |
| `similarity_score` | Float | Cosine similarity to query | Range: 0.0-1.0 | `0.87` |
| `rank` | Integer | Position in retrieval results | >= 1 | `1` |
| `retrieved_at` | Timestamp | Retrieval timestamp | Auto-set | `2026-01-03T14:22:16Z` |

**Validation Rules**:
- `similarity_score` must be between 0.0 and 1.0
- `rank` starts at 1 (highest relevance)
- For a given `query_id`, `rank` values must be unique and sequential

**Storage**: PostgreSQL `retrieved_passages` table (for audit trail and quality analysis)

**Relationships**:
- N Retrieved Passages → 1 User Query
- N Retrieved Passages → 1 Book Content Chunk (same chunk can be retrieved for different queries)
- N Retrieved Passages → 1 Chatbot Response

---

### 5. Chatbot Response

Represents the generated answer to a user's query, including source citations and quality metrics.

**Attributes**:

| Attribute | Type | Description | Constraints | Example |
|-----------|------|-------------|-------------|---------|
| `response_id` | UUID | Unique identifier | Primary key, auto-generated | `e5f6g7h8-i9j0-k1l2-m3n4-o5p6q7r8s9t0` |
| `query_id` | UUID | Associated query | Foreign key to UserQuery | `a3bb189e-8bf9-3888-9912-ace4e6543002` |
| `response_text` | String | Generated answer text | Non-empty, max 5000 chars | `"According to Chapter 4 [Source 1], the author defines overfitting as..."` |
| `citations` | JSON | Array of cited chunk IDs and references | Non-empty array | `[{"chunk_id": "550e8400...", "reference": "[Source 1]", "chapter": "Chapter 4", "page": 52}]` |
| `retrieval_quality` | Float | Highest similarity score from retrieved passages | Range: 0.0-1.0 | `0.87` |
| `validation_passed` | Boolean | Whether response passed hallucination validation | True/False | `true` |
| `validation_notes` | String | Details from validation process | Optional | `"All claims cited, semantic similarity check passed"` |
| `llm_model` | String | Model used for generation | Non-empty | `"gpt-4-turbo"` |
| `llm_tokens_used` | Integer | Total tokens consumed (prompt + completion) | >= 0 | `1247` |
| `latency_ms` | Integer | Total response time in milliseconds | >= 0 | `2340` |
| `created_at` | Timestamp | Response generation timestamp | Auto-set | `2026-01-03T14:22:18Z` |

**Validation Rules**:
- `citations` array must not be empty if `validation_passed` is true
- `retrieval_quality` must be >= 0.7 (minimum similarity threshold)
- `response_text` must be non-empty

**Storage**: PostgreSQL `chatbot_responses` table

**Relationships**:
- 1 Chatbot Response → 1 User Query
- 1 Chatbot Response → N Retrieved Passages (references multiple chunks via citations)

---

### 6. Session

Represents a reader's continuous interaction period with the chatbot, maintaining conversation history for context.

**Attributes**:

| Attribute | Type | Description | Constraints | Example |
|-----------|------|-------------|-------------|---------|
| `session_id` | UUID | Unique identifier | Primary key, auto-generated | `f47ac10b-58cc-4372-a567-0e02b2c3d479` |
| `user_id` | String | Optional user identifier from book platform | Nullable, max 255 chars | `"reader_12345"` |
| `messages` | JSON | Conversation history (last 10 messages) | Array of message objects | `[{"role": "user", "content": "...", "timestamp": "..."}]` |
| `active_retrieval_mode` | Enum | Current mode (can switch between queries) | Values: `FULL_BOOK`, `SELECTED_TEXT` | `FULL_BOOK` |
| `current_selection_id` | UUID | Active text selection (if mode is SELECTED_TEXT) | Foreign key to TextSelection, nullable | `null` |
| `created_at` | Timestamp | Session start time | Auto-set | `2026-01-03T14:15:00Z` |
| `updated_at` | Timestamp | Last activity time | Auto-updated | `2026-01-03T14:22:18Z` |
| `expires_at` | Timestamp | Expiration time (30 minutes from last activity) | Auto-computed: updated_at + 30 min | `2026-01-03T14:52:18Z` |

**Validation Rules**:
- `messages` array max length: 10 (last 5 Q&A pairs)
- Each message object must have `role` (user/assistant), `content`, and `timestamp`
- `expires_at` must be > `updated_at`

**Message Object Schema**:
```json
{
  "role": "user" | "assistant",
  "content": "string",
  "timestamp": "ISO 8601 timestamp",
  "citations": ["chunk_id1", "chunk_id2"]  // Only for assistant messages
}
```

**Storage**: PostgreSQL `sessions` table

**Relationships**:
- 1 Session → N User Queries
- 1 Session → 0..1 Text Selection (current active selection)

---

## Relationships Summary

1. **Book Content Chunk → Retrieved Passage**: One-to-Many
   - A chunk can be retrieved multiple times across different queries

2. **User Query → Retrieved Passage**: One-to-Many
   - Each query retrieves multiple relevant chunks (typically 3-5)

3. **User Query → Chatbot Response**: One-to-One
   - Each query generates exactly one response

4. **User Query → Text Selection**: Many-to-One (optional)
   - Multiple queries can reference the same selection
   - Query may have no selection (full book mode)

5. **Session → User Query**: One-to-Many
   - A session contains multiple queries over time

6. **Session → Text Selection**: One-to-One (optional)
   - Session may have an active selection at any given time

---

## State Transitions

### Session Lifecycle

```
[Created] → [Active] → [Expired]
    ↓          ↓
    └─────────→ [Manually Closed]
```

- **Created**: Session initialized on first query
- **Active**: `updated_at` refreshed with each query, `expires_at` extended
- **Expired**: `expires_at` < current_time, background job purges
- **Manually Closed**: User/client explicitly deletes session

### Query Processing Flow

```
[Query Received] → [Retrieval] → [Response Generated] → [Validated] → [Returned]
                                         ↓
                                    [Validation Failed] → [Fallback Response]
```

- **Query Received**: Parse and validate query + selection context
- **Retrieval**: Fetch relevant chunks from Qdrant (filtered if selected text mode)
- **Response Generated**: LLM produces answer from retrieved passages
- **Validated**: Check citations and semantic grounding
- **Returned**: Success response with citations
- **Fallback**: Validation fails → return "Unable to answer" message

---

## Validation Rules Summary

### Cross-Entity Validation

1. **Retrieval Mode Consistency**:
   - If `UserQuery.retrieval_mode` is `SELECTED_TEXT`, `UserQuery.text_selection_id` must not be null
   - If `Session.active_retrieval_mode` is `SELECTED_TEXT`, `Session.current_selection_id` must not be null

2. **Citation Integrity**:
   - All `chunk_ids` in `ChatbotResponse.citations` must exist in `RetrievedPassage` records for that query
   - All `chunk_ids` in `RetrievedPassage` must reference valid `BookContentChunk` entries

3. **Timestamp Ordering**:
   - `UserQuery.created_at` must be >= `Session.created_at`
   - `ChatbotResponse.created_at` must be >= `UserQuery.created_at`
   - `Session.expires_at` must be > `Session.updated_at`

4. **Similarity Threshold Enforcement**:
   - All `RetrievedPassage.similarity_score` values should be >= 0.7 (minimum threshold)
   - `ChatbotResponse.retrieval_quality` (max similarity) must be >= 0.7

---

## Indexing Strategy (PostgreSQL)

```sql
-- Session lookup and expiration cleanup
CREATE INDEX idx_sessions_session_id ON sessions(session_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- Query history by session
CREATE INDEX idx_queries_session_id ON user_queries(session_id);
CREATE INDEX idx_queries_created_at ON user_queries(created_at);

-- Retrieved passages for audit/analysis
CREATE INDEX idx_retrieved_query_id ON retrieved_passages(query_id);
CREATE INDEX idx_retrieved_chunk_id ON retrieved_passages(chunk_id);
CREATE INDEX idx_retrieved_similarity ON retrieved_passages(similarity_score DESC);

-- Response lookup
CREATE INDEX idx_responses_query_id ON chatbot_responses(query_id);

-- Chunk metadata for citation generation
CREATE INDEX idx_chunks_book_id ON book_chunks(book_id);
CREATE INDEX idx_chunks_chapter_id ON book_chunks(chapter_id);
```

---

## Next Phase

Proceed to create API contracts (`contracts/api.openapi.yaml`) defining REST endpoints for these entities.
