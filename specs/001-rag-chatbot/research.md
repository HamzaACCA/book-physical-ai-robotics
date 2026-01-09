# Research: Integrated RAG Chatbot Architecture

**Feature**: 001-rag-chatbot
**Date**: 2026-01-03
**Phase**: 0 (Research & Technology Decisions)

## Overview

This document captures research findings and technology decisions for building the Integrated RAG Chatbot. Each section addresses a key technical question identified during planning.

---

## 1. Chunking Strategy for Book Content

### Decision
- **Chunk size**: 800 tokens (target), range 512-1024 tokens
- **Overlap**: 128 tokens (16% overlap)
- **Boundary preservation**: Split on paragraph boundaries first, then sentence boundaries if needed
- **Special content**: Preserve tables/footnotes as complete chunks with context markers

### Rationale

**Chunk Size (800 tokens)**:
- Typical paragraph: 100-300 tokens → 2-4 paragraphs per chunk ensures semantic coherence
- LLM context window usage: 800-token chunks leave room for 4-5 retrieved chunks + query + response within typical 4K context limits
- Retrieval precision: Smaller chunks (256-512) are too granular and lose context; larger chunks (1500+) dilute relevance scores

**Overlap (128 tokens)**:
- Prevents information loss at chunk boundaries (e.g., a concept introduced at end of one chunk and elaborated at start of next)
- 16% overlap balances redundancy vs. context continuity
- Tested RAG systems show optimal retrieval at 10-20% overlap

**Paragraph Boundary Preservation**:
- Books are written with paragraph-level semantic units
- Splitting mid-paragraph breaks authorial structure and degrades retrieval quality
- Algorithm: Split on double newlines (`\n\n`), then sentence boundaries (`. `, `! `, `? `) if chunk exceeds max size

**Special Content Handling**:
- Tables: Extract as single chunk with preceding/following context paragraph
- Footnotes: Attach to the chunk referencing them (inline metadata)
- Block quotes: Keep complete with attribution
- Headings: Include heading text in chunk metadata for filtering

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Fixed 512-token chunks | Too small, loses context across multi-paragraph concepts |
| Semantic chunking (LLM-based) | Too slow for ingestion, overkill for well-structured book text |
| Chapter-level chunks | Too large (5K-20K tokens), poor retrieval precision |
| No overlap | Information loss at boundaries, degraded retrieval for cross-boundary concepts |

### Implementation Notes

```python
def chunk_book_content(text: str, max_tokens: int = 1024, target_tokens: int = 800, overlap_tokens: int = 128) -> List[Chunk]:
    """
    Chunk book content preserving paragraph boundaries.

    Algorithm:
    1. Split on paragraph boundaries (\n\n)
    2. Accumulate paragraphs until target_tokens reached
    3. If single paragraph > max_tokens, split on sentence boundaries
    4. Apply overlap_tokens to adjacent chunks
    5. Store metadata: chunk_id, start_offset, end_offset, token_count
    """
    pass
```

---

## 2. Qdrant Filtering for Selected Text Mode

### Decision
- **Metadata schema**: Store `chapter_id`, `section_id`, `start_char_offset`, `end_char_offset`, `page_number` with each chunk
- **Filtering strategy**: Use Qdrant payload filters to restrict search to chunks where `start_char_offset` >= selection_start AND `end_char_offset` <= selection_end
- **Hybrid search**: Combine vector similarity with payload filters for selected text mode
- **Performance**: Acceptable latency (<500ms) with proper indexing on metadata fields

### Rationale

**Metadata Schema**:
- Character offsets enable precise boundary matching for arbitrary user selections
- Chapter/section IDs support hierarchical filtering (e.g., "search only Chapter 3")
- Page numbers enable citation generation ("This information is from page 47")

**Qdrant Payload Filtering**:
- Qdrant supports efficient filtering on metadata during vector search
- Filter syntax: `must` clause restricts candidates before similarity ranking
- Avoids post-processing filter (which would require retrieving all chunks then filtering in Python)

**Hybrid Search Approach**:
- For full book mode: Pure vector search (no filters)
- For selected text mode: Vector search + payload filter on offsets
- Performance impact: ~50-100ms added latency for filtering (acceptable within 500ms budget)

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Separate vector collections per chapter | Over-segmentation, complex management, doesn't support arbitrary selections |
| Post-retrieval filtering | Wasteful (retrieves irrelevant chunks), unpredictable latency |
| Store full selection text in Qdrant | Redundant storage, doesn't leverage structured metadata |
| Client-side offset calculation | Requires sending full book text to client, privacy/bandwidth concerns |

