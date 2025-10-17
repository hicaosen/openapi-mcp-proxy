"""Authentication strategies for the proxy HTTP client."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping, Protocol

import httpx

from .config import AuthConfig


class AuthStrategy(Protocol):
    """Protocol describing runtime authentication customisation."""

    def headers(self) -> Mapping[str, str]:
        ...

    def auth(self) -> httpx.Auth | None:
        ...

    def query_params(self) -> Mapping[str, str]:
        ...

    def cookies(self) -> Mapping[str, str]:
        ...


@dataclass(slots=True)
class _BaseAuthStrategy(AuthStrategy):
    _headers: Dict[str, str] = field(default_factory=dict)
    _auth: httpx.Auth | None = None
    _query_params: Dict[str, str] = field(default_factory=dict)
    _cookies: Dict[str, str] = field(default_factory=dict)

    def headers(self) -> Mapping[str, str]:
        return self._headers

    def auth(self) -> httpx.Auth | None:
        return self._auth

    def query_params(self) -> Mapping[str, str]:
        return self._query_params

    def cookies(self) -> Mapping[str, str]:
        return self._cookies


def create_auth_strategy(config: AuthConfig) -> AuthStrategy:
    scheme = (config.scheme or "none").lower()
    strategy = _BaseAuthStrategy()

    if scheme == "none" or not scheme:
        pass
    elif scheme == "bearer":
        if not config.token:
            raise ValueError("Bearer authentication requires a token")
        strategy._headers["Authorization"] = f"Bearer {config.token}"
    elif scheme == "basic":
        if config.username is None or config.password is None:
            raise ValueError("Basic authentication requires username/password")
        strategy._auth = httpx.BasicAuth(config.username, config.password)
    elif scheme == "header":
        if config.header_name is None or config.header_value is None:
            raise ValueError("Header authentication requires name and value")
        strategy._headers[config.header_name] = config.header_value
    elif scheme == "api-key":
        if config.api_key_value is None:
            raise ValueError("API key authentication requires a key value")
        key_name = config.api_key_name or "X-API-Key"
        location = (config.api_key_location or "header").lower()
        if location == "header":
            strategy._headers[key_name] = config.api_key_value
        elif location == "query":
            strategy._query_params[key_name] = config.api_key_value
        elif location == "cookie":
            strategy._cookies[key_name] = config.api_key_value
        else:
            raise ValueError("Unsupported API key location; expected header/query/cookie")
    else:
        raise ValueError(f"Unsupported authentication scheme: {config.scheme}")

    strategy._headers.update(config.extra_headers)
    return strategy


__all__ = ["AuthStrategy", "create_auth_strategy"]
