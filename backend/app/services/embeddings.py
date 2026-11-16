"""Turn texts into vectors.

- dense  (OpenAI): captures the MEANING   -> "car" is close to "automobile"
- sparse (BM25):   captures the EXACT WORDS -> great for "LEFT JOIN", "L2", names
"""

from functools import lru_cache

from fastembed import SparseTextEmbedding
from openai import OpenAI
from qdrant_client import models

from app.core.config import get_settings


def embed_dense(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    vectors = []
    for start in range(0, len(texts), 100):  # send 100 texts per API call
        response = client.embeddings.create(
            model=settings.openai_embedding_model, input=texts[start : start + 100]
        )
        vectors += [item.embedding for item in response.data]
    return vectors


@lru_cache  # load the BM25 model only once
def _bm25_model() -> SparseTextEmbedding:
    return SparseTextEmbedding("Qdrant/bm25")


def embed_sparse(texts: list[str]) -> list[models.SparseVector]:
    return [
        models.SparseVector(indices=e.indices.tolist(), values=e.values.tolist())
        for e in _bm25_model().embed(texts)
    ]


def embed_sparse_query(query: str) -> models.SparseVector:
    """BM25 for a question (slightly different from documents: every word counts once)."""
    e = next(iter(_bm25_model().query_embed(query)))
    return models.SparseVector(indices=e.indices.tolist(), values=e.values.tolist())
