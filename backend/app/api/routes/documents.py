"""Upload, list and delete documents."""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from qdrant_client import QdrantClient

from app.schemas.documents import DocumentMeta
from app.services.ingestion import Chunk, process_document
from app.services.storage import LocalStorage, get_storage
from app.services.vector_store import delete_document_chunks, get_qdrant

router = APIRouter(prefix="/documents", tags=["documents"])
Storage = Annotated[LocalStorage, Depends(get_storage)]  # FastAPI gives us the storage
Qdrant = Annotated[QdrantClient, Depends(get_qdrant)]

ALLOWED_EXTENSIONS = {".pdf", ".html", ".htm", ".txt", ".md", ".sql", ".csv", ".docx", ".pptx"}
MAX_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("", status_code=201)
async def upload_documents(files: list[UploadFile], storage: Storage) -> list[DocumentMeta]:
    """Save the files. They are NOT chunked here: that is POST /ingest."""
    saved = []
    for file in files:
        # Keep only the name: "../../evil.txt" becomes "evil.txt" (no writing outside the folder).
        filename = Path(file.filename or "").name
        if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise HTTPException(415, f"{filename}: file type not supported")

        data = await file.read()
        if not data:
            raise HTTPException(400, f"{filename}: empty file")
        if len(data) > MAX_SIZE:
            raise HTTPException(413, f"{filename}: larger than 20 MB")

        meta = DocumentMeta(
            id=uuid.uuid4().hex,
            filename=filename,
            size_bytes=len(data),
            uploaded_at=datetime.now(UTC),
        )
        storage.save(meta, data)
        saved.append(meta)
    return saved


@router.get("")
def list_documents(storage: Storage) -> list[DocumentMeta]:
    return storage.list()


def get_document_or_404(doc_id: str, storage: LocalStorage) -> DocumentMeta:
    # Only accept our own ids (32 hex chars), never paths like "../..".
    if len(doc_id) != 32 or not all(c in "0123456789abcdef" for c in doc_id):
        raise HTTPException(404, "Document not found")
    meta = storage.get_meta(doc_id)
    if meta is None:
        raise HTTPException(404, "Document not found")
    return meta


@router.get("/{doc_id}/chunks")
def preview_chunks(doc_id: str, storage: Storage) -> list[Chunk]:
    """Show the chunks of a document without indexing it (to check the chunking)."""
    meta = get_document_or_404(doc_id, storage)
    return process_document(storage.read(meta), meta.id, meta.filename)


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: str, storage: Storage, qdrant: Qdrant) -> None:
    get_document_or_404(doc_id, storage)
    delete_document_chunks(qdrant, doc_id)  # remove its chunks from Qdrant too
    storage.delete(doc_id)
