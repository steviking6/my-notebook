"""Ingestion = 2 steps.

1. partition_document: file -> list of "elements" (Title, paragraph, list item...)
2. chunk_document:     elements -> chunks of ~1200 characters, cut at headings
"""

import io
import uuid

from pydantic import BaseModel
from unstructured.chunking.basic import chunk_elements
from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import Element, Title
from unstructured.partition.auto import partition


class Chunk(BaseModel):
    id: str
    doc_id: str
    filename: str
    index: int  # 0, 1, 2... position in the document
    text: str
    page: int | None = None  # PDF/PPTX only
    section: str | None = None  # the heading this chunk belongs to


def partition_document(data: bytes, filename: str) -> list[Element]:
    """Read a file and return its elements."""
    extra = {}
    if filename.lower().endswith(".sql"):
        extra["content_type"] = "text/plain"  # Unstructured has no SQL reader: read as text

    return partition(
        file=io.BytesIO(data),
        metadata_filename=filename,
        strategy="fast",  # read the PDF text layer directly (no OCR / vision model)
        languages=["eng"],
        **extra,
    )


def chunk_document(
    elements: list[Element], doc_id: str, filename: str, max_chars: int = 1200
) -> list[Chunk]:
    """Group elements into chunks."""
    if filename.lower().endswith(".sql"):
        # SQL has no headings: just pack lines together up to max_chars.
        raw_chunks = chunk_elements(elements, max_characters=max_chars)
    else:
        # Start a new chunk at every heading, so a section stays together.
        raw_chunks = chunk_by_title(
            elements,
            max_characters=max_chars,
            combine_text_under_n_chars=200,  # merge only very small sections (e.g. a lone title)
        )

    chunks = []
    section = None
    for i, raw in enumerate(raw_chunks):
        first_element = raw.metadata.orig_elements[0]
        if isinstance(first_element, Title):
            section = first_element.text  # new heading -> new section

        chunks.append(
            Chunk(
                # Same doc + same position = same id, so re-indexing overwrites
                # the old chunk in Qdrant instead of creating a duplicate.
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}-{i}")),
                doc_id=doc_id,
                filename=filename,
                index=i,
                text=raw.text,
                page=raw.metadata.page_number,
                section=section,
            )
        )
    return chunks


def process_document(data: bytes, doc_id: str, filename: str) -> list[Chunk]:
    """Steps 1 + 2."""
    elements = partition_document(data, filename)
    return chunk_document(elements, doc_id, filename)
