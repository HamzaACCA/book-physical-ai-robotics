# Implementation Plan: Integrated RAG Chatbot

**Branch**: `001-rag-chatbot` | **Date**: 2026-01-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-rag-chatbot/spec.md`

## Summary

Build a Retrieval-Augmented Generation (RAG) chatbot embedded within a published book that enables readers to ask natural-language questions and receive accurate, grounded responses exclusively from the book's content. The system supports two retrieval modes: full book search and user-selected text search. Architecture prioritizes content fidelity, traceability, and strict context control.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, OpenAI SDK (Agents/ChatKit), Qdrant Client, psycopg3 (async), pydantic
**Storage**: Qdrant Cloud (vector embeddings), Neon Serverless PostgreSQL (metadata, sessions)
**Testing**: pytest, pytest-asyncio, httpx (API testing)
**Target Platform**: Linux server (containerized with Docker)
**Project Type**: Backend API service
**Performance Goals**:
- Vector retrieval: <500ms p95 latency
- End-to-end API response: <3s p95 (including LLM generation)
- Throughput: 50+ concurrent user sessions

**Constraints**:
- Responses MUST be grounded in retrieved book content only (zero hallucination)
- Selected text mode MUST enforce 100% context isolation (no leakage from other sections)
- Minimum similarity threshold: 0.7 cosine similarity for retrieved chunks
- Chunk size: 512-1024 tokens with 128-token overlap

**Scale/Scope**:
- Single book (can be extended to multiple books later)
- Target: 50-100 concurrent readers
- Book size: Assume 200-500 pages (typical published book)
- Vector DB: ~1000-5000 chunks per book

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Content Fidelity
- ✅ **Compliant**: Architecture uses RAG pattern with strict retrieval-based response generation
- ✅ **Compliant**: Response validation layer checks for hallucination before returning to user
- ✅ **Compliant**: System explicitly communicates when information is unavailable

### Principle II: User-Controlled Context
- ✅ **Compliant**: Dual retrieval modes implemented (full book vs. selected text)
- ✅ **Compliant**: Metadata filtering in Qdrant enforces context boundaries for selected text
- ✅ **Compliant**: API accepts selection context and restricts retrieval accordingly

### Principle III: Transparency and Traceability
- ✅ **Compliant**: Each response includes source citations (chapter, section, page)
- ✅ **Compliant**: Retrieved passages stored with metadata for audit trail
- ✅ **Compliant**: PostgreSQL logs query history and retrieval quality metrics

### Principle IV: Accuracy and Retrieval Quality
- ✅ **Compliant**: Chunking strategy: 512-1024 tokens with 128-token overlap, preserves paragraph boundaries
- ✅ **Compliant**: Semantic search via embeddings (OpenAI text-embedding-3-small)
- ✅ **Compliant**: Minimum similarity threshold 0.7 enforced before using retrieved chunks
- ✅ **Compliant**: Metadata (chapter, section, page, hierarchy) stored with each chunk

### Principle V: Security and Data Isolation
- ✅ **Compliant**: Only book content ingested into vector database
- ✅ **Compliant**: No external data sources queried during response generation
- ✅ **Compliant**: API keys and credentials stored in `.env` files (never committed)
- ✅ **Compliant**: User queries processed transiently (no sensitive PII logging)

### Principle VI: Scope Boundaries
- ✅ **Compliant**: System rejects out-of-scope questions (validation layer)
- ✅ **Compliant**: No professional advice generation unless directly quoted from book
- ✅ **Compliant**: Responses preserve author's original meaning (no reinterpretation)

### Test-First Development
- ✅ **Compliant**: Acceptance tests defined in spec will be written first (Red-Green-Refactor)
- ✅ **Compliant**: Contract tests for API endpoints, integration tests for RAG pipeline
- ✅ **Compliant**: Unit test coverage target: 80% for core logic

### Code Quality Gates
- ✅ **Compliant**: Linting (ruff), type checking (mypy), formatting (black)
- ✅ **Compliant**: Integration tests for API + RAG pipeline
- ✅ **Compliant**: Code review required before merge

**Constitution Compliance: PASS** - All principles satisfied by planned architecture.

## Project Structure

### Documentation (this feature)

```text
specs/001-rag-chatbot/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   └── api.openapi.yaml
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── query.py          # Query endpoints
│   │   │   └── health.py         # Health check
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   └── app.py                # FastAPI app initialization
│   ├── models/
│   │   ├── domain.py             # Domain models (Query, Response, Session, etc.)
│   │   ├── database.py           # PostgreSQL models
│   │   └── vector.py             # Qdrant payload schemas
│   ├── services/
│   │   ├── ingestion.py          # Book chunking and embedding
│   │   ├── retrieval.py          # Vector search and filtering
│   │   ├── rag.py                # RAG orchestration (retrieval + LLM)
│   │   ├── validation.py         # Response validation (hallucination check)
│   │   └── session.py            # Session management
│   ├── db/
│   │   ├── postgres.py           # PostgreSQL connection pool
│   │   └── qdrant.py             # Qdrant client setup
│   ├── core/
│   │   ├── config.py             # Environment configuration
│   │   └── logging.py            # Logging setup
│   └── cli/
│       └── ingest.py             # CLI tool for book ingestion
└── tests/
    ├── contract/
    │   └── test_api_contract.py  # API contract tests
    ├── integration/
    │   ├── test_rag_pipeline.py  # End-to-end RAG tests
    │   ├── test_retrieval.py     # Vector search tests
    │   └── test_ingestion.py     # Chunking and embedding tests
    └── unit/
        ├── test_chunking.py      # Chunking logic
        ├── test_validation.py    # Response validation
        └── test_models.py        # Model serialization

