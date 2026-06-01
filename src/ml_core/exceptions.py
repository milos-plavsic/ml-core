"""Typed exception hierarchy for ml-core."""


class ApplicationError(Exception):
    """Base for all application-level errors."""

    status_code: int = 500

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class RetryExhausted(ApplicationError):
    """All retry attempts were exhausted."""

    status_code = 503


class ValidationError(ApplicationError):
    """Input or data validation failure."""

    status_code = 422


class AuthenticationError(ApplicationError):
    """Missing or invalid credentials."""

    status_code = 401


class RateLimitExceeded(ApplicationError):
    """Request rate limit exceeded."""

    status_code = 429


class CircuitOpenError(ApplicationError):
    """Circuit breaker is open — downstream service unavailable."""

    status_code = 503


class ConfigurationError(ApplicationError):
    """Invalid or missing configuration."""

    status_code = 500
