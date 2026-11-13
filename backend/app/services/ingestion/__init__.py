"""Ingestion: raw file -> Unstructured elements -> chunks."""

from app.core.config import Settings
from app.services.ingestion.chunker import Chunk, chunk_document
from app.services.ingestion.loader import partition_document

__all__ = ["Chunk", "process_document"]


def process_document(data: bytes, *, doc_id: str, filename: str, settings: Settings) -> list[Chunk]:
    elements = partition_document(data, filename)
    return chunk_document(elements, doc_id=doc_id, filename=filename, settings=settings)
