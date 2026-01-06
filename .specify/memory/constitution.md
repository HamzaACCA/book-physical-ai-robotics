<!--
Sync Impact Report:
Version: 0.0.0 → 1.0.0
Change Summary: Initial constitution creation for Integrated RAG Chatbot project
Modified Principles: All principles created from template
Added Sections:
  - Core Principles (6 principles)
  - Technical Architecture
  - Development Workflow
  - Governance
Removed Sections: N/A (initial creation)
Templates Status:
  ✅ plan-template.md: Constitution Check section already generic (no updates needed)
  ✅ spec-template.md: Requirements and success criteria align with Content Fidelity and Accuracy principles
  ✅ tasks-template.md: Test-first approach aligns with constitution validation requirements
Follow-up TODOs: None
-->

# Integrated RAG Chatbot Constitution

## Core Principles

### I. Content Fidelity
All responses MUST be generated exclusively from retrieved book content stored in the vector database. The chatbot MUST NOT hallucinate, infer, or fabricate information beyond what exists in the retrieved text. If an answer cannot be derived from the retrieved content, the system MUST explicitly state that the information is not available in the book.

**Rationale**: Ensures users receive accurate information directly from the source material, maintaining trust and preventing misinformation. This principle protects the author's intent and the integrity of the published work.

### II. User-Controlled Context
When a user selects specific text within the book, the chatbot MUST restrict its responses strictly to the selected content. No information outside the user's selection may be used in response generation. The system MUST provide two distinct retrieval modes: (1) Full book retrieval for general questions, and (2) Selection-only retrieval for targeted queries.

**Rationale**: Empowers users to control the scope of analysis and ensures responses remain relevant to their current reading context. This prevents confusion from mixing different sections of the book.

### III. Transparency and Traceability
Every response MUST be backed by specific retrieved passages stored in the vector database to ensure auditability. The system MUST maintain a clear audit trail linking responses to source chunks. When unable to answer from available content, the chatbot MUST provide a clear explanation rather than speculation.

**Rationale**: Enables users and administrators to verify response accuracy and trace information back to the original source. Critical for building confidence in the system and debugging response quality issues.

### IV. Accuracy and Retrieval Quality
The RAG pipeline MUST implement semantic search using embeddings to ensure relevant passage retrieval. Chunking strategies MUST preserve context and meaning (no mid-sentence splits without overlap). Retrieved passages MUST be ranked by relevance, and the system MUST only use top-k results that meet a minimum similarity threshold.

**Rationale**: High-quality retrieval is the foundation of accurate responses. Poor chunking or irrelevant retrievals directly degrade response quality and user experience.

### V. Security and Data Isolation
Only the published book's content shall be ingested into the vector database. User queries and selected text shall be processed securely without logging sensitive personal information. No external data sources shall be accessed during response generation. API keys, database credentials, and secrets MUST be stored in environment variables and never committed to version control.

**Rationale**: Protects user privacy, maintains data integrity, and ensures system responses remain scoped to authorized content only.

### VI. Scope Boundaries
The chatbot shall NOT answer questions unrelated to the book content. The chatbot shall NOT provide professional advice (legal, medical, financial) unless such advice is explicitly quoted from the book with clear attribution. The chatbot shall NOT alter, reinterpret, or editorialize the author's original meaning—responses must reflect the source material faithfully.

**Rationale**: Prevents scope creep, liability issues, and misrepresentation of the author's work. Establishes clear boundaries for system capabilities and user expectations.

## Technical Architecture

The chatbot MUST be implemented using the following technology stack:

- **Conversational Logic**: FastAPI with custom conversation management for agentic workflows
- **Backend API**: FastAPI for RESTful endpoints and WebSocket support
- **Structured Data**: Neon Serverless PostgreSQL for session management, user state, and metadata
- **Vector Storage**: Qdrant Cloud (Free Tier) for embeddings storage and semantic search
- **Embeddings**: Google Gemini `text-embedding-004` (768 dimensions) for vector generation
- **LLM**: Google Gemini `gemini-1.5-flash` or `gemini-1.5-pro` for response generation

