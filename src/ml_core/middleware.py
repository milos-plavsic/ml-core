"""ASGI middleware: request IDs, security headers, CORS — safe defaults."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable, Sequence

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rid = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = rid
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Content-Security-Policy": "default-src 'none'",
                "Strict-Transport-Security": (
                    "max-age=63072000; includeSubDomains; preload"
                ),
            }
        )
        return response


def install_middleware(
    app: FastAPI,
    *,
    # No wildcard default — caller must be explicit about allowed origins
    cors_allow_origins: Sequence[str] = (),
    cors_allow_credentials: bool = False,
    cors_allow_methods: Sequence[str] = ("GET", "POST"),
    cors_allow_headers: Sequence[str] = ("Content-Type", "X-API-Key", "X-Request-ID"),
) -> None:
    """Install request-ID, security headers, and CORS middleware onto ``app``."""
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    if cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(cors_allow_origins),
            allow_credentials=cors_allow_credentials,
            allow_methods=list(cors_allow_methods),
            allow_headers=list(cors_allow_headers),
        )
