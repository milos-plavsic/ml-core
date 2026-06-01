"""ml-core: shared production utilities for ML/agent repositories."""

from ml_core.auth import APIKeyMiddleware, require_api_key
from ml_core.cache import DiskCache, TTLCache, cache_with_ttl
from ml_core.circuit import CircuitBreaker, CircuitOpenError
from ml_core.config import BaseAppSettings
from ml_core.exceptions import ApplicationError, RetryExhausted, ValidationError
from ml_core.lifecycle import (
    lifespan,
    register_shutdown,
    register_startup,
    shutdown_requested,
)
from ml_core.logging import configure_logging
from ml_core.middleware import install_middleware
from ml_core.observability import get_metrics
from ml_core.ratelimit import RateLimiter, RateLimitExceeded
from ml_core.retry import async_retry, retry_with_backoff
from ml_core.validation import validate_array, validate_dataframe

__all__ = [
    "APIKeyMiddleware",
    "ApplicationError",
    "BaseAppSettings",
    "CircuitBreaker",
    "CircuitOpenError",
    "DiskCache",
    "RateLimiter",
    "RateLimitExceeded",
    "RetryExhausted",
    "TTLCache",
    "ValidationError",
    "async_retry",
    "cache_with_ttl",
    "configure_logging",
    "get_metrics",
    "install_middleware",
    "lifespan",
    "register_shutdown",
    "register_startup",
    "require_api_key",
    "retry_with_backoff",
    "shutdown_requested",
    "validate_array",
    "validate_dataframe",
]
