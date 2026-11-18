# FastAPI backend image (local docker compose + Cloud Run).
FROM python:3.12-slim

# uv, pinned (same version as in dev)
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/uv

# libmagic: used by Unstructured to detect file types
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    MODEL_CACHE_DIR=/app/models \
    FASTEMBED_CACHE_PATH=/app/models/fastembed

# 1. Dependencies first: this layer is cached as long as the lockfile does not change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2. Download the local models at build time, not at the first request
#    (otherwise every new Cloud Run instance would download them again):
#    - FlashRank reranker + BM25: same names as app/services/reranking.py and embeddings.py
#    - spaCy "en_core_web_sm": Unstructured installs it into .venv on first use,
#      which fails at runtime because the app does not run as root.
RUN python -c "\
from flashrank import Ranker; Ranker(model_name='ms-marco-MiniLM-L-12-v2', cache_dir='/app/models'); \
from fastembed import SparseTextEmbedding; SparseTextEmbedding('Qdrant/bm25'); \
from unstructured.nlp.tokenize import sent_tokenize; sent_tokenize('Warm up.')"

# 3. The code (changes often, so it comes last)
COPY app ./app

# Do not run as root
RUN useradd --uid 1000 --create-home app && chown -R app /app/models
USER app

# Cloud Run gives the port in $PORT (8080 by default)
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
