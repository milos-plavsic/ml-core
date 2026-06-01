"""Unit tests for ml_core.auth."""

import os

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ml_core.auth import APIKeyMiddleware


def _make_app(key: str = "secret") -> TestClient:
    os.environ["API_KEY"] = key
    app = FastAPI()
    app.add_middleware(APIKeyMiddleware, public_paths=("/health",))

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/protected")
    def protected():
        return {"data": "secret"}

    return TestClient(app, raise_server_exceptions=False)


def test_public_path_no_key_required():
    client = _make_app()
    r = client.get("/health")
    assert r.status_code == 200


def test_protected_without_key_returns_401():
    client = _make_app()
    r = client.get("/protected")
    assert r.status_code == 401


def test_protected_with_correct_key():
    client = _make_app("my-key")
    r = client.get("/protected", headers={"X-API-Key": "my-key"})
    assert r.status_code == 200


def test_protected_with_wrong_key_returns_401():
    client = _make_app("my-key")
    r = client.get("/protected", headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


def test_no_key_configured_allows_all():
    os.environ.pop("API_KEY", None)
    app = FastAPI()
    app.add_middleware(APIKeyMiddleware)

    @app.get("/open")
    def open_route():
        return {"ok": True}

    client = TestClient(app)
    r = client.get("/open")
    assert r.status_code == 200
