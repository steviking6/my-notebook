from app.api.routes import ask as ask_route
from app.services.generation import NO_SOURCES, format_sources, generate_answer
from app.services.ingestion import Chunk


def make_chunk(i: int, text: str, page=None, section=None) -> Chunk:
    return Chunk(
        id=str(i), doc_id="d", filename="notes.pdf", index=i, text=text, page=page, section=section
    )


def test_sources_are_numbered_from_1_with_their_location():
    text = format_sources(
        [
            make_chunk(0, "The model learns the noise.", page=3, section="Overfitting"),
            make_chunk(1, "b"),
        ]
    )
    assert text.startswith("[1] (notes.pdf, p. 3, Overfitting)\nThe model learns the noise.")
    assert "[2] (notes.pdf)\nb" in text


def test_no_chunks_means_no_llm_call():
    assert generate_answer("What is overfitting?", []) == NO_SOURCES


def test_ask_endpoint_returns_answer_and_sources(client, monkeypatch):
    chunk = make_chunk(0, "The model learns the noise.")
    monkeypatch.setattr(ask_route, "retrieve", lambda qdrant, q, level: ([q], [chunk]))
    monkeypatch.setattr(ask_route, "generate_answer", lambda q, chunks: "It learns the noise [1].")

    resp = client.post("/ask", json={"question": "What is overfitting?", "level": 1})

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "It learns the noise [1]."
    assert body["sources"][0]["text"] == "The model learns the noise."
    assert body["queries"] == ["What is overfitting?"]
