"""Upload, list and delete source documents."""

import uuid
from datetime import UTC, datetime
from pathlib import PurePath
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.schemas.documents import DocumentMeta
from app.services.storage import Storage, get_storage

router = APIRouter(prefix="/documents", tags=["documents"])

# Reusable dependency: FastAPI injects the configured storage backend.
StorageDep = Annotated[Storage, Depends(get_storage)]

# Formats Unstructured can parse with the lightweight "fast" strategy.
ALLOWED_EXTENSIONS = {".pdf", ".html", ".htm", ".txt", ".md", ".sql", ".csv", ".docx", ".pptx"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _safe_filename(name: str | None) -> str:
    # Keep only the final path component: "../../etc/passwd" -> "passwd".
    clean = PurePath(name or "").name.strip()
    if not clean or clean in {".", ".."}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing or invalid filename")
    return clean


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_documents(files: list[UploadFile], storage: StorageDep) -> list[DocumentMeta]:
    """Store one or more files. They are NOT chunked yet: that is the job of POST /ingest."""
    # Validate everything first, so a bad file does not leave a half-done batch.
    payloads: list[tuple[str, UploadFile, bytes]] = []
    for file in files:
        filename = _safe_filename(file.filename)
        ext = PurePath(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                f"{filename}: unsupported type {ext or '(none)'}. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )
        data = await file.read(MAX_FILE_SIZE + 1)
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, f"{filename}: larger than 20 MB")
        if not data:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{filename}: empty file")
        payloads.append((filename, file, data))

    saved: list[DocumentMeta] = []
    for filename, file, data in payloads:
        meta = DocumentMeta(
            id=uuid.uuid4().hex,
            filename=filename,
            content_type=file.content_type,
            size_bytes=len(data),
            uploaded_at=datetime.now(UTC),
        )
        storage.save(meta, data)
        saved.append(meta)
    return saved


@router.get("")
def list_documents(storage: StorageDep) -> list[DocumentMeta]:
    return storage.list()


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: str, storage: StorageDep) -> None:
    # Ids are uuid4 hex: reject anything else before touching storage.
    try:
        uuid.UUID(hex=doc_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found") from exc
    if not storage.delete(doc_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    # TODO(MNB-6): also delete the document's chunks from Qdrant.