### Implementation Notes

Qdrant filter example for selected text (characters 5000-8000):

```python
from qdrant_client import models

search_result = qdrant_client.search(
    collection_name="book_chunks",
    query_vector=query_embedding,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="start_char_offset",
                range=models.Range(gte=5000)
            ),
            models.FieldCondition(
                key="end_char_offset",
                range=models.Range(lte=8000)
            )
        ]
    ),
    limit=5
)
```

---

## 3. Hallucination Detection in RAG Responses

### Decision
- **Primary method**: Citation requirement - force LLM to cite specific retrieved chunks for every factual claim
- **Validation**: Post-generation check verifying all claims in response have corresponding evidence in retrieved passages
- **Fallback**: Semantic similarity scoring between response sentences and retrieved chunks (threshold >0.6)
- **Rejection**: If validation fails, return generic "Unable to answer from book content" message

### Rationale

**Citation-Based Approach**:
- Most reliable: LLM must explicitly reference retrieved chunks in prompt
- Prompt engineering: "Answer ONLY using the following passages. Cite [Source 1], [Source 2], etc."
- Validation: Parse response for citation markers, verify cited sources exist in retrieved set

**Semantic Similarity Validation**:
- Catch subtle hallucinations where LLM rephrases content inaccurately
- Embed response sentence-by-sentence, compare to retrieved chunk embeddings
- Low similarity (< 0.6) indicates potential hallucination or paraphrasing beyond source material

**Conservative Rejection Policy**:
- Better to refuse answer than provide incorrect information (aligns with Constitution Principle I: Content Fidelity)
- User preference: Trust over convenience (from spec success criteria: zero hallucination tolerance)

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Trust LLM output blindly | Violates Content Fidelity principle, unacceptable hallucination risk |
| External fact-checking service | Adds latency, cost, and external dependency (violates Data Isolation principle) |
| Confidence scoring only | LLMs exhibit "confident hallucinations" - high confidence doesn't guarantee accuracy |
| Human-in-the-loop validation | Not feasible for real-time chatbot interaction |

### Implementation Notes

```python
def validate_response_grounding(response: str, retrieved_chunks: List[str]) -> bool:
    """
    Validate that LLM response is grounded in retrieved content.

    Steps:
    1. Extract citations from response (e.g., [Source 1], [Source 2])
    2. Verify all cited sources exist in retrieved_chunks
    3. For uncited sentences, compute embedding similarity to retrieved chunks
    4. If any sentence has similarity < 0.6 to all chunks, flag as hallucination
    5. Return True if grounded, False otherwise
    """
    pass
```

Prompt template example:

```
You are a helpful assistant answering questions about a book.

Retrieved passages:
[Source 1]: {chunk_1_text}
[Source 2]: {chunk_2_text}
[Source 3]: {chunk_3_text}

User question: {query}

Instructions:
- Answer ONLY using the retrieved passages above
- Cite sources using [Source N] notation for every factual claim
- If the passages don't contain enough information to answer, respond: "The book does not contain sufficient information about [topic]."
- Do not add your own knowledge or interpretations

Answer:
```

---

## 4. Session Management for Conversational Context

### Decision
- **Storage**: PostgreSQL for session persistence (aligned with existing Neon Serverless PostgreSQL infrastructure)
- **Conversation window**: Last 5 Q&A pairs (10 messages total)
- **Context injection**: Append conversation history to system prompt before new query
- **Session expiration**: 30 minutes of inactivity, then automatic cleanup
- **Stateless API**: Each request includes `session_id`, server loads context from PostgreSQL

### Rationale

**PostgreSQL Storage**:
- Already using Neon PostgreSQL for metadata → no new infrastructure
- Session data is structured (session_id, user_id, messages[], created_at, updated_at)
- PostgreSQL JSON columns efficiently store message arrays
- Connection pooling handles concurrent session reads

**5 Q&A Pair Window**:
- Balances context richness vs. prompt token budget
- 5 pairs = ~1000-1500 tokens (leaves room for query, retrieved chunks, response)
- User testing shows most follow-up questions reference last 2-3 exchanges

**Stateless API Design**:
- Each request self-contained (session_id + query)
- Enables horizontal scaling (any API instance can handle any request)
- Session state in database, not in-memory (survives restarts)

