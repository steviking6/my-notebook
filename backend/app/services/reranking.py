"""Re-order the RRF candidates by how well they really answer the question.

Why a second step? The search (dense + BM25) compares the question and each chunk
SEPARATELY (two vectors). A reranker reads the question AND the chunk TOGETHER,
so it is much more precise, but too slow to run on the whole collection.
So: search finds ~30 candidates, the reranker keeps the best ~6.

- "flashrank": small cross-encoder model, runs locally on CPU (free, ~100 ms).
- "llm":       the OpenAI chat model reads all candidates and ranks them
               (better on tricky questions, but slower and paid). Level 5 only.
"""

import json
from functools import lru_cache

from flashrank import Ranker, RerankRequest
from openai import OpenAI

from app.core.config import get_settings
from app.services.ingestion import Chunk

FLASHRANK_MODEL = "ms-marco-MiniLM-L-12-v2"


# ---------- 1. FlashRank (cross-encoder) ----------
@lru_cache
def get_ranker() -> Ranker:
    """Load the model once (downloaded on first use, ~30 MB)."""
    return Ranker(model_name=FLASHRANK_MODEL, cache_dir=get_settings().model_cache_dir)


def rerank_flashrank(question: str, chunks: list[Chunk], top_n: int) -> list[Chunk]:
    passages = [{"id": i, "text": chunk.text} for i, chunk in enumerate(chunks)]
    results = get_ranker().rerank(RerankRequest(query=question, passages=passages))
    # results are sorted best first, each one keeps the "id" we gave it
    return [chunks[r["id"]] for r in results[:top_n]]


# ---------- 2. LLM ----------
PROMPT = """You help a student find the passages of their course notes that answer a question.
Below are numbered passages. Return the numbers of the {top_n} most useful passages
to answer the question, the most useful first.
Return JSON: {{"ranking": [3, 0, 7]}}

Question: {question}

Passages:
{passages}"""


def rerank_llm(question: str, chunks: list[Chunk], top_n: int) -> list[Chunk]:
    passages = "\n\n".join(f"[{i}] {chunk.text}" for i, chunk in enumerate(chunks))
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {
                "role": "user",
                "content": PROMPT.format(top_n=top_n, question=question, passages=passages),
            }
        ],
        response_format={"type": "json_object"},
    )
    ranking = json.loads(response.choices[0].message.content)["ranking"]
    return pick(chunks, ranking, top_n)


def pick(chunks: list[Chunk], ranking: list, top_n: int) -> list[Chunk]:
    """Turn the LLM's numbers into chunks, without trusting it blindly.

    Ignore invalid numbers and duplicates. If the LLM returned too few,
    fill up with the remaining chunks in their RRF order.
    """
    order = []
    for i in ranking:
        if isinstance(i, int) and 0 <= i < len(chunks) and i not in order:
            order.append(i)
    order += [i for i in range(len(chunks)) if i not in order]
    return [chunks[i] for i in order[:top_n]]


# ---------- 3. Entry point ----------
def rerank(question: str, chunks: list[Chunk], top_n: int, method: str) -> list[Chunk]:
    if not chunks:
        return []
    if method == "llm":
        return rerank_llm(question, chunks, top_n)
    return rerank_flashrank(question, chunks, top_n)
