"""Server level tests for the OpenAPI → MCP proxy."""

from __future__ import annotations

import sys
from typing import Any

import pytest

import openapi_mcp_proxy.server as server_module
from openapi_mcp_proxy.core.config import AuthConfig, ClientConfig, RuntimeConfig
from openapi_mcp_proxy.server import create_proxy, get_proxy_instance, run


class DummyLoader:
    def __init__(self, spec: dict[str, Any]):
        self._spec = spec
        self.calls: list[str] = []

    def load(self, source: str) -> dict[str, Any]:
        self.calls.append(source)
        return self._spec


class DummyClient:
    def __init__(self, **kwargs: Any):
        self.kwargs = kwargs


class DummyProxy:
    def __init__(self, *, openapi_spec: dict[str, Any], client: Any, name: str):
        self.openapi_spec = openapi_spec
        self.client = client
        self.name = name
        self.run_called = False

    def run(self) -> None:
        self.run_called = True


def test_create_proxy_uses_loader(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "openapi_mcp_proxy.core.client.httpx.AsyncClient",
        lambda **kwargs: DummyClient(**kwargs),
    )
    monkeypatch.setattr(
        "openapi_mcp_proxy.core.server.FastMCPOpenAPI",
        DummyProxy,
    )

    spec = {"servers": [{"url": "https://api.example"}]}
    loader = DummyLoader(spec)
    runtime = RuntimeConfig(
        openapi_source="spec.yaml",
        headers={"X-Test": "1"},
        auth=AuthConfig(scheme="bearer", token="token"),
        client=ClientConfig(timeout=5),
    )

    proxy = create_proxy(runtime, loader=loader)

    assert loader.calls == ["spec.yaml"]
    assert isinstance(proxy, DummyProxy)
    assert proxy.openapi_spec is spec
    assert proxy.name == runtime.server_name
    assert proxy.client.kwargs["headers"]["Authorization"] == "Bearer token"


def test_run_invokes_proxy(monkeypatch: pytest.MonkeyPatch):
    runtime = RuntimeConfig(openapi_source="spec.yaml")
    dummy_proxy = DummyProxy(openapi_spec={}, client=DummyClient(), name="Proxy")

    monkeypatch.setattr(
        "openapi_mcp_proxy.server.load_runtime_config",
        lambda argv: (runtime, ["--leftover"]),
    )

    class DummyRegistry:
        def __init__(self, config: RuntimeConfig, loader: Any):
            self.config = config
            self.loader = loader

        def get(self) -> DummyProxy:
            return dummy_proxy

    monkeypatch.setattr(
        "openapi_mcp_proxy.server.ProxyRegistry",
        DummyRegistry,
    )
    monkeypatch.setattr(
        "openapi_mcp_proxy.server.OpenAPISpecLoader",
        lambda: object(),
    )

    original_argv = sys.argv[:]
    try:
        sys.argv = ["prog"]
        run([])
        assert sys.argv[1:] == ["--leftover"]
    finally:
        sys.argv = original_argv

    assert dummy_proxy.run_called is True


def test_get_proxy_instance_block_switch(monkeypatch: pytest.MonkeyPatch):
    class DummyRegistry:
        def __init__(self, config: RuntimeConfig):
            self.config = config
            self.proxy = DummyProxy(openapi_spec={}, client=DummyClient(), name="Proxy")

        def get(self) -> DummyProxy:
            return self.proxy

    runtime = RuntimeConfig(openapi_source="spec.yaml")
    server_module._registry = DummyRegistry(config=runtime)

    assert get_proxy_instance() is server_module._registry.proxy

    with pytest.raises(RuntimeError):
        get_proxy_instance(RuntimeConfig(openapi_source="other.yaml"))

    server_module._registry = None


def teardown_module(module):  # type: ignore[unused-argument]
    """Ensure module-level registry is reset between tests."""

    server_module._registry = None
