"""FastAPI entrypoint for My Notebook."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ask, documents, health, ingest, search
from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title="My Notebook API", version="0.1.0")

# Allow the Next.js frontend (another port/domain) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(ask.router)
