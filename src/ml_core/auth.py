"""API-key authentication middleware and dependency."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ml_core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def _constant_time_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(
        hashlib.sha256(a.encode()).digest(),
        hashlib.sha256(b.encode()).digest(),
    )


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Reject requests that don't carry a valid X-API-Key header.

    Paths listed in ``public_paths`` are exempt (e.g. /health, /metrics).

    Set ``API_KEY`` environment variable on the server.  If the env var is
    absent the middleware is a no-op (useful in local dev without auth).
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        public_paths: tuple[str, ...] = (
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
        ),
        env_var: str = "API_KEY",
    ) -> None:
        super().__init__(app)
        self._public = public_paths
        self._key: str | None = os.environ.get(env_var, "").strip() or None
        if not self._key:
            logger.warning("API_KEY not set — auth middleware is a no-op (dev mode)")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self._key or request.url.path in self._public:
            return await call_next(request)

        provided = request.headers.get("X-API-Key", "").strip()
        if not provided or not _constant_time_compare(provided, self._key):
            logger.warning(
                "Rejected request: bad/missing X-API-Key from %s", request.client
            )
            return Response(
                content=(
                    '{"error":"Unauthorized",'
                    '"detail":"Missing or invalid X-API-Key"}'
                ),
                status_code=401,
                media_type="application/json",
            )
        return await call_next(request)


async def require_api_key(request: Request) -> str:
    """FastAPI dependency that validates X-API-Key and returns it."""
    key = os.environ.get("API_KEY", "").strip()
    if not key:
        return "dev"
    provided = request.headers.get("X-API-Key", "").strip()
    if not provided or not _constant_time_compare(provided, key):
        raise AuthenticationError("Missing or invalid X-API-Key")
    return provided
