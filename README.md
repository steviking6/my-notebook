# My Notebook

A study companion inspired by NotebookLM: upload your course material, index it in one click, and ask questions that are answered **only from your sources**, with citations.

> 🚧 Work in progress. Full documentation lands with the first release.

## Stack

- **Backend**: FastAPI · Unstructured · Qdrant (hybrid dense + BM25) · OpenAI
- **Retrieval**: multi-query → hybrid search → Reciprocal Rank Fusion → reranking
- **Frontend**: Next.js
- **Deployment**: Google Cloud Run

## Quickstart (local)

```bash
cp .env.example .env          # add your OPENAI_API_KEY
make qdrant-up                # start Qdrant in Docker
make backend-install
make backend-dev              # API on http://localhost:8000/docs
```

## Project layout

```
backend/        FastAPI app (ingestion, retrieval, reranking, generation)
frontend/       Next.js UI
documentation/  Architecture diagrams, ADRs, learning notes
```
