-- Books table for tracking published books
CREATE TABLE IF NOT EXISTS books (
    book_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    author VARCHAR(255),
    description TEXT,
    github_repo_name VARCHAR(255) NOT NULL UNIQUE,
    github_repo_url TEXT NOT NULL,
    live_site_url TEXT,
    deployment_status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (deployment_status IN ('pending', 'deploying', 'deployed', 'failed')),
    github_actions_run_id BIGINT,
    chunks_count INTEGER DEFAULT 0,
    total_characters INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),
    deployed_at TIMESTAMP,
    CONSTRAINT valid_chunks_count CHECK (chunks_count >= 0)
);

CREATE INDEX idx_books_deployment_status ON books(deployment_status);
CREATE INDEX idx_books_created_at ON books(created_at DESC);
CREATE INDEX idx_books_github_repo_name ON books(github_repo_name);

-- Update last_updated timestamp on book updates
CREATE OR REPLACE FUNCTION update_book_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_book_timestamp
BEFORE UPDATE ON books
FOR EACH ROW
EXECUTE FUNCTION update_book_timestamp();
