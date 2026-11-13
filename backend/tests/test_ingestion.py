"""Ingestion tests on real sample course files (tests/fixtures)."""

from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.ingestion import process_document

FIXTURES = Path(__file__).parent / "fixtures"
SETTINGS = Settings(_env_file=None)


def _chunks(name: str, settings: Settings = SETTINGS):
    return process_document(
        (FIXTURES / name).read_bytes(), doc_id="doc123", filename=name, settings=settings
    )


@pytest.mark.parametrize(
    "name", ["sql_course.md", "ml_course.html", "notes.txt", "schema.sql", "preprocessing.pdf"]
)
def test_every_supported_format_produces_chunks(name):
    chunks = _chunks(name)
    assert chunks, f"{name} produced no chunk"
    assert all(c.text and c.doc_id == "doc123" and c.filename == name for c in chunks)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_chunks_follow_headings():
    chunks = _chunks("ml_course.html")
    assert [c.section for c in chunks] == ["Overfitting", "Bias-variance tradeoff"]
    assert "regularization" in chunks[0].text  # list items stay with their section


def test_pdf_chunks_record_their_page_range():
    # Both pages are tiny, so they are merged into one chunk covering pages 1-2.
    chunks = _chunks("preprocessing.pdf")
    assert [(c.page_start, c.page_end) for c in chunks] == [(1, 2)]
    assert chunks[0].section == "Normalization"


def test_pdf_pages_are_separate_when_not_merged():
    no_merge = Settings(_env_file=None, chunk_combine_under_chars=0)
    chunks = _chunks("preprocessing.pdf", no_merge)
    assert [(c.page_start, c.page_end) for c in chunks] == [(1, 1), (2, 2)]
    assert [c.section for c in chunks] == ["Normalization", "Standardization"]


def test_sql_is_not_split_on_fake_titles():
    chunks = _chunks("schema.sql")
    full = " ".join(c.text for c in chunks)
    assert "CREATE TABLE students" in full and "GROUP BY s.name" in full
    assert all(c.section is None for c in chunks)


def test_max_chars_is_respected():
    small = Settings(
        _env_file=None,
        chunk_max_chars=150,
        chunk_new_after_chars=120,
        chunk_overlap_chars=20,
        chunk_combine_under_chars=0,
    )
    chunks = _chunks("sql_course.md", small)
    assert len(chunks) > 2
    assert all(len(c.text) <= 150 for c in chunks)


def test_chunk_ids_are_deterministic():
    assert [c.id for c in _chunks("notes.txt")] == [c.id for c in _chunks("notes.txt")]
