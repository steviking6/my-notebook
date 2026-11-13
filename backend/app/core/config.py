"""Application settings, loaded from environment variables (and a local .env file)."""

from functools import lru_cache
from typing import Literal

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

    # Storage
    storage_backend: Literal["local", "gcs"] = "local"
    local_upload_dir: str = "../data/uploads"
    gcs_bucket: str = ""

    # Chunking (characters, not tokens: ~1200 chars is roughly 250-300 tokens)
    chunk_max_chars: int = 1200  # hard limit per chunk
    chunk_new_after_chars: int = 1000  # soft limit: start a new chunk after this
    chunk_overlap_chars: int = 150  # overlap when a long element has to be split
    chunk_combine_under_chars: int = 200  # merge tiny sections (e.g. a lone title)

    # Security
    app_api_key: str = ""

    # App
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached so the .env file is read once per process."""
    return Settings()
