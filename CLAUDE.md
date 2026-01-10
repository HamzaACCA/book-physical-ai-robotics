# Physical AI & Humanoid Robotics - RAG Chatbot

## Project Overview
A RAG (Retrieval-Augmented Generation) chatbot for the "Physical AI & Humanoid Robotics" book/course. Users can ask questions and get answers based on the book content.

## Tech Stack
- **Backend**: Python 3.11+ / FastAPI
- **LLM**: OpenAI GPT-4o-mini
- **Embeddings**: OpenAI text-embedding-3-small (1536 dims)
- **Vector DB**: Qdrant Cloud
- **Database**: Neon Serverless PostgreSQL
- **Frontend**: Docusaurus + Custom Chat Widget
- **Hosting**: Railway (backend) + GitHub Pages (frontend)

## Deployment Configuration

### Production URLs
- **Backend API**: https://book-physical-ai-robotics-production.up.railway.app
- **Frontend**: https://hamzaacca.github.io/book-physical-ai-robotics/
- **Health Check**: GET /health

### Database (PostgreSQL - Neon)
- **Host**: ep-patient-tree-adr5pn76-pooler.c-2.us-east-1.aws.neon.tech
- **Tables**: book_chunks, sessions, books
- **Chunks**: 16 (600 tokens, 200 overlap)

### Vector Database (Qdrant Cloud)
- **Collection**: `book_chunks`
- **Dimensions**: 1536
- **Points**: 16
- **Distance**: Cosine

### Railway Environment Variables
```
OPENAI_API_KEY=sk-proj-...
QDRANT_URL=https://...qdrant.io
QDRANT_API_KEY=...
QDRANT_COLLECTION_NAME=book_chunks
QDRANT_VECTOR_SIZE=1536
DATABASE_URL=postgresql://...
```

### API Endpoints
- `POST /api/v1/chat/message` - Send chat message
- `POST /api/v1/chat/session` - Create new session
- `GET /api/v1/chat/history/{session_id}` - Get chat history
- `GET /health` - Health check

### Chat Response Format
```json
{
  "answer": "Response with **bold headings** and book content",
  "session_id": "uuid"
}
```

## RAG Pipeline

### Retrieval Flow
1. User query → OpenAI embedding (1536 dims)
2. Vector search in Qdrant (cosine similarity)
3. Filter by similarity threshold (0.25)
4. Fetch chunk metadata from PostgreSQL
5. Build context from top 3 chunks
6. Generate response with GPT-4o-mini

### Configuration
| Setting | Value |
|---------|-------|
| Embedding Model | text-embedding-3-small |
| LLM Model | gpt-4o-mini |
| Temperature | 0.3 |
| Max Tokens | 800 |
| Similarity Threshold | 0.25 |
| Top K Chunks | 3 |
| Chunk Size | 600 tokens |
| Chunk Overlap | 200 tokens |

### LLM Prompt
- Strict instructions: Use ONLY book content, no hallucination
- Format: Bold headings, bullet points, structured paragraphs
- Context: Retrieved chunks + conversation history

### Key Files
| File | Purpose |
|------|---------|
| `backend/src/services/chat.py` | Main RAG logic |
| `backend/src/services/retrieval.py` | Vector search |
| `backend/src/db/qdrant.py` | Qdrant client |
| `backend/src/db/postgres.py` | PostgreSQL connection |
| `backend/src/cli/ingest.py` | Book ingestion |
| `backend/src/api/routes/chat.py` | API endpoints |

## Frontend Chat Widget

### File Location
- `static/chat-widget.js` - Self-contained widget
- `docusaurus.config.js` - Loads widget script

### Widget Structure
```
┌─────────────────────────────┐
│  Chat Header                │  Title + Close button
├─────────────────────────────┤
│  Messages Area              │  Bot/User messages
│  - Markdown rendered        │  Typing indicator
├─────────────────────────────┤
│  Input Area                 │  Text input + Send
└─────────────────────────────┘
     [Floating Button]           Bottom-right
```

### Features
- Session persistence (localStorage)
- Chat history loading
- Markdown rendering (marked.js + fallback)
- Typing indicator (animated dots)
- Responsive design (mobile-friendly)

### Styling
- Colors: Purple gradient (#667eea → #764ba2)
- Bot messages: White background
- User messages: Purple gradient, white text
- Bold text: `<strong>` tags

### Markdown Support
- `**bold**` → `<strong>`
- Double newline → `<p>` paragraphs
- Single newline → `<br>`
- Lists via marked.js

## Project Structure
```
├── backend/
│   └── src/
│       ├── api/routes/     # FastAPI endpoints
│       ├── services/       # RAG, chat, ingestion
│       ├── db/             # Qdrant, PostgreSQL
│       └── core/           # Config, logging
├── static/
│   └── chat-widget.js      # Frontend widget
├── docs/                   # Docusaurus content
├── physical-ai-robotics-book.md  # Source book
└── .env                    # Environment variables
```
