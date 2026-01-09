"""Application configuration using pydantic settings."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI Configuration (Primary)
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    openai_llm_model: str = Field(default="gpt-4o-mini")
    openai_temperature: float = Field(default=0.3, ge=0.0, le=2.0)

    # Google Gemini Configuration (Fallback)
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_embedding_model: str = Field(default="models/text-embedding-004")
    gemini_llm_model: str = Field(default="gemini-2.0-flash-exp")
    gemini_temperature: float = Field(default=0.3, ge=0.0, le=2.0)

    # Qdrant Configuration
    qdrant_url: str = Field(..., description="Qdrant cluster URL")
    qdrant_api_key: str = Field(..., description="Qdrant API key")
    qdrant_collection_name: str = Field(default="book_chunks")
    qdrant_vector_size: int = Field(default=1536)  # OpenAI text-embedding-3-small dimensions

    # PostgreSQL Configuration
    database_url: str = Field(..., description="PostgreSQL connection URL")
    database_pool_min_size: int = Field(default=2)
    database_pool_max_size: int = Field(default=10)

    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, validation_alias="PORT")  # Support Railway's PORT env var
    api_reload: bool = Field(default=False)
    api_workers: int = Field(default=1)
    api_cors_origins: List[str] = Field(default=["http://localhost:3000"])

    # Admin Configuration
    admin_api_key: str = Field(..., description="Admin API key for ingestion")

    # Application Settings
    log_level: str = Field(default="INFO")
    chunk_size_tokens: int = Field(default=800, ge=512, le=1024)
    chunk_overlap_tokens: int = Field(default=128, ge=0, le=256)
    min_similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    session_expiration_minutes: int = Field(default=30, ge=1)
    max_conversation_messages: int = Field(default=10, ge=2)
    max_retrieved_chunks: int = Field(default=5, ge=1, le=10)

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=100, ge=1)


# Global settings instance
settings = Settings()
