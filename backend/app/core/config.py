"""Application settings, loaded from environment variables (and a local .env file)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    # OpenAI
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "my_notebook"

    # Storage: a local folder. In production (Cloud Run) it is a GCS bucket
    # mounted as a folder (Cloud Storage FUSE), so the code does not change.
    local_upload_dir: str = "../data/uploads"

    # Local ML models (FlashRank reranker), downloaded on first use
    model_cache_dir: str = "../data/models"

    # Security
    app_api_key: str = ""

    # App
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Cached so the .env file is read once per process."""
    return Settings()