.env.example                      # Environment template
docker-compose.yml                # Local development setup
Dockerfile                        # Container build
pyproject.toml                    # Python dependencies
```

**Structure Decision**: Selected **Web application** structure with `backend/` directory because this is a service-oriented architecture (API-first). Frontend integration is out of scope for this feature (handled by book platform), but the API structure allows future frontend development. The `backend/src/` organization separates concerns: API routing, domain models, business services, data access, and configuration.

## Complexity Tracking

No constitutional violations detected. Architecture aligns with all principles and follows YAGNI (minimum complexity to satisfy requirements).

---

## Phase 0: Research & Technology Decisions

**Status**: To be completed by /sp.plan command

### Research Tasks

#### 1. Chunking Strategy for Book Content
**Question**: What's the optimal chunk size and overlap for published book content to preserve context while enabling precise retrieval?

**Research Areas**:
- Chunk size tradeoffs (token length vs. context preservation)
- Overlap strategies for semantic continuity
- Paragraph boundary preservation techniques
- Handling special content (tables, footnotes, quotes)

#### 2. Qdrant Filtering for Selected Text Mode
**Question**: How to efficiently filter Qdrant vector search results to only chunks within user-selected text boundaries?

**Research Areas**:
- Qdrant payload filtering capabilities
- Metadata schema for positional tracking (start/end offsets, chapter/section IDs)
- Performance impact of filtered vs. unfiltered vector search
- Hybrid search strategies (vector + metadata filters)

#### 3. Hallucination Detection in RAG Responses
**Question**: What techniques can validate that LLM responses are grounded in retrieved content and don't introduce fabricated information?

**Research Areas**:
- Fact-checking LLM outputs against source passages
- Semantic similarity between response and retrieved chunks
- Citation verification (ensuring all claims have source evidence)
- Detecting "confident hallucinations" (plausible but incorrect statements)

#### 4. Session Management for Conversational Context
**Question**: How to maintain conversation history and context across multiple user queries while keeping the system stateless at the API level?

**Research Areas**:
- Session storage strategies (PostgreSQL vs. Redis vs. in-memory)
- Conversation window sizing (how many previous Q&A pairs to retain)
- Context injection into RAG pipeline (combining history with new query)
- Session expiration and cleanup policies

#### 5. OpenAI Agents SDK vs. Custom RAG Orchestration
**Question**: Should we use OpenAI Agents SDK for orchestration or build custom RAG logic?

**Research Areas**:
- OpenAI Agents SDK capabilities for tool calling and retrieval
- Control over prompt construction and response validation
- Latency and cost implications
- Flexibility for custom validation and context control

**Output**: `research.md` documenting decisions for each area above.

---

## Phase 1: Design & Contracts

**Status**: To be completed after Phase 0 research

### Artifacts to Generate

1. **data-model.md**: Define all entities and their relationships
   - Book Content Chunk (text, metadata, embeddings)
   - User Query (query text, session ID, retrieval mode)
   - Text Selection (start/end positions, selected content)
   - Retrieved Passage (chunk ID, similarity score, metadata)
   - Chatbot Response (response text, citations, quality metrics)
   - Session (session ID, history, active mode)

2. **contracts/api.openapi.yaml**: OpenAPI specification for all endpoints
   - `POST /api/v1/query` - Submit user question
   - `POST /api/v1/query/selected` - Submit question with text selection
   - `GET /api/v1/session/{session_id}` - Retrieve session history
   - `DELETE /api/v1/session/{session_id}` - End session
   - `GET /api/health` - Health check
   - `POST /api/admin/ingest` - Trigger book ingestion (admin only)

3. **quickstart.md**: Developer onboarding guide
   - Local environment setup (Docker Compose)
   - Environment variables configuration
   - Running ingestion CLI
   - API usage examples
   - Running tests

4. **Agent context update**: Run `.specify/scripts/bash/update-agent-context.sh claude`

---

## Phase 2: Tasks Generation

**Status**: Deferred to `/sp.tasks` command (not part of /sp.plan)

Tasks will be organized by user story priority (P1, P2, P3) with:
- Setup and foundational infrastructure
- P1: Full book query implementation
- P2: Selected text query implementation
- P3: Source traceability and citations
- Polish and cross-cutting concerns

---

## Next Steps

1. Execute Phase 0 research to resolve unknowns
2. Generate Phase 1 design artifacts (data-model, contracts, quickstart)
3. Run constitution check validation post-design
4. Proceed to `/sp.tasks` for task breakdown
