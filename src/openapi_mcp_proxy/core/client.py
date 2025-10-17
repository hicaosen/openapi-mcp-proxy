"""HTTP client factory used by the MCP proxy."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import httpx

from .auth import create_auth_strategy
from .config import RuntimeConfig


def derive_base_url(spec: Mapping[str, Any]) -> str | None:
    servers = spec.get("servers") if isinstance(spec, Mapping) else None
    if isinstance(servers, Sequence):
        for candidate in servers:
            if not isinstance(candidate, Mapping):
                continue
            url = candidate.get("url")
            if isinstance(url, str) and url.strip():
                return url.strip()
    return None


def create_http_client(
    config: RuntimeConfig,
    spec: Mapping[str, Any],
    *,
    transport_factory: type[httpx.AsyncHTTPTransport] | None = httpx.AsyncHTTPTransport,
) -> httpx.AsyncClient:
    strategy = create_auth_strategy(config.auth)

    headers = dict(config.headers)
    headers.update(strategy.headers())

    params = dict(strategy.query_params())
    cookies = dict(strategy.cookies())

    base_url = config.base_url or derive_base_url(spec)

    kwargs: dict[str, Any] = {
        "timeout": config.client.timeout,
        "verify": config.client.verify_ssl,
    }
    if base_url:
        kwargs["base_url"] = base_url
    if headers:
        kwargs["headers"] = headers
    if params:
        kwargs["params"] = params
    if cookies:
        kwargs["cookies"] = cookies

    auth = strategy.auth()
    if auth is not None:
        kwargs["auth"] = auth

    if config.client.proxies is not None:
        kwargs["proxies"] = config.client.proxies

    if config.client.retries and config.client.retries > 0 and transport_factory:
        kwargs["transport"] = transport_factory(retries=config.client.retries)

    return httpx.AsyncClient(**kwargs)


__all__ = ["create_http_client", "derive_base_url"]
