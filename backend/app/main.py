"""FastAPI entrypoint for My Notebook."""

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, health
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.services.ingestion.loader import warmup

settings = get_settings()
setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Load the heavy parsing stack in the background: the API answers
    # /health immediately while torch & co. are imported.
    threading.Thread(target=warmup, daemon=True).start()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="My Notebook API",
    description="Upload course material, index it, and ask grounded questions.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router)
