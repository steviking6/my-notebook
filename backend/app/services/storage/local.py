"""Local-disk storage, used in development."""

import shutil
from pathlib import Path

from app.schemas.documents import DocumentMeta
from app.services.storage.base import Storage

META_FILE = "meta.json"


class LocalStorage(Storage):
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _dir(self, doc_id: str) -> Path:
        path = (self.root / doc_id).resolve()
        # Defense in depth: never let an id escape the storage root.
        if path.parent != self.root:
            raise ValueError(f"Invalid document id: {doc_id!r}")
        return path

    def save(self, meta: DocumentMeta, data: bytes) -> None:
        folder = self._dir(meta.id)
        folder.mkdir(parents=True, exist_ok=False)
        (folder / meta.filename).write_bytes(data)
        self.update_meta(meta)

    def read(self, doc_id: str) -> bytes:
        meta = self.get_meta(doc_id)
        if meta is None:
            raise FileNotFoundError(doc_id)
        return (self._dir(doc_id) / meta.filename).read_bytes()

    def get_meta(self, doc_id: str) -> DocumentMeta | None:
        meta_path = self._dir(doc_id) / META_FILE
        if not meta_path.exists():
            return None
        return DocumentMeta.model_validate_json(meta_path.read_text(encoding="utf-8"))

    def update_meta(self, meta: DocumentMeta) -> None:
        (self._dir(meta.id) / META_FILE).write_text(
            meta.model_dump_json(indent=2), encoding="utf-8"
        )

    def list(self) -> list[DocumentMeta]:
        metas = [
            DocumentMeta.model_validate_json(p.read_text(encoding="utf-8"))
            for p in self.root.glob(f"*/{META_FILE}")
        ]
        return sorted(metas, key=lambda m: m.uploaded_at, reverse=True)

    def delete(self, doc_id: str) -> bool:
        folder = self._dir(doc_id)
        if not folder.exists():
            return False
        shutil.rmtree(folder)
        return True