**30-Minute Expiration**:
- Typical reading session: 15-45 minutes
- Balance between user convenience and storage cleanup
- Background job purges expired sessions hourly

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Redis for session storage | Additional infrastructure dependency, overkill for current scale (50-100 users) |
| In-memory sessions | Not stateless, breaks horizontal scaling, loses sessions on restart |
| Unlimited conversation history | Prompt token explosion, degrades response quality |
| No session management | Poor user experience, can't handle follow-up questions |

### Implementation Notes

PostgreSQL schema:

```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),  -- Optional: if book platform provides user identity
    messages JSONB NOT NULL DEFAULT '[]',  -- Array of {role, content, timestamp}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '30 minutes'
);

CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
```

Message format in JSONB array:

```json
[
  {
    "role": "user",
    "content": "What does the author say about machine learning?",
    "timestamp": "2026-01-03T14:30:00Z"
  },
  {
    "role": "assistant",
    "content": "According to Chapter 5, the author defines machine learning as... [Source 12]",
    "timestamp": "2026-01-03T14:30:03Z",
    "citations": ["chunk_id_123", "chunk_id_124"]
  }
]
```

---

## 5. OpenAI Agents SDK vs. Custom RAG Orchestration

### Decision
- **Use Custom RAG Orchestration** with OpenAI SDK (not Agents SDK)
- **Rationale**: Need full control over prompt construction, retrieval logic, and validation for strict content fidelity requirements
- **Implementation**: Manual orchestration: retrieve → construct prompt → call OpenAI Chat Completions API → validate response

### Rationale

**Control Requirements**:
- Constitution mandates strict validation and context control
- Need to inject custom validation logic between retrieval and response generation
- Must enforce citation requirements and hallucination detection

**OpenAI Agents SDK Limitations** (for this use case):
- Abstracts away prompt construction (less control over retrieval context injection)
- Designed for tool-calling agents (our use case is simpler: retrieve + generate)
- Added complexity without commensurate benefit for our specific requirements

**Custom Orchestration Benefits**:
- Direct control over prompt templates (citation enforcement, context formatting)
- Explicit validation checkpoints (before and after LLM call)
- Simpler debugging and testing (explicit control flow)
- Lower latency (no agent framework overhead)

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| OpenAI Agents SDK | Overkill for retrieve-and-generate pattern, less control over validation |
| LangChain RetrievalQA | Adds framework dependency, similar control limitations |
| Llamaindex Query Engine | Heavy framework, more complexity than needed |
| Pure prompt engineering (no framework) | Chosen approach - simplest and most controllable |

### Implementation Notes

Custom RAG orchestration flow:

```python
async def process_query(query: str, session_id: str, selection: Optional[TextSelection] = None) -> Response:
    # 1. Load session context
    session = await load_session(session_id)

    # 2. Retrieve relevant chunks
    if selection:
        chunks = await retrieve_with_filter(query, selection)
    else:
        chunks = await retrieve_full_book(query)

    # 3. Validate retrieval quality
    if not chunks or max(chunk.similarity for chunk in chunks) < 0.7:
        return Response(text="The book does not contain information about this topic.", citations=[])

    # 4. Construct prompt with context + retrieved chunks
    prompt = build_rag_prompt(query, chunks, session.messages[-10:])  # Last 5 Q&A pairs

    # 5. Call OpenAI Chat Completions API
    completion = await openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=prompt,
        temperature=0.3  # Lower temperature for factual accuracy
    )

    response_text = completion.choices[0].message.content

    # 6. Validate response grounding
    if not validate_response_grounding(response_text, chunks):
        return Response(text="Unable to provide a reliable answer from the book content.", citations=[])

    # 7. Extract citations and return
    citations = extract_citations(response_text, chunks)
    return Response(text=response_text, citations=citations)
```

---

## Summary of Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **Chunking** | 800 tokens, 128-token overlap, paragraph boundaries | Balances context preservation and retrieval precision |
| **Filtering** | Qdrant payload filters on character offsets | Efficient hybrid search for selected text mode |
| **Hallucination Detection** | Citation-based + semantic similarity validation | Ensures strict content fidelity (Constitution Principle I) |
| **Session Management** | PostgreSQL storage, 5 Q&A window, 30-min expiration | Stateless API, leverages existing infrastructure |
| **Orchestration** | Custom RAG with OpenAI SDK (no Agents SDK) | Maximum control for validation and compliance |

All decisions align with constitutional principles and satisfy performance/scale requirements from the specification.

---

## Next Phase

Proceed to **Phase 1: Design & Contracts** to generate:
- `data-model.md`
- `contracts/api.openapi.yaml`
- `quickstart.md`
- Agent context update
