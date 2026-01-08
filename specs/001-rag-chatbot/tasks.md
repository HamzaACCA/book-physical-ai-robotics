---

description: "Task list for Integrated RAG Chatbot implementation"
---

# Tasks: Integrated RAG Chatbot

**Input**: Design documents from `/specs/001-rag-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend API**: `backend/src/`, `backend/tests/`
- Paths assume backend API service structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure (backend/src/, backend/tests/, backend/data/)
- [x] T002 Initialize Python project with pyproject.toml including dependencies: FastAPI, OpenAI SDK, Qdrant Client, psycopg3, pydantic, pytest
- [x] T003 [P] Configure linting and formatting tools (ruff, mypy, black) in pyproject.toml
- [x] T004 [P] Create .env.example file with all required environment variables (OpenAI, Qdrant, PostgreSQL)
- [x] T005 [P] Create Dockerfile for backend API containerization
- [x] T006 [P] Create docker-compose.yml for local development environment
- [x] T007 [P] Create .gitignore file (exclude .env, __pycache__, .pytest_cache, venv)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 Create core configuration module in backend/src/core/config.py (load env vars using pydantic Settings)
- [x] T009 [P] Setup logging configuration in backend/src/core/logging.py
- [x] T010 Create PostgreSQL connection pool in backend/src/db/postgres.py (async with psycopg3)
- [x] T011 [P] Create Qdrant client setup in backend/src/db/qdrant.py
- [x] T012 Define database schema for book_chunks table in backend/src/db/schema.sql
- [x] T013 Define database schema for sessions table in backend/src/db/schema.sql
- [x] T014 Define database schema for user_queries table in backend/src/db/schema.sql
- [x] T015 Define database schema for text_selections table in backend/src/db/schema.sql
- [x] T016 Define database schema for retrieved_passages table in backend/src/db/schema.sql
- [x] T017 Define database schema for chatbot_responses table in backend/src/db/schema.sql
- [x] T018 [P] Create Qdrant collection initialization script in backend/src/db/init_qdrant.py (1536 dimensions for text-embedding-3-small)
- [x] T019 Create domain models in backend/src/models/domain.py (Query, Response, Session, TextSelection, Citation - pydantic models)
- [x] T020 [P] Create PostgreSQL models in backend/src/models/database.py (SQLAlchemy/psycopg3 models for all tables)
- [x] T021 [P] Create Qdrant payload schemas in backend/src/models/vector.py
- [x] T022 Initialize FastAPI application in backend/src/api/app.py (app instance, CORS, exception handlers)
- [x] T023 Create FastAPI dependencies in backend/src/api/dependencies.py (get_db, get_qdrant_client, etc.)
- [x] T024 [P] Create health check route in backend/src/api/routes/health.py (check PostgreSQL, Qdrant, OpenAI connectivity)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ask Questions About Full Book Content (Priority: P1) 🎯 MVP

**Goal**: Enable readers to ask natural-language questions and receive accurate, grounded responses from the full book

**Independent Test**: Ask questions about various book topics and verify responses are accurate, sourced from the book, and clearly indicate when information is unavailable

### Implementation for User Story 1

- [x] T025 [P] [US1] Create book ingestion service in backend/src/services/ingestion.py (chunk_book_content function with 800 token target, 128 overlap, paragraph boundaries)
- [x] T026 [P] [US1] Implement embedding generation in backend/src/services/ingestion.py (generate_embeddings function using OpenAI text-embedding-3-small)
- [x] T027 [US1] Implement book storage in backend/src/services/ingestion.py (store_chunks_postgres and store_embeddings_qdrant functions)
- [x] T028 [P] [US1] Create ingestion CLI tool in backend/src/cli/ingest.py (accept file path, book ID, book title, format parameters)
- [x] T029 [P] [US1] Implement full book retrieval service in backend/src/services/retrieval.py (retrieve_full_book function using Qdrant vector search)
- [x] T030 [P] [US1] Implement session management service in backend/src/services/session.py (create_session, load_session, update_session, expire_session functions)
- [x] T031 [US1] Implement RAG orchestration in backend/src/services/rag.py (process_query function combining retrieval + LLM + validation)
- [x] T032 [US1] Implement response validation in backend/src/services/validation.py (validate_response_grounding function with citation check and semantic similarity)
- [x] T033 [US1] Implement query endpoint in backend/src/api/routes/query.py (POST /api/v1/query for full book queries)
- [x] T034 [US1] Implement session retrieval endpoint in backend/src/api/routes/query.py (GET /api/v1/session/{session_id})
- [x] T035 [US1] Implement session deletion endpoint in backend/src/api/routes/query.py (DELETE /api/v1/session/{session_id})
- [x] T036 [P] [US1] Add error handling for out-of-scope queries in backend/src/services/validation.py
- [x] T037 [P] [US1] Add logging for query processing in backend/src/services/rag.py (log query_id, retrieval_quality, latency)
- [x] T038 [US1] Integration test: Ingest sample book and verify chunks stored in both PostgreSQL and Qdrant in backend/tests/integration/test_ingestion.py
- [x] T039 [US1] Integration test: Submit query and verify response with citations in backend/tests/integration/test_rag_pipeline.py
- [x] T040 [US1] Integration test: Test out-of-scope query rejection in backend/tests/integration/test_rag_pipeline.py
- [x] T041 [US1] Integration test: Test concurrent queries (10 parallel requests) in backend/tests/integration/test_rag_pipeline.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (MVP complete)

---

## Phase 4: User Story 2 - Ask Questions About Selected Text Only (Priority: P2)

**Goal**: Enable readers to ask questions restricted to user-selected text with 100% context isolation

**Independent Test**: Select various text portions, ask questions, and verify responses reference only the selected content

### Implementation for User Story 2

- [ ] T042 [P] [US2] Implement selected text retrieval with Qdrant filtering in backend/src/services/retrieval.py (retrieve_with_filter function using payload filters on start/end offsets)
- [ ] T043 [US2] Implement selected text query endpoint in backend/src/api/routes/query.py (POST /api/v1/query/selected accepting TextSelection in request body)
- [ ] T044 [P] [US2] Add validation for text selection boundaries in backend/src/services/validation.py (validate_selection function checking offset constraints)
- [ ] T045 [P] [US2] Extend RAG service to handle retrieval mode switching in backend/src/services/rag.py (modify process_query to accept selection parameter)
- [ ] T046 [US2] Integration test: Query with selected text and verify no leakage from other sections in backend/tests/integration/test_retrieval.py
- [ ] T047 [US2] Integration test: Switch between full book and selected text modes in same session in backend/tests/integration/test_rag_pipeline.py
- [ ] T048 [US2] Integration test: Test empty result handling when selection doesn't contain answer in backend/tests/integration/test_rag_pipeline.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Understand Response Sources and Traceability (Priority: P3)

**Goal**: Provide source citations with chapter/section/page references for transparency and verification

**Independent Test**: Ask questions, receive responses, and verify that passage references are accurate and traceable back to the original book location

### Implementation for User Story 3

- [ ] T049 [P] [US3] Implement citation extraction in backend/src/services/rag.py (extract_citations function parsing response for citation markers and mapping to chunk metadata)
- [ ] T050 [P] [US3] Enhance response model to include detailed citations in backend/src/models/domain.py (Citation model with chunk_id, reference, chapter_title, section_title, page_number, text_preview)
- [ ] T051 [US3] Update RAG service to populate citations in response in backend/src/services/rag.py (modify process_query to return QueryResponse with full citations array)
- [ ] T052 [P] [US3] Add citation accuracy logging in backend/src/services/validation.py (log citation count, chunk references)
- [ ] T053 [US3] Integration test: Verify citation accuracy (all citations map to retrieved chunks) in backend/tests/integration/test_rag_pipeline.py
- [ ] T054 [US3] Integration test: Test multi-source responses (question requiring 3+ chunks) in backend/tests/integration/test_rag_pipeline.py
- [ ] T055 [US3] Integration test: Verify "information unavailable" explanation includes search scope in backend/tests/integration/test_rag_pipeline.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T056 [P] Add input sanitization for all API endpoints in backend/src/api/routes/query.py (trim whitespace, validate lengths, escape special chars)
- [ ] T057 [P] Implement rate limiting middleware in backend/src/api/app.py (limit: 100 requests per minute per IP)
- [ ] T058 [P] Add API key authentication for admin ingestion endpoint in backend/src/api/routes/query.py (POST /api/admin/ingest with X-API-Key header validation)
- [ ] T059 [P] Unit test: Chunking logic preserves paragraph boundaries in backend/tests/unit/test_chunking.py
- [ ] T060 [P] Unit test: Embedding generation handles batch processing in backend/tests/unit/test_chunking.py
- [ ] T061 [P] Unit test: Response validation detects hallucination (response with facts not in chunks) in backend/tests/unit/test_validation.py
- [ ] T062 [P] Unit test: Session expiration logic (30 min timeout) in backend/tests/unit/test_session.py
- [ ] T063 [P] Unit test: Domain model serialization/deserialization in backend/tests/unit/test_models.py
- [ ] T064 [P] Create API documentation serving in backend/src/api/app.py (Swagger UI at /docs, ReDoc at /redoc)
- [ ] T065 Implement background job for expired session cleanup in backend/src/services/session.py (run hourly)
- [ ] T066 [P] Add performance monitoring for vector retrieval latency in backend/src/services/retrieval.py (log p95 latency)
- [ ] T067 [P] Add performance monitoring for end-to-end response time in backend/src/services/rag.py (log p95 latency)
- [ ] T068 Update quickstart.md with actual curl examples from integration tests in specs/001-rag-chatbot/quickstart.md
- [ ] T069 Run full test suite and ensure 80% coverage for core logic (backend/src/services/, backend/src/core/)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3, 4, 5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Extends US1 retrieval logic but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Enhances US1 responses but independently testable

### Within Each User Story

- Ingestion before retrieval (need data to query)
- Retrieval before RAG orchestration
- RAG orchestration before API endpoints
- Core implementation before integration tests
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (7 tasks: T003, T004, T005, T006, T007)
- All Foundational tasks marked [P] can run in parallel (within Phase 2) after T008 completes (10 tasks: T009, T011, T018, T020, T021, T024)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Within each story, tasks marked [P] can run in parallel

---

## Parallel Example: Foundational Phase

After T008 (config) completes, run in parallel:

```bash
# Launch foundational infrastructure tasks together:
Task T009: Setup logging (backend/src/core/logging.py)
Task T011: Qdrant client (backend/src/db/qdrant.py)
Task T018: Qdrant collection init (backend/src/db/init_qdrant.py)
Task T020: PostgreSQL models (backend/src/models/database.py)
Task T021: Qdrant payload schemas (backend/src/models/vector.py)
Task T024: Health check route (backend/src/api/routes/health.py)
```

---

## Parallel Example: User Story 1

After Foundational phase completes, run in parallel:

```bash
# Launch all ingestion components together:
Task T025: Chunking service (backend/src/services/ingestion.py)
Task T026: Embedding generation (backend/src/services/ingestion.py)
Task T029: Retrieval service (backend/src/services/retrieval.py)
Task T030: Session management (backend/src/services/session.py)

