---
id: 0002
title: RAG Chatbot Implementation Plan
stage: plan
date: 2026-01-03
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-rag-chatbot
branch: 001-rag-chatbot
user: Hamza
command: /sp.plan
labels: ["plan", "architecture", "rag", "research", "design"]
links:
  spec: specs/001-rag-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-rag-chatbot/plan.md
  - specs/001-rag-chatbot/research.md
  - specs/001-rag-chatbot/data-model.md
  - specs/001-rag-chatbot/contracts/api.openapi.yaml
  - specs/001-rag-chatbot/quickstart.md
  - CLAUDE.md (agent context updated)
tests:
  - N/A (planning phase, no executable tests)
---

## Prompt

```text
# Plan: Integrated RAG Chatbot Architecture

## Overview
This plan outlines the technical stack and system architecture for building an
integrated Retrieval-Augmented Generation (RAG) chatbot embedded within a
published book. The architecture is designed for accuracy, scalability, and
strict content control.

---

## Tech Stack

### AI & Orchestration
- **OpenAI Agents / ChatKit SDKs**
  - Used for conversational flow, tool calling, and response orchestration
  - Ensures structured reasoning and controlled output generation

### Backend API
- **FastAPI**
  - Provides RESTful endpoints for query handling
  - Manages user requests, selected text context, and response delivery
  - Lightweight, high-performance, and async-friendly

### Vector Database
- **Qdrant Cloud (Free Tier)**
  - Stores vector embeddings of book content
  - Enables semantic search and similarity-based retrieval
  - Supports filtered retrieval for user-selected text

### Relational Database
- **Neon Serverless PostgreSQL**
  - Stores metadata, document references, user sessions, and query logs
  - Manages book structure (chapters, sections, page references)

### Embedding Pipeline
- Book content is chunked and embedded
- Each chunk is stored with metadata (chapter, section, page range)
- Embeddings are indexed in Qdrant for retrieval

---

## System Architecture

### Ingestion Layer
- Parses and chunks the published book content
- Generates embeddings for each chunk
- Stores embeddings in Qdrant
- Stores metadata in PostgreSQL

### Query Layer
- Accepts user queries and optional selected text
- Applies context rules based on user selection
- Retrieves relevant chunks from Qdrant

### RAG Layer
- Combines retrieved content with user query
- Passes grounded context to OpenAI Agents
- Enforces content boundaries and response rules

### Response Layer
- Generates final answer
- Validates response against retrieved content
- Returns answer to the user interface

---

## Context Control Strategy
- If no text is selected:
  - Retrieve from the full book corpus
- If text is selected:
  - Restrict retrieval to embeddings linked to the selected content only
- Prevents context leakage and hallucination

---

## Security and Data Handling
- Only book content is indexed and retrievable
- No external data sources are queried at runtime
- User data is stored minimally and securely

---

## Scalability Considerations
- Serverless PostgreSQL supports elastic scaling
- Vector search scales independently via Qdrant Cloud
- Stateless API design allows horizontal scaling

---

## Deployment Strategy
- Backend API deployed as a containerized service
- Environment-based configuration for development and production
- Secure API key and credential management

---

## Maintenance and Monitoring
- Logging of queries and retrieval results for auditability
- Monitoring response accuracy and failure cases
- Periodic re-indexing when book content updates
```

## Response snapshot

Completed comprehensive implementation plan with all phases:

**Technical Context**:
- Language: Python 3.11+
- Stack: FastAPI, OpenAI SDK, Qdrant Client, psycopg3 (async), pydantic
- Storage: Qdrant Cloud (vectors), Neon Serverless PostgreSQL (metadata)
- Performance: <500ms retrieval p95, <3s end-to-end p95, 50+ concurrent users
- Constraints: Zero hallucination, 0.7 min similarity threshold, 512-1024 token chunks with 128 overlap

**Constitution Check: PASS** - All 6 principles satisfied:
- ✅ Content Fidelity: RAG with validation layer
- ✅ User-Controlled Context: Dual retrieval modes (full book vs. selected text)
- ✅ Transparency: Citations with chapter/section/page references
- ✅ Accuracy: Semantic search, chunking standards, similarity thresholds
- ✅ Security: Book-only content, env-based secrets, no external sources
- ✅ Scope Boundaries: Validation layer rejects out-of-scope queries

**Phase 0: Research** (research.md) - 5 key decisions:
1. Chunking: 800 tokens, 128 overlap, paragraph boundaries
2. Filtering: Qdrant payload filters on character offsets for selected text mode
3. Hallucination Detection: Citation-based + semantic similarity validation
4. Session Management: PostgreSQL storage, 5 Q&A window, 30-min expiration
5. Orchestration: Custom RAG (not Agents SDK) for maximum control

**Phase 1: Design** - 3 artifacts created:
1. data-model.md: 6 entities (BookContentChunk, UserQuery, TextSelection, RetrievedPassage, ChatbotResponse, Session) with full validation rules
2. contracts/api.openapi.yaml: OpenAPI 3.0 spec with 6 endpoints (query, query/selected, session CRUD, health, admin/ingest)
3. quickstart.md: Developer onboarding guide with Docker Compose setup, ingestion CLI, API testing examples

**Project Structure**: Backend API service with organized src/ layout (api/, models/, services/, db/, core/, cli/) and comprehensive test structure (contract/, integration/, unit/)

## Outcome

- ✅ Impact: Complete implementation plan with architecture, research decisions, data model, API contracts, and developer guide
- 🧪 Tests: N/A (planning phase - tests will be defined in /sp.tasks)
- 📁 Files: plan.md, research.md, data-model.md, contracts/api.openapi.yaml, quickstart.md, CLAUDE.md updated
- 🔁 Next prompts: /sp.tasks (generate actionable task breakdown organized by user story priority)
- 🧠 Reflection: Architecture aligns with constitution, research resolves all technical unknowns, ready for task generation

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - Constitution check passed all 6 principles, research decisions documented with rationale/alternatives, data model complete with validation rules, API contracts comprehensive
- Prompt variant (if applicable): N/A (initial planning)
- Next experiment (smallest change to try): Validate task generation aligns with user story priorities (P1: Full book queries, P2: Selected text, P3: Traceability)
