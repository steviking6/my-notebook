"""The "Chunk & Index" button."""

from typing import Annotated

from fastapi import APIRouter, Depends
from qdrant_client import QdrantClient

from app.schemas.documents import DocumentMeta, DocumentStatus
from app.services.ingestion import process_document
from app.services.storage import LocalStorage, get_storage
from app.services.vector_store import get_qdrant, index_chunks

router = APIRouter(tags=["ingest"])
Storage = Annotated[LocalStorage, Depends(get_storage)]
Qdrant = Annotated[QdrantClient, Depends(get_qdrant)]


@router.post("/ingest")
def ingest(storage: Storage, qdrant: Qdrant) -> list[DocumentMeta]:
    """Chunk + index every document that is not indexed yet."""
    for meta in storage.list():
        if meta.status == DocumentStatus.INDEXED:
            continue
        try:
            chunks = process_document(storage.read(meta), meta.id, meta.filename)
            if not chunks:
                raise ValueError("No text found (scanned PDF or image?)")
            index_chunks(qdrant, chunks)
            meta.status = DocumentStatus.INDEXED
            meta.chunk_count = len(chunks)
            meta.error = None
        except Exception as error:  # one bad file must not stop the others
            meta.status = DocumentStatus.FAILED
            meta.error = str(error)
        storage.update_meta(meta)
    return storage.list()
