"""Search only (no answer yet): handy to check the retrieval."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from app.services.ingestion import Chunk
from app.services.retrieval import retrieve
from app.services.vector_store import get_qdrant

router = APIRouter(tags=["search"])
Qdrant = Annotated[QdrantClient, Depends(get_qdrant)]


class SearchRequest(BaseModel):
    question: str = Field(min_length=1)
    level: int = Field(default=3, ge=1, le=5)  # efficiency level 1-5


class SearchResponse(BaseModel):
    queries: list[str]
    chunks: list[Chunk]


@router.post("/search")
def search(request: SearchRequest, qdrant: Qdrant) -> SearchResponse:
    queries, chunks = retrieve(qdrant, request.question, request.level)
    return SearchResponse(queries=queries, chunks=chunks)