# Then after ingestion components, run service layer in parallel:
Task T031: RAG orchestration (backend/src/services/rag.py)
Task T032: Response validation (backend/src/services/validation.py)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T025-T041)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Ingest a sample book
   - Ask 10 diverse questions
   - Verify response accuracy, citations, and "not available" handling
   - Test concurrent queries (10 parallel)
5. Deploy/demo if ready (functional RAG chatbot for full book queries)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (T025-T041) → Test independently → **Deploy/Demo (MVP!)**
   - Value: Readers can ask any question about the full book
3. Add User Story 2 (T042-T048) → Test independently → Deploy/Demo
   - Value: Readers can focus queries on selected text with context isolation
4. Add User Story 3 (T049-T055) → Test independently → Deploy/Demo
   - Value: Readers can verify sources and trace answers back to book
5. Add Polish (T056-T069) → Deploy/Demo
   - Value: Production-ready system with security, monitoring, comprehensive tests

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T024)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (T025-T041) - Full book queries
   - **Developer B**: User Story 2 (T042-T048) - Selected text queries
   - **Developer C**: User Story 3 (T049-T055) - Source traceability
3. Stories complete and integrate independently
4. Team reconvenes for Polish (T056-T069)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

**Test Coverage Target**: Minimum 80% for backend/src/services/ and backend/src/core/

**Performance Validation**:
- Vector retrieval: <500ms p95 (measured in T066)
- End-to-end API response: <3s p95 (measured in T067)
- Concurrent users: 50+ simultaneous sessions (validated in T041)

**Constitution Compliance Checkpoints**:
- T032: Response validation enforces Content Fidelity (Principle I)
- T042: Selected text filtering enforces User-Controlled Context (Principle II)
- T049: Citation extraction enforces Transparency and Traceability (Principle III)
- T025: Chunking strategy enforces Accuracy and Retrieval Quality (Principle IV)
- T004: Environment variables enforce Security and Data Isolation (Principle V)
- T036: Out-of-scope rejection enforces Scope Boundaries (Principle VI)
