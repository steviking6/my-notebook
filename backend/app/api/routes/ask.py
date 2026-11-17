"""Ask a question: search + rerank + answer with citations."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from app.services.generation import generate_answer
from app.services.ingestion import Chunk
from app.services.retrieval import retrieve
from app.services.vector_store import get_qdrant

router = APIRouter(tags=["ask"])
Qdrant = Annotated[QdrantClient, Depends(get_qdrant)]


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    level: int = Field(default=3, ge=1, le=5)  # efficiency level 1-5


class AskResponse(BaseModel):
    answer: str  # contains citations like [1], [2]
    sources: list[Chunk]  # [n] in the answer = sources[n - 1]
    queries: list[str]  # queries used for the search (handy to debug)


@router.post("/ask")
def ask(request: AskRequest, qdrant: Qdrant) -> AskResponse:
    queries, chunks = retrieve(qdrant, request.question, request.level)
    answer = generate_answer(request.question, chunks)
    return AskResponse(answer=answer, sources=chunks, queries=queries)
