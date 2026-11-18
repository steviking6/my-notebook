"""Shared API key, sent by the Next.js server in the X-API-Key header.

Why? In production the API URL is public: without this, anyone could call
/ask and spend our OpenAI credits. The key never reaches the browser:
only the Next.js server (its /api proxy) knows it.
Empty APP_API_KEY = check disabled (local dev and tests).
"""

import secrets
from typing import Annotated

from fastapi import Header, HTTPException

from app.core.config import get_settings


def require_api_key(x_api_key: Annotated[str, Header()] = "") -> None:
    expected = get_settings().app_api_key
    if not expected:
        return
    # compare_digest takes the same time whatever the input: no guessing by timing.
    if not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(401, "Invalid or missing API key")
