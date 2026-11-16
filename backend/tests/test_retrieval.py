import pytest
from qdrant_client import models

from app.services import retrieval
from app.services.retrieval import LEVELS, generate_queries, rrf


# ---------- RRF (checked by hand) ----------
def test_rrf_scores_match_the_formula():
    scores = rrf([["a", "b"], ["b", "c"]], k=60)
    # a: rank 1 in list 1          -> 1/61
    # b: rank 2 in list 1 + rank 1 in list 2 -> 1/62 + 1/61
    # c: rank 2 in list 2          -> 1/62
    assert scores["a"] == pytest.approx(1 / 61)
    assert scores["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert scores["c"] == pytest.approx(1 / 62)
    assert list(scores) == ["b", "a", "c"]  # b is in both lists -> first


def test_rrf_rewards_agreement_over_one_top_rank():
    # "x" is first in one list only; "y" is second in three lists.
    scores = rrf([["x", "y"], ["z", "y"], ["w", "y"]])
    assert list(scores)[0] == "y"


# ---------- Levels ----------
def test_more_efficiency_means_more_queries():
    n = [LEVELS[level].n_queries for level in range(1, 6)]
    assert n == [1, 3, 4, 6, 8]
    assert n == sorted(n)


def test_level_1_does_not_call_the_llm():
    assert generate_queries("What is overfitting?", 1) == ["What is overfitting?"]


# ---------- Full search on in-memory Qdrant ----------
def test_search_endpoint_returns_indexed_chunks(client, monkeypatch):
    monkeypatch.setattr(retrieval, "generate_queries", lambda q, n: [q, "rewrite"][:n])
    monkeypatch.setattr(retrieval, "embed_dense", lambda texts: [[0.1] * 1536 for _ in texts])
    monkeypatch.setattr(
        retrieval,
        "embed_sparse_query",
        lambda q: models.SparseVector(indices=[1, 2], values=[1.0, 1.0]),
    )
    client.post(
        "/documents",
        files=[
            ("files", ("notes.txt", b"Overfitting\n\nThe model learns the noise.", "text/plain"))
        ],
    )
    client.post("/ingest")

    resp = client.post("/search", json={"question": "What is overfitting?", "level": 2})

    assert resp.status_code == 200
    body = resp.json()
    assert body["queries"] == ["What is overfitting?", "rewrite"]
    assert body["chunks"][0]["section"] == "Overfitting"


def test_level_must_be_between_1_and_5(client):
    assert client.post("/search", json={"question": "x", "level": 9}).status_code == 422
