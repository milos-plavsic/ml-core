"""Prometheus metrics + optional OpenTelemetry tracing."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
_cache_hits = Counter("cache_hits_total", "Cache hits", ["cache"])
_cache_misses = Counter("cache_misses_total", "Cache misses", ["cache"])


def get_metrics() -> dict:
    return {
        "requests_total": _requests_total,
        "request_duration": _request_duration,
        "cache_hits": _cache_hits,
        "cache_misses": _cache_misses,
    }


metrics_router = APIRouter()


@metrics_router.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def observe_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    path = request.url.path
    _requests_total.labels(request.method, path, str(response.status_code)).inc()
    _request_duration.labels(request.method, path).observe(duration)
    return response


# ------------------------------------------------------------------
# Optional OpenTelemetry tracing — graceful no-op if not installed
# ------------------------------------------------------------------
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    _provider = TracerProvider()
    _provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(_provider)
    _tracer = trace.get_tracer("ml-core")

    def get_tracer():
        return _tracer

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

    class _NoOpTracer:
        def start_as_current_span(self, name, **_):
            from contextlib import nullcontext

            return nullcontext()

    def get_tracer():
        return _NoOpTracer()