**Architecture Constraints**:
- Vector database queries MUST complete within 500ms p95 latency
- API responses (including LLM generation) MUST complete within 3 seconds p95
- The system MUST handle concurrent users gracefully (target: 50+ simultaneous sessions)
- All retrieval operations MUST be idempotent and stateless

**Deployment Requirements**:
- Backend MUST be containerized (Docker) for consistent deployment
- Vector database MUST be cloud-hosted with automated backups
- PostgreSQL MUST support connection pooling for session management
- Environment-specific configurations MUST be externalized via `.env` files

## Development Workflow

### Test-First Development
All new features MUST follow a test-first approach:
1. Write acceptance tests based on user scenarios in the specification
2. Ensure tests FAIL before implementation (red phase)
3. Implement minimal code to pass tests (green phase)
4. Refactor for clarity and performance while keeping tests passing

**Rationale**: Ensures all features are testable, reduces regression risk, and validates requirements before implementation effort.

### Code Review and Quality Gates
All code changes MUST pass:
- Linting (ruff for Python, eslint for JavaScript/TypeScript)
- Type checking (mypy for Python, TypeScript strict mode)
- Unit tests (minimum 80% coverage for core logic)
- Integration tests for API endpoints and RAG pipeline
- Manual review by at least one other developer

**Rationale**: Maintains code quality, catches bugs early, and ensures knowledge sharing across the team.

### Chunking and Ingestion Standards
Book content ingestion MUST follow these rules:
- Chunk size: 512-1024 tokens with 128-token overlap
- Preserve paragraph boundaries; avoid mid-sentence splits
- Store metadata: chapter, section, page number, heading hierarchy
- Generate embeddings immediately after chunking
- Validate chunk quality: no empty chunks, no encoding errors

**Rationale**: Consistent chunking ensures reliable retrieval and prevents context loss. Metadata enables advanced filtering and source attribution.

### Response Validation
Before returning responses to users, the system MUST:
- Verify that retrieved passages meet minimum similarity threshold (>0.7 cosine similarity)
- Validate that the LLM response references retrieved content
- Check for hallucination indicators (e.g., claiming specific facts not in retrieved chunks)
- Log retrieval quality metrics for monitoring

**Rationale**: Prevents low-quality or fabricated responses from reaching users. Enables continuous improvement through metric tracking.

## Governance

This constitution supersedes all other practices and serves as the authoritative source for project principles. All pull requests, code reviews, and design decisions MUST verify compliance with the principles defined above.

**Amendment Process**:
1. Proposed changes MUST be documented with rationale and impact analysis
2. Amendments require approval from project lead or designated constitution owner
3. Version MUST be incremented following semantic versioning:
   - **MAJOR**: Breaking changes to core principles (e.g., removing Content Fidelity requirement)
   - **MINOR**: New principles or significant expansions (e.g., adding new security requirements)
   - **PATCH**: Clarifications, wording improvements, or non-semantic updates
4. All dependent templates (spec, plan, tasks) MUST be reviewed and updated for consistency

**Complexity Justification**:
Any violations of simplicity principles (YAGNI, minimal dependencies, smallest viable change) MUST be explicitly justified in the implementation plan with:
- Why the additional complexity is necessary
- What simpler alternatives were considered and rejected
- Measurable criteria for success

**Compliance Review**:
- Constitution compliance MUST be verified at each phase gate (spec → plan → tasks → implementation)
- The `/sp.plan` command MUST include a "Constitution Check" section validating alignment
- Architectural decisions MUST be documented in ADRs when they affect multiple principles

**Version**: 1.1.0 | **Ratified**: 2026-01-03 | **Last Amended**: 2026-01-06
**Amendment Notes**:
- v1.1.0 (2026-01-06): Updated technology stack to use Google Gemini instead of OpenAI for embeddings and LLM generation (free tier with similar capabilities)
