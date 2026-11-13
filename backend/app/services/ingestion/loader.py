"""Turn a raw file into Unstructured elements (Title, NarrativeText, ListItem, Table...)."""

import io
import logging
from pathlib import PurePath

from unstructured.documents.elements import Element
from unstructured.partition.auto import partition

logger = logging.getLogger(__name__)

# Files that are code/data rather than prose: no headings to detect.
CODE_EXTENSIONS = {".sql"}


def partition_document(data: bytes, filename: str) -> list[Element]:
    """Parse a file with Unstructured.

    strategy="fast" extracts the text layer with pdfminer: quick and CPU-light.
    "hi_res" (layout detection model) would handle scanned PDFs and tables
    better, but is ~10-50x slower: it is a v2 option.
    """
    ext = PurePath(filename).suffix.lower()
    kwargs: dict = {}
    if ext in CODE_EXTENSIONS:
        # Unstructured has no SQL partitioner: read it as plain text.
        kwargs["content_type"] = "text/plain"

    elements = partition(
        file=io.BytesIO(data),
        metadata_filename=filename,
        strategy="fast",
        languages=["eng"],
        **kwargs,
    )
    logger.info("Partitioned %s into %d elements", filename, len(elements))
    return elements


def warmup() -> None:
    """Import the heavy PDF stack (torch, pdfminer...) once at startup.

    The first import costs tens of seconds; doing it in the background
    avoids making the first user's "Chunk & Index" click pay for it.
    """
    try:
        from unstructured.partition.pdf import partition_pdf  # noqa: F401

        logger.info("Unstructured PDF stack loaded")
    except Exception:  # pragma: no cover - warmup must never crash the app
        logger.exception("Unstructured warmup failed")
