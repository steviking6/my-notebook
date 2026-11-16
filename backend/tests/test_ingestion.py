"""Ingestion tests on small course files (tests/fixtures)."""

from pathlib import Path

import pytest

from app.services.ingestion import process_document

FIXTURES = Path(__file__).parent / "fixtures"


def chunks_of(name):
    return process_document((FIXTURES / name).read_bytes(), "doc123", name)


@pytest.mark.parametrize(
    "name", ["sql_course.md", "ml_course.html", "notes.txt", "schema.sql", "preprocessing.pdf"]
)
def test_every_format_gives_chunks(name):
    chunks = chunks_of(name)
    assert len(chunks) > 0
    assert all(c.text and c.filename == name for c in chunks)


def test_chunks_follow_headings():
    chunks = chunks_of("ml_course.html")
    assert [c.section for c in chunks] == ["Overfitting", "Bias-variance tradeoff"]


def test_pdf_chunks_have_a_page_number():
    chunks = chunks_of("preprocessing.pdf")
    assert chunks[0].page == 1


def test_sql_keeps_all_the_code():
    text = " ".join(c.text for c in chunks_of("schema.sql"))
    assert "CREATE TABLE students" in text and "GROUP BY s.name" in text


def test_same_document_gives_same_ids():
    assert [c.id for c in chunks_of("notes.txt")] == [c.id for c in chunks_of("notes.txt")]
