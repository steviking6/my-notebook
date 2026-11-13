def _upload(client, *files):
    return client.post("/documents", files=[("files", f) for f in files])


def test_upload_list_delete_roundtrip(client, storage):
    resp = _upload(client, ("notes.txt", b"SQL joins: INNER, LEFT, RIGHT.", "text/plain"))
    assert resp.status_code == 201
    doc = resp.json()[0]
    assert doc["filename"] == "notes.txt"
    assert doc["status"] == "uploaded"
    assert doc["size_bytes"] == 30
    assert storage.read(doc["id"]) == b"SQL joins: INNER, LEFT, RIGHT."

    listed = client.get("/documents").json()
    assert [d["id"] for d in listed] == [doc["id"]]

    assert client.delete(f"/documents/{doc['id']}").status_code == 204
    assert client.get("/documents").json() == []


def test_upload_several_files_at_once(client):
    resp = _upload(
        client,
        ("a.md", b"# Title", "text/markdown"),
        ("b.sql", b"SELECT 1;", "application/sql"),
    )
    assert resp.status_code == 201
    assert {d["filename"] for d in resp.json()} == {"a.md", "b.sql"}


def test_rejects_unsupported_extension(client):
    resp = _upload(client, ("virus.exe", b"MZ", "application/octet-stream"))
    assert resp.status_code == 415


def test_rejects_empty_file(client):
    assert _upload(client, ("empty.txt", b"", "text/plain")).status_code == 400


def test_bad_batch_stores_nothing(client):
    resp = _upload(client, ("ok.txt", b"hello", "text/plain"), ("bad.exe", b"x", "x/x"))
    assert resp.status_code == 415
    assert client.get("/documents").json() == []


def test_path_traversal_filename_is_neutralized(client, storage):
    doc = _upload(client, ("../../evil.txt", b"x", "text/plain")).json()[0]
    assert doc["filename"] == "evil.txt"
    assert (storage.root / doc["id"] / "evil.txt").exists()


def test_delete_unknown_or_malformed_id_returns_404(client):
    assert client.delete("/documents/" + "0" * 32).status_code == 404
    assert client.delete("/documents/..").status_code in (404, 405)


def test_preview_chunks_endpoint(client):
    doc = _upload(
        client, ("notes.txt", b"Title\n\nSome body text about SQL.", "text/plain")
    ).json()[0]
    resp = client.get(f"/documents/{doc['id']}/chunks")
    assert resp.status_code == 200
    chunks = resp.json()
    assert chunks and chunks[0]["doc_id"] == doc["id"]


def test_preview_chunks_unknown_doc_returns_404(client):
    assert client.get("/documents/" + "0" * 32 + "/chunks").status_code == 404
