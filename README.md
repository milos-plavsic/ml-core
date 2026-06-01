# ml-core

Shared production utilities for Python ML and agent services.

## Features

- Structured JSON logging (`configure_logging`)
- Pydantic settings (`AppSettings`)
- TTL disk cache with exponential-backoff retries
- FastAPI middleware (CORS, security headers, request IDs)
- API-key auth helper
- Token-bucket rate limiting
- Prometheus metrics + OpenTelemetry hooks
- DataFrame validation helpers

## Install

```bash
pip install "ml-core @ git+https://github.com/milos-plavsic/ml-core.git@v1.0.0"
```

## Usage

```python
from ml_core import configure_logging, install_middleware

logger = configure_logging("my-service")
```

## Consumers

Install as a versioned dependency from GitHub releases.

## License

MIT
