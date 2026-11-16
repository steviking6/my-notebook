from app.api.routes import ingest
from app.core.config import get_settings


def upload(client, name, content):
    return client.post("/documents", files=[("files", (name, content, "text/plain"))]).json()[0]


def count_points(qdrant):
    return qdrant.count(get_settings().qdrant_collection).count


def test_ingest_indexes_uploaded_documents(client, qdrant):
    upload(client, "notes.txt", b"Gradient descent\n\nIt minimizes the loss step by step.")

    docs = client.post("/ingest").json()

    assert docs[0]["status"] == "indexed"
    assert docs[0]["chunk_count"] == 1
    assert count_points(qdrant) == 1


def test_ingest_twice_does_not_duplicate(client, qdrant):
    upload(client, "notes.txt", b"Gradient descent\n\nIt minimizes the loss step by step.")
    client.post("/ingest")
    client.post("/ingest")
    assert count_points(qdrant) == 1


def test_chunk_payload_is_stored(client, qdrant):
    doc = upload(client, "notes.txt", b"Gradient descent\n\nIt minimizes the loss step by step.")
    client.post("/ingest")

    point = qdrant.scroll(get_settings().qdrant_collection)[0][0]
    assert point.payload["doc_id"] == doc["id"]
    assert point.payload["section"] == "Gradient descent"


def test_delete_document_removes_its_chunks(client, qdrant):
    doc = upload(client, "notes.txt", b"Gradient descent\n\nIt minimizes the loss step by step.")
    client.post("/ingest")
    client.delete(f"/documents/{doc['id']}")
    assert count_points(qdrant) == 0


def test_a_failing_document_is_marked_failed(client, monkeypatch):
    def crash(*args):
        raise RuntimeError("parsing crashed")

    monkeypatch.setattr(ingest, "process_document", crash)
    upload(client, "notes.txt", b"some text")

    docs = client.post("/ingest").json()

    assert docs[0]["status"] == "failed"
    assert docs[0]["error"] == "parsing crashed"
