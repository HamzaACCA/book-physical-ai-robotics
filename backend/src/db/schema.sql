-- Database schema for RAG Chatbot
-- PostgreSQL schema definition

-- Book chunks table (metadata only, embeddings in Qdrant)
CREATE TABLE IF NOT EXISTS book_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL,
    text_content TEXT NOT NULL,
    token_count INTEGER NOT NULL CHECK (token_count BETWEEN 512 AND 1024),
    chapter_id VARCHAR(255),
    chapter_title VARCHAR(500),
    section_id VARCHAR(255),
    section_title VARCHAR(500),
    page_number INTEGER CHECK (page_number >= 1),
    start_char_offset INTEGER NOT NULL CHECK (start_char_offset >= 0),
    end_char_offset INTEGER NOT NULL CHECK (end_char_offset > start_char_offset),
    heading_hierarchy TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_offsets CHECK (end_char_offset > start_char_offset)
);

CREATE INDEX idx_book_chunks_book_id ON book_chunks(book_id);
CREATE INDEX idx_book_chunks_chapter_id ON book_chunks(chapter_id);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    messages JSONB NOT NULL DEFAULT '[]',
    active_retrieval_mode VARCHAR(50) NOT NULL DEFAULT 'FULL_BOOK' CHECK (active_retrieval_mode IN ('FULL_BOOK', 'SELECTED_TEXT')),
    current_selection_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '30 minutes')
);

CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- User queries table
CREATE TABLE IF NOT EXISTS user_queries (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    query_text TEXT NOT NULL CHECK (LENGTH(TRIM(query_text)) > 0),
    retrieval_mode VARCHAR(50) NOT NULL CHECK (retrieval_mode IN ('FULL_BOOK', 'SELECTED_TEXT')),
    text_selection_id UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_queries_session_id ON user_queries(session_id);
CREATE INDEX idx_user_queries_created_at ON user_queries(created_at);

-- Text selections table
CREATE TABLE IF NOT EXISTS text_selections (
    selection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    selected_text TEXT NOT NULL CHECK (LENGTH(selected_text) > 0 AND LENGTH(selected_text) <= 50000),
    start_char_offset INTEGER NOT NULL CHECK (start_char_offset >= 0),
    end_char_offset INTEGER NOT NULL CHECK (end_char_offset > start_char_offset),
    chapter_id VARCHAR(255),
    page_range_start INTEGER CHECK (page_range_start >= 1),
    page_range_end INTEGER CHECK (page_range_end >= page_range_start),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_selection_offsets CHECK (end_char_offset > start_char_offset)
);

-- Retrieved passages table (audit trail)
CREATE TABLE IF NOT EXISTS retrieved_passages (
    retrieval_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL REFERENCES user_queries(query_id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES book_chunks(chunk_id) ON DELETE CASCADE,
    similarity_score FLOAT NOT NULL CHECK (similarity_score BETWEEN 0.0 AND 1.0),
    rank INTEGER NOT NULL CHECK (rank >= 1),
    retrieved_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_retrieved_passages_query_id ON retrieved_passages(query_id);
CREATE INDEX idx_retrieved_passages_chunk_id ON retrieved_passages(chunk_id);
CREATE INDEX idx_retrieved_passages_similarity ON retrieved_passages(similarity_score DESC);

-- Chatbot responses table
CREATE TABLE IF NOT EXISTS chatbot_responses (
    response_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL REFERENCES user_queries(query_id) ON DELETE CASCADE,
    response_text TEXT NOT NULL CHECK (LENGTH(response_text) > 0),
    citations JSONB NOT NULL,
    retrieval_quality FLOAT NOT NULL CHECK (retrieval_quality BETWEEN 0.0 AND 1.0),
    validation_passed BOOLEAN NOT NULL,
    validation_notes TEXT,
    llm_model VARCHAR(255) NOT NULL,
    llm_tokens_used INTEGER CHECK (llm_tokens_used >= 0),
    latency_ms INTEGER CHECK (latency_ms >= 0),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chatbot_responses_query_id ON chatbot_responses(query_id);

-- Function to auto-update session updated_at and expires_at
CREATE OR REPLACE FUNCTION update_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.expires_at = NOW() + INTERVAL '30 minutes';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_session_timestamp
BEFORE UPDATE ON sessions
FOR EACH ROW
EXECUTE FUNCTION update_session_timestamp();
