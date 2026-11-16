"""Save uploaded files on disk.

Each document gets its own folder:
    data/uploads/<doc_id>/<filename>   the file
    data/uploads/<doc_id>/meta.json    its info (name, size, status...)
"""

import shutil
from pathlib import Path

from app.core.config import get_settings
from app.schemas.documents import DocumentMeta


class LocalStorage:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, meta: DocumentMeta, data: bytes) -> None:
        folder = self.root / meta.id
        folder.mkdir(parents=True)
        (folder / meta.filename).write_bytes(data)
        self.update_meta(meta)

    def update_meta(self, meta: DocumentMeta) -> None:
        (self.root / meta.id / "meta.json").write_text(meta.model_dump_json(indent=2))

    def get_meta(self, doc_id: str) -> DocumentMeta | None:
        path = self.root / doc_id / "meta.json"
        if not path.exists():
            return None
        return DocumentMeta.model_validate_json(path.read_text())

    def read(self, meta: DocumentMeta) -> bytes:
        return (self.root / meta.id / meta.filename).read_bytes()

    def list(self) -> list[DocumentMeta]:
        metas = [
            DocumentMeta.model_validate_json(p.read_text()) for p in self.root.glob("*/meta.json")
        ]
        return sorted(metas, key=lambda m: m.uploaded_at, reverse=True)  # newest first

    def delete(self, doc_id: str) -> None:
        shutil.rmtree(self.root / doc_id)


def get_storage() -> LocalStorage:
    """Used by FastAPI routes (and replaced by a temp folder in tests)."""
    return LocalStorage(get_settings().local_upload_dir)
