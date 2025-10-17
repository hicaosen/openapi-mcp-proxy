"""Server factory helpers for turning OpenAPI specs into MCP proxies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

try:  # pragma: no cover - imported lazily and mocked in tests
    from fastmcp.openapi import FastMCPOpenAPI
except ModuleNotFoundError:  # pragma: no cover - handled at runtime/tests
    FastMCPOpenAPI = None  # type: ignore[assignment]

from .client import create_http_client
from .config import RuntimeConfig
from .spec import OpenAPISpecLoader


def create_proxy(
    config: RuntimeConfig,
    *,
    loader: OpenAPISpecLoader | None = None,
) -> "FastMCPOpenAPI":
    if FastMCPOpenAPI is None:  # pragma: no cover - requires dependency
        raise RuntimeError("fastmcp.openapi.FastMCPOpenAPI 不可用，请安装 fastmcp 库。")

    loader = loader or OpenAPISpecLoader()
    spec = loader.load(config.openapi_source)
    client = create_http_client(config, spec)
    return FastMCPOpenAPI(openapi_spec=spec, client=client, name=config.server_name)


@dataclass(slots=True)
class ProxyRegistry:
    """Lazily initialises and memoises proxy instances."""

    config: RuntimeConfig
    loader: OpenAPISpecLoader = field(default_factory=OpenAPISpecLoader)
    _proxy: Optional["FastMCPOpenAPI"] = None

    def get(self) -> "FastMCPOpenAPI":
        if self._proxy is None:
            self._proxy = create_proxy(self.config, loader=self.loader)
        return self._proxy


__all__ = ["create_proxy", "ProxyRegistry"]
