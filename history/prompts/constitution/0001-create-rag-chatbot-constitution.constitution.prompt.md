---
id: 0001
title: Create RAG Chatbot Constitution
stage: constitution
date: 2026-01-03
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: master
user: Hamza
command: /sp.constitution
labels: ["constitution", "rag-chatbot", "principles", "governance"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A (constitution document, no executable tests)
---

## Prompt

```text
# Constitution: Integrated RAG Chatbot

## Purpose
# This constitution defines the rules, principles, and boundaries for the
# development of an Integrated Retrieval-Augmented Generation (RAG) chatbot
# embedded within a published book.
# The chatbot must answer questions strictly based on the book's content.

## Scope
# The chatbot shall be embedded within the digital version of the book.
# It shall allow users to ask questions about the book.
# The chatbot must support answering questions based on:
# - The full book content
# - Only the text explicitly selected by the user
# The chatbot shall not use external or unrelated information.

## Core Principles

### Content Fidelity
# All responses must be generated only from retrieved book content.
# The chatbot must not hallucinate, infer, or fabricate information
# beyond what exists in the retrieved text.

### User-Controlled Context
# When a user selects specific text, the chatbot must restrict
# its responses strictly to the selected content.
# No information outside the selection may be used.

### Transparency
# If an answer cannot be derived from the retrieved or selected text,
# the chatbot must clearly state that the information is not available.

### Accuracy and Traceability
# Every response must be backed by retrieved passages
# stored within the vector database to ensure auditability.

## Technical Architecture
# The chatbot shall be implemented using:
# - OpenAI Agents / Gemini Agent / ChatKit SDKs for conversational logic
# - FastAPI for backend API services
# - Neon Serverless PostgreSQL for structured data and session management
# - Qdrant Cloud (Free Tier) for vector storage and semantic retrieval

## Data Handling and Security
# Only the published book's content shall be ingested into the system.
# User queries and selected text shall be processed securely.
# No external data sources shall be accessed during response generation.

## System Limitations
# The chatbot shall not answer questions unrelated to the book.
# The chatbot shall not provide professional advice unless explicitly
# stated within the book.
# The chatbot shall not alter or reinterpret the author's original meaning.

## Compliance
# This constitution governs all phases of development and deployment.
# Any system changes must comply with the principles defined above.
```

## Response snapshot

Created the Integrated RAG Chatbot Constitution v1.0.0 with 6 core principles:

1. **Content Fidelity**: Responses must come exclusively from retrieved book content, no hallucination
2. **User-Controlled Context**: Support both full-book and selection-only retrieval modes
3. **Transparency and Traceability**: All responses backed by retrievable passages with audit trails
4. **Accuracy and Retrieval Quality**: Semantic search with quality chunking (512-1024 tokens, 128-token overlap)
5. **Security and Data Isolation**: Book content only, no external sources, secrets in env vars
6. **Scope Boundaries**: No unrelated questions, no professional advice, faithful to author's meaning

Technical stack specified: OpenAI Agents/ChatKit, FastAPI, Neon PostgreSQL, Qdrant Cloud, with performance constraints (500ms p95 retrieval, 3s p95 API response).

Development workflow includes test-first development, code quality gates (80% coverage), chunking standards, and response validation (>0.7 cosine similarity threshold).

Governance section defines amendment process with semantic versioning, complexity justification requirements, and phase-gate compliance checks.

## Outcome

- ✅ Impact: Project constitution established from template, all placeholders resolved, 6 core principles defined
- 🧪 Tests: N/A (constitution is a governance document)
- 📁 Files: Created .specify/memory/constitution.md (v1.0.0)
- 🔁 Next prompts: /sp.specify to create feature specification, /sp.plan for architecture planning
- 🧠 Reflection: Constitution successfully maps RAG chatbot requirements to testable principles with clear technical constraints

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - All template placeholders filled, no bracketed tokens remaining, principles are declarative and testable
- Prompt variant (if applicable): N/A (initial creation)
- Next experiment (smallest change to try): Validate constitution check alignment when running /sp.plan command
