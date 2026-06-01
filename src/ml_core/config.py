"""Base settings shared across all repos."""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class BaseAppSettings(BaseSettings):
    app_name: str = "ml-service"
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"
    api_key: str = ""  # empty = auth disabled (dev)

    # Cache
    cache_ttl_seconds: int = Field(default=3600, ge=60)
    cache_max_size: int = Field(default=1000, ge=1)

    # Retry
    request_max_retries: int = Field(default=3, ge=1, le=10)
    request_backoff_factor: float = Field(default=2.0, ge=1.0)

    # ML defaults
    random_state: int = 42
    validation_split: float = Field(default=0.2, ge=0.0, le=0.5)

    # CORS — explicit allowlist; never default to "*" in production
    cors_allow_origins: list[str] = Field(default_factory=list)

    @field_validator("log_level")
    @classmethod
    def _valid_log_level(cls, v: str) -> str:
        import logging

        if v.upper() not in logging._nameToLevel:
            raise ValueError(f"Invalid log level: {v!r}")
        return v.upper()

    model_config = {"env_file": ".env", "extra": "ignore"}
