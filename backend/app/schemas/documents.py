"""API models for uploaded documents."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"  # raw file stored, not chunked yet
    INDEXED = "indexed"  # chunked + embedded + stored in Qdrant
    FAILED = "failed"  # ingestion error (see `error`)


class DocumentMeta(BaseModel):
    id: str
    filename: str
    content_type: str | None = None
    size_bytes: int
    status: DocumentStatus = DocumentStatus.UPLOADED
    uploaded_at: datetime
    chunk_count: int | None = None
    error: str | None = None
