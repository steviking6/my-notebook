"""Find the best chunks for a question.

question
  -> multi-query: the LLM rewrites it N times (different words, same need)
  -> for each query: dense search + BM25 search in Qdrant (= 2 ranked lists)
  -> RRF: merge all the lists into a single ranking
"""

import json
from dataclasses import dataclass

from openai import OpenAI
from qdrant_client import QdrantClient

from app.core.config import get_settings
from app.services.embeddings import embed_dense, embed_sparse_query
from app.services.ingestion import Chunk
from app.services.vector_store import DENSE, SPARSE


# ---------- 1. Efficiency levels ----------
@dataclass
class Level:
    name: str
    n_queries: int  # original question + rewrites
    top_k: int  # results kept per ranked list
    candidates: int  # chunks kept after RRF (sent to the reranker in MNB-8)
    final_chunks: int  # chunks given to the LLM for the answer (MNB-9)
    reranker: str  # "flashrank" or "llm" (MNB-8)


LEVELS = {
    1: Level("Fast", n_queries=1, top_k=10, candidates=20, final_chunks=4, reranker="flashrank"),
    2: Level("Light", n_queries=3, top_k=10, candidates=25, final_chunks=5, reranker="flashrank"),
    3: Level(
        "Balanced", n_queries=4, top_k=15, candidates=30, final_chunks=6, reranker="flashrank"
    ),
    4: Level("Deep", n_queries=6, top_k=20, candidates=40, final_chunks=8, reranker="flashrank"),
    5: Level("Exhaustive", n_queries=8, top_k=25, candidates=50, final_chunks=10, reranker="llm"),
}


# ---------- 2. Multi-query ----------
PROMPT = """You help a student search their course notes.
Rewrite the question below in {n} different ways, to find more relevant passages.
Vary the wording, use synonyms and technical terms, and include one more general version.
Return JSON: {{"queries": ["...", "..."]}}

Question: {question}"""


def generate_queries(question: str, n: int) -> list[str]:
    """Return the original question + (n - 1) rewrites."""
    if n == 1:
        return [question]  # level 1: no LLM call at all

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[{"role": "user", "content": PROMPT.format(n=n - 1, question=question)}],
        response_format={"type": "json_object"},  # force a JSON answer
    )
    rewrites = json.loads(response.choices[0].message.content)["queries"]
    return [question] + rewrites[: n - 1]


# ---------- 3. RRF ----------
def rrf(ranked_lists: list[list[str]], k: int = 60) -> dict[str, float]:
    """Reciprocal Rank Fusion.

    Each list contributes 1 / (k + rank) to every chunk it contains.
    A chunk found high in MANY lists ends up first.
    k = 60 (from the original paper) softens the gap between rank 1 and rank 2.
    Returns {chunk_id: score}, best first.
    """
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, chunk_id in enumerate(ranked, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank)
    return dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))


# ---------- 4. Put it all together ----------
def retrieve(client: QdrantClient, question: str, level: int) -> tuple[list[str], list[Chunk]]:
    """Return (queries used, best chunks after RRF)."""
    config = LEVELS[level]
    collection = get_settings().qdrant_collection
    queries = generate_queries(question, config.n_queries)
    dense_vectors = embed_dense(queries)  # one OpenAI call for all queries

    ranked_lists = []
    chunks_by_id = {}
    for query, dense_vector in zip(queries, dense_vectors, strict=True):
        searches = [
            (DENSE, dense_vector),  # by meaning
            (SPARSE, embed_sparse_query(query)),  # by exact words
        ]
        for vector_name, vector in searches:
            points = client.query_points(
                collection, query=vector, using=vector_name, limit=config.top_k, with_payload=True
            ).points
            ranked_lists.append([str(p.id) for p in points])
            for p in points:
                chunks_by_id[str(p.id)] = Chunk(**p.payload)

    fused = rrf(ranked_lists)
    best_ids = list(fused)[: config.candidates]
    return queries, [chunks_by_id[chunk_id] for chunk_id in best_ids]
