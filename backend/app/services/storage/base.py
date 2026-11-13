"""Storage abstraction for raw uploaded files.

Each document lives under its own folder, keyed by a server-generated id:
    <doc_id>/<filename>      the raw file
    <doc_id>/meta.json       its metadata (DocumentMeta)

Keeping metadata next to the file means we need no extra database:
the same layout works on local disk and on a Cloud Storage bucket.
"""

from abc import ABC, abstractmethod

from app.schemas.documents import DocumentMeta


class Storage(ABC):
    @abstractmethod
    def save(self, meta: DocumentMeta, data: bytes) -> None:
        """Persist the raw file and its metadata."""

    @abstractmethod
    def read(self, doc_id: str) -> bytes:
        """Return the raw file content."""

    @abstractmethod
    def get_meta(self, doc_id: str) -> DocumentMeta | None:
        """Return metadata, or None if the document does not exist."""

    @abstractmethod
    def update_meta(self, meta: DocumentMeta) -> None:
        """Overwrite metadata (e.g. status change after ingestion)."""

    @abstractmethod
    def list(self) -> list[DocumentMeta]:
        """All documents, most recent first."""

    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """Remove file + metadata. Returns False if it did not exist."""
