"""Server factory helpers for turning OpenAPI specs into MCP proxies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

FastMCPOpenAPI = None

try:  # pragma: no cover - imported lazily and mocked in tests
    from fastmcp.server.openapi import FastMCPOpenAPI  # type: ignore[assignment]
except ModuleNotFoundError:  # pragma: no cover - handled at runtime/tests
    try:  # Legacy fallback for fastmcp < 2.12
        from fastmcp.openapi import FastMCPOpenAPI  # type: ignore[assignment]
    except ModuleNotFoundError:
        FastMCPOpenAPI = None

from .client import create_http_client
from .config import RuntimeConfig
from .spec import OpenAPISpecLoader


def create_proxy(
    config: RuntimeConfig,
    *,
    loader: OpenAPISpecLoader | None = None,
) -> "FastMCPOpenAPI":
    if FastMCPOpenAPI is None:  # pragma: no cover - requires dependency
        raise RuntimeError(
            "FastMCPOpenAPI 不可用，请确认 fastmcp 已安装且版本满足 OpenAPI 支持。"
        )

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
