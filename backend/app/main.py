"""FastAPI entrypoint for My Notebook."""

from fastapi import Depends, FastAPI

from app.api.routes import ask, documents, health, ingest, search
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.security import require_api_key

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title="My Notebook API", version="0.1.0")

# No CORS: the browser never calls this API directly. It calls the Next.js
# server (/api/...), which forwards the request here with the API key.

app.include_router(health.router)  # public: used by Cloud Run / monitoring
protected = [Depends(require_api_key)]
app.include_router(documents.router, dependencies=protected)
app.include_router(ingest.router, dependencies=protected)
app.include_router(search.router, dependencies=protected)
app.include_router(ask.router, dependencies=protected)
