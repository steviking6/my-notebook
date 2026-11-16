"""Store chunks in Qdrant.

One collection = one "table". Each point (= one chunk) has:
- 2 vectors: "dense" (OpenAI) and "bm25" (sparse)
- a payload: the chunk text + info (file, page, section) returned with search results
"""

from functools import lru_cache

from qdrant_client import QdrantClient, models

from app.core.config import get_settings
from app.services.embeddings import embed_dense, embed_sparse
from app.services.ingestion import Chunk

DENSE = "dense"
SPARSE = "bm25"
DENSE_SIZE = 1536  # size of text-embedding-3-small vectors


@lru_cache  # one connection for the whole app
def get_qdrant() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def create_collection_if_missing(client: QdrantClient) -> None:
    name = get_settings().qdrant_collection
    if client.collection_exists(name):
        return
    client.create_collection(
        collection_name=name,
        vectors_config={
            DENSE: models.VectorParams(size=DENSE_SIZE, distance=models.Distance.COSINE)
        },
        # IDF = rare words weigh more than common ones (the "IDF" of BM25 / TF-IDF).
        sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )


def index_chunks(client: QdrantClient, chunks: list[Chunk]) -> None:
    create_collection_if_missing(client)
    texts = [c.text for c in chunks]
    dense_vectors = embed_dense(texts)
    sparse_vectors = embed_sparse(texts)

    points = [
        models.PointStruct(
            id=chunk.id,
            vector={DENSE: dense, SPARSE: sparse},
            payload=chunk.model_dump(),
        )
        for chunk, dense, sparse in zip(chunks, dense_vectors, sparse_vectors, strict=True)
    ]
    client.upsert(collection_name=get_settings().qdrant_collection, points=points)


def delete_document_chunks(client: QdrantClient, doc_id: str) -> None:
    name = get_settings().qdrant_collection
    if not client.collection_exists(name):
        return
    client.delete(
        collection_name=name,
        points_selector=models.Filter(
            must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))]
        ),
    )
