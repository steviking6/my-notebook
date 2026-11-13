"""Pick the storage backend from settings (Strategy pattern)."""

from functools import lru_cache

from app.core.config import get_settings
from app.services.storage.base import Storage
from app.services.storage.local import LocalStorage

__all__ = ["Storage", "get_storage"]


@lru_cache
def get_storage() -> Storage:
    settings = get_settings()
    if settings.storage_backend == "local":
        return LocalStorage(settings.local_upload_dir)
    # GCS backend arrives with the deployment ticket (MNB-11).
    raise NotImplementedError(f"Storage backend {settings.storage_backend!r} not implemented yet")
