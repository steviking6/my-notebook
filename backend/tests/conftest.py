import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.storage import get_storage
from app.services.storage.local import LocalStorage


@pytest.fixture
def storage(tmp_path):
    return LocalStorage(tmp_path / "uploads")


@pytest.fixture
def client(storage):
    # Swap the real storage for a temporary one: tests never touch data/uploads.
    app.dependency_overrides[get_storage] = lambda: storage
    yield TestClient(app)
    app.dependency_overrides.clear()
