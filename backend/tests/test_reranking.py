from app.services import reranking
from app.services.ingestion import Chunk
from app.services.reranking import pick, rerank


def make_chunks(*texts: str) -> list[Chunk]:
    return [
        Chunk(id=str(i), doc_id="d", filename="notes.txt", index=i, text=t)
        for i, t in enumerate(texts)
    ]


# ---------- FlashRank (real model, runs locally) ----------
def test_flashrank_puts_the_relevant_chunk_first():
    chunks = make_chunks(
        "The French Revolution started in 1789.",
        "Photosynthesis turns light into chemical energy in plants.",
        "Overfitting: the model learns the noise of the training set "
        "and performs badly on unseen test data.",
    )
    best = rerank("What is overfitting?", chunks, top_n=2, method="flashrank")

    assert len(best) == 2
    assert best[0].text.startswith("Overfitting")


# ---------- LLM (OpenAI call mocked) ----------
def test_llm_reranker_follows_the_llm_ranking(monkeypatch):
    chunks = make_chunks("a", "b", "c")
    monkeypatch.setattr(reranking, "rerank_llm", lambda q, c, n: pick(c, [2, 0], n))

    assert [c.text for c in rerank("q", chunks, top_n=2, method="llm")] == ["c", "a"]


def test_pick_ignores_bad_answers_and_fills_up():
    chunks = make_chunks("a", "b", "c", "d")
    # 9 does not exist, 2 is repeated, "x" is not a number, and only 1 valid id is left
    assert [c.text for c in pick(chunks, [9, 2, 2, "x"], top_n=3)] == ["c", "a", "b"]


def test_no_candidates_means_no_call():
    assert rerank("q", [], top_n=5, method="llm") == []
