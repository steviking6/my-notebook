"""Split Unstructured elements into retrieval-sized chunks."""

import uuid
from pathlib import PurePath

from pydantic import BaseModel
from unstructured.chunking.basic import chunk_elements
from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import Element, Title

from app.core.config import Settings
from app.services.ingestion.loader import CODE_EXTENSIONS

# Fixed namespace so chunk ids are deterministic: re-ingesting the same
# document produces the same ids, which lets Qdrant overwrite instead of duplicate.
CHUNK_NAMESPACE = uuid.UUID("6f1c1d2e-8a4b-4f7e-9c3d-2b5a7e9f1a10")


class Chunk(BaseModel):
    id: str
    doc_id: str
    filename: str
    index: int  # position in the document
    text: str
    # PDFs/PPTX only, used in citations ("p. 3" or "p. 3-4"). A chunk can span two
    # pages when tiny sections (e.g. sparse slides) are merged together.
    page_start: int | None = None
    page_end: int | None = None
    section: str | None = None  # nearest heading, shown in the UI


def chunk_document(
    elements: list[Element], *, doc_id: str, filename: str, settings: Settings
) -> list[Chunk]:
    ext = PurePath(filename).suffix.lower()
    common = {
        "max_characters": settings.chunk_max_chars,
        "new_after_n_chars": settings.chunk_new_after_chars,
        "overlap": settings.chunk_overlap_chars,
    }
    if ext in CODE_EXTENSIONS:
        # Code has no headings: "by_title" would treat random lines as titles.
        # Basic chunking just packs consecutive blocks up to the size limit.
        raw_chunks = chunk_elements(elements, **common)
    else:
        raw_chunks = chunk_by_title(
            elements,
            combine_text_under_n_chars=settings.chunk_combine_under_chars,
            # A section that continues on the next page is cut at the page break,
            # so citations stay precise. (Merging of tiny sections can still span
            # pages: we record page_start/page_end for that case.)
            multipage_sections=False,
            **common,
        )

    chunks: list[Chunk] = []
    section: str | None = None
    for raw in raw_chunks:
        text = raw.text.strip()
        if not text:
            continue
        origin = getattr(raw.metadata, "orig_elements", None) or []
        # A chunk starting with a heading opens a new section; otherwise it
        # continues the previous one (e.g. a long section split in two).
        if origin and isinstance(origin[0], Title):
            section = origin[0].text.strip()[:200]
        pages = [e.metadata.page_number for e in origin if e.metadata.page_number] or [
            raw.metadata.page_number
        ]
        pages = [p for p in pages if p is not None]
        index = len(chunks)
        chunks.append(
            Chunk(
                id=str(uuid.uuid5(CHUNK_NAMESPACE, f"{doc_id}:{index}")),
                doc_id=doc_id,
                filename=filename,
                index=index,
                text=text,
                page_start=min(pages) if pages else None,
                page_end=max(pages) if pages else None,
                section=section if ext not in CODE_EXTENSIONS else None,
            )
        )
    return chunks
