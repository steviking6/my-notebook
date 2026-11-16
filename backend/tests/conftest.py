import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient, models

from app.main import app
from app.services import vector_store
from app.services.storage import LocalStorage, get_storage
from app.services.vector_store import get_qdrant


@pytest.fixture
def storage(tmp_path):
    return LocalStorage(tmp_path / "uploads")


@pytest.fixture
def qdrant(monkeypatch):
    # Fake embeddings: no OpenAI call (free, fast, works offline).
    monkeypatch.setattr(
        vector_store, "embed_dense", lambda texts: [[0.1] * vector_store.DENSE_SIZE for _ in texts]
    )
    monkeypatch.setattr(
        vector_store,
        "embed_sparse",
        lambda texts: [models.SparseVector(indices=[1, 2], values=[0.5, 0.5]) for _ in texts],
    )
    # Qdrant "in memory": a real Qdrant, without Docker.
    return QdrantClient(":memory:")


@pytest.fixture
def client(storage, qdrant):
    # Use a temp folder and in-memory Qdrant instead of the real ones.
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_qdrant] = lambda: qdrant
    yield TestClient(app)
    app.dependency_overrides.clear()
