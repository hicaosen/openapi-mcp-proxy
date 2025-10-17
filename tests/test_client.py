"""Tests for the HTTP client factory."""

from __future__ import annotations

from typing import Any

import pytest

from openapi_mcp_proxy.core.client import create_http_client
from openapi_mcp_proxy.core.config import AuthConfig, ClientConfig, RuntimeConfig


class DummyClient:
    def __init__(self, **kwargs: Any):
        self.kwargs = kwargs


class DummyTransport:
    def __init__(self, retries: int):
        self.retries = retries


def test_client_merges_headers_and_retries(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, Any] = {}

    def fake_async_client(**kwargs: Any) -> DummyClient:
        captured.update(kwargs)
        return DummyClient(**kwargs)

    monkeypatch.setattr(
        "openapi_mcp_proxy.core.client.httpx.AsyncClient",
        fake_async_client,
    )

    runtime = RuntimeConfig(
        openapi_source="spec.yaml",
        headers={"X-Test": "1"},
        auth=AuthConfig(scheme="bearer", token="token"),
        client=ClientConfig(timeout=10, retries=2),
    )

    spec = {"servers": [{"url": "https://api.example"}]}

    client = create_http_client(
        runtime,
        spec,
        transport_factory=DummyTransport,
    )

    assert isinstance(client, DummyClient)
    assert captured["base_url"] == "https://api.example"
    assert captured["headers"]["Authorization"] == "Bearer token"
    assert captured["headers"]["X-Test"] == "1"
    assert captured["timeout"] == 10
    assert captured["verify"] is True
    assert isinstance(captured["transport"], DummyTransport)
    assert captured["transport"].retries == 2


def test_config_base_url_and_query_api_key(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, Any] = {}

    def fake_async_client(**kwargs: Any) -> DummyClient:
        captured.update(kwargs)
        return DummyClient(**kwargs)

    monkeypatch.setattr(
        "openapi_mcp_proxy.core.client.httpx.AsyncClient",
        fake_async_client,
    )

    runtime = RuntimeConfig(
        openapi_source="spec.yaml",
        base_url="https://override",
        auth=AuthConfig(
            scheme="api-key",
            api_key_value="value",
            api_key_name="token",
            api_key_location="query",
        ),
        client=ClientConfig(timeout=5),
    )

    spec = {"servers": [{"url": "https://api.example"}]}

    client = create_http_client(runtime, spec)

    assert isinstance(client, DummyClient)
    assert captured["base_url"] == "https://override"
    assert captured["params"]["token"] == "value"
    assert "transport" not in captured
